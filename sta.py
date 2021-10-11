import os
import re
import json
import operator

from datetime import datetime, timedelta
from hashlib import md5

import click
import pandas
import pytz

from ics import Calendar, Event
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError


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
    return md5(json.dumps(item).encode('utf-8')).hexdigest()


def process(pdf_file: str) -> list:
    # Create page data array
    pages = []

    # Fetch content from PDF file
    with open(pdf_file, 'rb') as file:
        for page in PdfFileReader(file).pages:
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


@click.command()
@click.version_option('1.0.0')
@click.option('-i', '--input-file', type=click.Path(True), help='Path to PDF input file.')
@click.option('-o', '--output-file', default='csv', type=click.Path(), help='Output filename, without extension.')
@click.option('-f', '--file-format', default='csv', help='File format, "csv", "json" or "ics".')
@click.option('-q', '--query', help='Filter people, eg by name or department.')
def cli(input_file, output_file, file_format, user, department):
    # If no input file provided ..
    if not input_file:
        # (1) .. report reason
        click.echo('Please provide input file!')

        # (2) .. abort execution
        click.Context.exit(0)

    # Build filename of output file
    output_file = '{}.{}'.format(output_file, file_format)

    # Create output path
    create_path(output_file)

    # Process data
    data = process(input_file)

    # If present, filter data by ..
    if user:
        # (1) .. user
        click.echo('Applied filter for user "{}"'.format(user))
        data = [item for item in data if user in item['who']]

    if department:
        # (1) .. department
        click.echo('Applied filter for department "{}"'.format(department))
        data = [item for item in data if department in item['who']]

    # Write data as ..
    if file_format == 'json':
        # (1) .. JSON
        with open(output_file, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    if file_format == 'csv':
        # (2) .. CSV
        df = pandas.DataFrame(data)
        df.to_csv(output_file, index=False)

    if file_format == 'ics':
        # (3) .. ICS
        calendar = Calendar(creator='S1SYPHOS')

        # Iterate over items
        for item in data:
            # Build event
            # (1) Define basic information
            uid = hash(item)
            name = 'Sitzungsdienst ({})'.format(item['what'])
            location = item['where']

            # (2) Define timezone, date & times
            time = datetime.strptime(item['date'] + item['when'], '%Y-%m-%d%H:%M')
            begin = time.replace(tzinfo=pytz.timezone('Europe/Berlin'))
            end = begin + timedelta(hours=1)

            # (3) Create event
            event = Event(name=name, begin=begin, end=end, uid=uid, location=location)

            # Add event to calendar
            calendar.events.add(event)

        # Write calendar to file
        with open(output_file, 'w') as file:
            file.writelines(calendar)

    # Report back
    click.echo('Saved file as "{}"'.format(output_file))


if __name__ == '__main__':
    cli()
