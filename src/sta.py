from io import BufferedReader
from re import match, search
from json import dump, dumps
from hashlib import md5
from datetime import datetime, timedelta
from operator import itemgetter


class Sitzungsdienst:
    def __init__(self, input_file: BufferedReader) -> None:
        self.data = self.extract_data(input_file)


    def is_court(self, string: str) -> bool:
        if match(r'(?:AG|LG)\s', string):
            return True

        return False


    def is_person(self, string: str) -> bool:
        if search(r'(?:E?(?:O?StA|OAA)|Ref)(?:\'in)?', string):
            return True

        return False


    def is_time(self, string: str) -> bool:
        if match(r'\d{2}:\d{2}', string):
            return True

        return False


    def is_docket(self, string: str) -> bool:
        if match(r'\d{3}\sU?Js\s\d+/\d{2}', string):
            return True

        return False


    def reverse_date(self, string: str, separator: str='-') -> str:
        return separator.join(reversed(string.split('.')))


    def format_person(self, data: list) -> str:
        # Form complete string
        string = ' '.join(data)

        people = []

        # Create people buffer
        buffer = []

        for text in string.split(','):
            # Remove whitespaces
            text = text.strip()

            # Look for title
            title = search(r'\b((?:E?(?:O?StA|OAA)|Ref)(?:\'in)?)\b', text)

            # Check whether text block contains title which
            # indicates last text block for current person
            if title:
                # Iterate over buffer items
                for index, item in enumerate(buffer):
                    # If person has PhD ..
                    if 'Dr.' in item:
                        # (1) .. remove it from current string
                        buffer[index] = item.replace('Dr.', '')

                        # (2) .. add PhD to buffer at proper position
                        buffer.append('Dr.')

                        # Abort iteration
                        break

                # Add title to buffer
                buffer.append(title[1])

                # Build proper name from it
                people.append(' '.join(reversed([item.strip() for item in buffer if item])))

                # Reset buffer, but keep the rest of the string
                buffer = [text.replace(title[1], '')]

            # .. otherwise ..
            else:
                buffer.append(text)

        return '; '.join(people)


    def extract_data(self, pdf_file: BufferedReader) -> list:
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
                if self.is_court(words):
                    entry = []

                    for i in range(1, 50):
                        try:
                            string = text[index + i]

                            # Stop upon reaching the court belonging to the next person
                            if self.is_court(string):
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
                        if self.is_person(string):
                            # Determine current appointment
                            appointments.append((last_index, i + 1))

                            last_index = i + 1

                    # Skip appointments without assignee
                    if not appointments:
                        continue

                    # Create data buffer
                    buffer = []

                    # Create location array
                    where = []

                    for appointment in appointments:
                        when  = ''
                        what  = ''
                        who   = []

                        start, end = appointment

                        for i in range(start, end):
                            # Parse strings, which are either ..
                            # (1) .. time
                            if self.is_time(entry[i]):
                                # Apply findings
                                when = entry[i]

                            # (2) .. docket number
                            elif self.is_docket(entry[i]):
                                # Apply findings
                                what = entry[i]

                            # (3) .. person
                            elif self.is_person(entry[i]):
                                # If entry before this one is no docket ..
                                if not self.is_docket(entry[i - 1]):
                                    # .. add it
                                    who.append(entry[i - 1])

                                # Add current entry
                                who.append(entry[i])

                            # (4) .. something else
                            else:
                                # If next entry is not a person ..
                                if not self.is_person(entry[i + 1]):
                                    # .. treat current entry as
                                    where.append(entry[i])

                        # Combine & store results
                        buffer.append({
                            'date': self.reverse_date(date),
                            'when': when,
                            'who': self.format_person(who),
                            'where': '',
                            'what': what,
                        })

                        # On last appointment ..
                        if appointment == appointments[-1]:
                            # .. iterate over buffer items and ..
                            for item in buffer:
                                # (1) .. apply location
                                item['where'] = ' '.join([words.replace(' ,', '')] + where)

                                # (2) .. add it to data array
                                data.append(item)

                            # Reset buffer & location
                            buffer = []
                            where = []

        # Monkeypatch issue where two assignees result in two entries where ..
        for index, item in enumerate(data):
            # .. one contains empty fields for time & docket number
            # .. one contains incorrect assignees
            if not item['when'] and not item['what']:
                # (1) Transfer mising information
                data[index - 1]['who'] = item['who']

                # (2) Remove incomplete entry
                del data[index]

        return sorted(data, key=itemgetter('date', 'who', 'when', 'where', 'what'))


    def filter(self, query: list) -> None:
        # Create data buffer
        buffer = []

        # Loop over search terms in order to ..
        for term in query:
            # .. filter out relevant items
            buffer += [item for item in self.data if term.lower() in item['who'].lower()]

        # Apply data buffer
        self.data = buffer


    def dump_csv(self, csv_file: str) -> None:
        # Import library
        import pandas

        # Write data to CSV file
        dataframe = pandas.DataFrame(self.data)
        dataframe.to_csv(csv_file, index=False)


    def dump_json(self, json_file: str) -> None:
        # Write data to JSON file
        with open(json_file, 'w') as file:
            dump(self.data, file, ensure_ascii=False, indent=4)


    def dump_ics(self, ics_file: str) -> None:
        # Import libraries
        import ics
        import pytz

        # Create calendar object
        calendar = ics.Calendar(creator='S1SYPHOS')

        # Iterate over items
        for item in self.data:
            # Build event object
            # (1) Define basic information
            uid = md5(dumps(item).encode('utf-8')).hexdigest()
            name = 'Sitzungsdienst ({})'.format(item['what'])
            location = item['where']

            # (2) Define timezone, date & times
            time = datetime.strptime(item['date'] + item['when'], '%Y-%m-%d%H:%M')
            begin = time.replace(tzinfo=pytz.timezone('Europe/Berlin'))
            end = begin + timedelta(hours=1)

            # (3) Create event
            event = ics.Event(name=name, begin=begin, end=end, uid=uid, location=location)

            # (4) Add person as attendee
            event.add_attendee(item['who'])

            # Add event to calendar
            calendar.events.add(event)

        # Write calendar object to ICS file
        with open(ics_file, 'w') as file:
            file.writelines(calendar)


    def date_range(self) -> tuple:
        return (self.data[0]['date'], self.data[-1]['date'])
