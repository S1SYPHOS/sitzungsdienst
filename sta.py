import os
import re
import json
import hashlib
import datetime
import operator

from io import BufferedReader

import click


def create_path(path: str) -> None:
    # Determine if (future) target is appropriate data file
    if os.path.splitext(path)[1].lower() in ['.csv', '.json', '.ics']:
        path = os.path.dirname(path)

    if not os.path.exists(path):
        try:
            os.makedirs(path)

        # Guard against race condition
        except OSError:
            pass


def reverse_date(string: str, separator: str='-') -> str:
    return separator.join(reversed(string.split('.')))


def reverse_person(string: str) -> str:
    return ' '.join(reversed([string.strip() for string in string.split(',')]))


def is_time(string: str) -> bool:
    if re.match(r'\d{2}:\d{2}', string):
        return True

    return False


def is_docket(string: str) -> bool:
    if re.match(r'\d{3}\sU?Js\s\d+/\d{2}', string):
        return True

    return False


def is_person(string: str) -> bool:
    if re.search(r'E?(?:O?StA|OAA)|Ref(?:\'in)?', string):
        return True

    return False


def hash(item: dict) -> str:
    return hashlib.md5(json.dumps(item).encode('utf-8')).hexdigest()


def process(pdf_file: BufferedReader) -> list:
    # Import library
    import PyPDF2

    # Create page data array
    pages = []

    # Fetch content from PDF file
    for page in PyPDF2.PdfFileReader(pdf_file).pages:
        pages.append([text.strip() for text in page.extractText().splitlines() if text])

    # Create source data array
    source = {}

    # Initialize weekday buffer
    date = None

    # Extract source
    for page in pages:
        # Reset mode
        is_live = False

        for index, entry in enumerate(page):
            # Determine starting point ..
            if entry == 'Anfahrt':
                is_live = True

                # .. and proceed with next entry
                continue

            # Determine terminal point ..
            if entry == 'Seite':
                is_live = False

                # .. and proceed with next entry
                continue

            # Enforce entries between starting & terminal point
            if not is_live or 'Ende der Auflistung' in entry:
                continue

            # Determine current date / weekday
            if entry in ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']:
                date = page[index + 1]

                if date not in source:
                    source[date] = []

                # Proceed with next entry
                continue

            # Proceed with next entry if it indicates ..
            # (1) .. current date
            if entry == date:
                continue

            # (2) .. follow-up appointment for main trial
            if entry in ['F', '+']:
                continue

            source[date].append(entry)

    # Create data array
    data = []

    # Convert source to usable data
    for date, text in source.items():
        # Iterate over text blocks
        for index, words in enumerate(text):
            # Determine index of each milestone
            if re.match(r'(?:AG|LG)\s', words):
                entry = []

                for i in range(1, 50):
                    try:
                        string = text[index + i]

                        # Stop upon reaching the court belonging to the next person
                        if re.match(r'(?:AG|LG)\s', string):
                            break

                        entry.append(string)

                    except IndexError:
                        break

                appointments = []

                # Set index of last entry
                last_index = 0

                for i, string in enumerate(entry):
                    # Upon first entry ..
                    if i == 0:
                        # .. reset index
                        last_index = 0

                    # Detect every ..
                    #
                    # (1) .. (Erste:r) Oberamtsanwalt / -anwältin
                    # - EOAA / EOAA'in
                    # - OAA / OAA'in
                    #
                    # (2) .. (Erste:r / Ober-) Staatsanwalt / -anwältin
                    # - OStA / OStA'in
                    # - EStA / EStA'in
                    # - StA / StA'in
                    #
                    # (3) .. Rechtsreferendar:in
                    # - Ref / Ref'in
                    if is_person(string):
                        # Determine current appointment
                        appointments.append((last_index, i + 1))

                        last_index = i + 1

                # Skip appointments without assignee
                if not appointments:
                    continue

                for appointment in appointments:
                    where = []
                    when  = ''
                    what  = ''
                    who   = []

                    start, end = appointment

                    for i in range(start, end):
                        if is_time(entry[i]):
                            # Apply findings
                            when = entry[i]

                        if is_docket(entry[i]):
                            # Apply findings
                            what = entry[i]

                        if is_person(entry[i]):
                            # If entry before this one is no docket ..
                            if not is_docket(entry[i - 1]):
                                # .. add it
                                who.append(entry[i - 1])

                            # Add current entry
                            who.append(entry[i])

                        if not when + what:
                            # Apply findings
                            where.append(entry[i])

                            # Proceed to next entry
                            continue

                    # Combine & store results
                    data.append({
                        'date': reverse_date(date),
                        'when': when,
                        'who': reverse_person(' '.join(who)),
                        'where': ' '.join([words.replace(' ,', '')] + where),
                        'what': what,
                    })

    return sorted(data, key=operator.itemgetter('date', 'who', 'when', 'where', 'what'))


def dump_csv(data: list, csv_file: str) -> None:
    # Import library
    import pandas

    # Write data to CSV file
    dataframe = pandas.DataFrame(data)
    dataframe.to_csv(csv_file, index=False)


def dump_json(data: list, json_file: str) -> None:
    # Write data to JSON file
    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def dump_ics(data: list, ics_file: str) -> None:
    # Import libraries
    import ics
    import pytz

    # Create calendar object
    calendar = ics.Calendar(creator='S1SYPHOS')

    # Iterate over items
    for item in data:
        # Build event object
        # (1) Define basic information
        uid = hash(item)
        name = 'Sitzungsdienst ({})'.format(item['what'])
        location = item['where']

        # (2) Define timezone, date & times
        time = datetime.datetime.strptime(item['date'] + item['when'], '%Y-%m-%d%H:%M')
        begin = time.replace(tzinfo=pytz.timezone('Europe/Berlin'))
        end = begin + datetime.timedelta(hours=1)

        # (3) Create event
        event = ics.Event(name=name, begin=begin, end=end, uid=uid, location=location)

        # Add event to calendar
        calendar.events.add(event)

    # Write calendar object to ICS file
    with open(ics_file, 'w') as file:
        file.writelines(calendar)


@click.command()
@click.argument('input-file', type=click.File('rb'))
@click.option('-o', '--output-file', default='data', type=click.Path(), help='Output filename, without extension.')
@click.option('-d', '--directory', default='dist', help='Output directory.')
@click.option('-f', '--file-format', default='csv', help='File format, "csv", "json" or "ics".')
@click.option('-q', '--query', multiple=True, help='Query assignees, eg for name, department.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose mode.')
@click.version_option('1.2.0')
def cli(input_file: BufferedReader, output_file: str, directory: str, file_format: str, query: str, verbose: bool) -> None:
    """Extract weekly assignments from INPUT_FILE."""

    # If file format is invalid ..
    if file_format.lower() not in ['csv', 'json', 'ics']:
        # (1) .. report falling back
        click.echo('Invalid file format "{}", falling back to "csv".'.format(file_format))

        # (2) .. actually fall back
        file_format = 'csv'

    # Process data
    data = process(input_file)

    # If query is present, filter data
    if query:
        # Make report on query human-readable
        # (1) Build list of verbose search terms
        query_report = ['{}) {}'.format(index + 1, term) for index, term in enumerate(query)]

        # (2) Simplify report for single term
        if len(query_report) == 1:
            query_report = ['"{}"'.format(query[0])]

        # (3) Report filtering
        click.echo('Querying data for {} ..'.format(' '.join(query_report)), nl=False)

        # Create data buffer
        buffer = []

        # Loop over search terms in order to ..
        for term in query:
            # .. filter out relevant items
            buffer += [item for item in data if term.lower() in item['who'].lower()]

        # Apply data buffer
        data = buffer

        # Report back
        click.echo(' done.')

    # Build output path
    output_file = os.path.join(directory, '{}.{}'.format(output_file.lower(), file_format))

    # Create output path (if necessary)
    create_path(output_file)

    # Report saving the file
    click.echo('Saving file as "{}" ..'.format(output_file), nl=False)

    # Write data as ..
    if file_format == 'csv':
        # (1) .. CSV
        dump_csv(data, output_file)

    if file_format == 'json':
        # (2) .. JSON
        dump_json(data, output_file)

    if file_format == 'ics':
        # (3) .. ICS
        dump_ics(data, output_file)

    # Report back
    click.echo(' done.')

    # If verbose mode is activated ..
    if verbose:
        # Add newline
        click.echo()

        # .. print results, consisting of ..
        # (1) .. date range
        click.echo('Zeitraum: {} - {}'.format(data[0]['date'], data[-1]['date']))

        # Add newline before first entry
        click.echo()

        # (2) .. data entries, namely ..
        for index, item in enumerate(data):
            # (a) .. entry number
            click.echo('Eintrag {}:'.format(index + 1))

            # (b) .. its key-value pairs
            for key, value in item.items():
                click.echo('{}: {}'.format(key, value))

            # Add newline before each subsequent entry
            click.echo()


if __name__ == '__main__':
    cli()
