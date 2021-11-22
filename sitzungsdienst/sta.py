from io import BufferedReader
from re import match, search
from operator import itemgetter


class Sitzungsdienst:
    '''
    This class represents the weekly assignments of a single
    PDF file as published by the Staatsanwaltschaft Freiburg
    '''

    def __init__(self, input_file: BufferedReader) -> None:
        '''
        Parses & processes the given file object,
        storing the result as the `data` property
        '''

        self.data = self.extract_data(input_file)


    def process_pages(self, pages: list) -> dict:
        '''
        Processes PDF content per-page,
        returning its contents per-date
        '''

        # Create data array
        data = {}

        # Initialize weekday buffer
        date = None

        # Extract data
        for page in pages:
            # Reset mode
            is_live = False

            for index, text in enumerate(page):
                # Determine starting point ..
                if text == 'Anfahrt':
                    is_live = True

                    # .. and proceed with next entry
                    continue

                # Determine terminal point ..
                if text == 'Seite':
                    is_live = False

                    # .. and proceed with next entry
                    continue

                # Enforce entries between starting & terminal point
                if not is_live or 'Ende der Auflistung' in text:
                    continue

                # Determine current date / weekday
                if text in ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']:
                    date = page[index + 1]

                    if date not in data:
                        data[date] = []

                    # Proceed with next entry
                    continue

                # Proceed with next entry if it indicates ..
                # (1) .. current date
                if text == date:
                    continue

                # (2) .. follow-up appointment for main trial
                if text in ['F', '+']:
                    continue

                data[date].append(text)

        return data


    def process_data(self, source: dict) -> list:
        '''
        Processes preprocessed per-date data,
        returning data records for each court
        '''

        # Create data array
        unprocessed = []

        # Iterate over source data
        for date, raw in source.items():
            buffer = []
            court  = ''

            # Iterate over text blocks
            for index, text in enumerate(raw):
                if self.is_court(text):
                    court = text

                else:
                    buffer.append(text)

                if index == len(raw) - 1 or self.is_court(raw[index + 1]):
                    unprocessed.append({
                        'date': date,
                        'court': court,
                        'data': buffer,
                    })

                    # Reset buffer
                    buffer = []

        # Create data array
        processed = []

        for item in unprocessed:
            events = []

            # Set index of last entry
            last_index = 0

            for index, text in enumerate(item['data']):
                # Upon first entry ..
                if index == 0:
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
                if self.is_person(text):
                    # Determine current appointment
                    events.append((last_index, index + 1))

                    # Adjust position of last index
                    last_index = index + 1

            # Skip events without assignee
            if not events:
                continue

            processed.append({
                'date': item['date'],
                'court': item['court'],
                'events': events,
                'infos': item['data'],
            })

        return processed


    def is_court(self, string: str) -> bool:
        '''Checks whether string denotes a court'''

        if match(r'(?:AG|LG)\s', string):
            return True

        return False


    def is_person(self, string: str) -> bool:
        '''Checks whether string indicates a person'''

        if search(r'(?:E?(?:O?StA|OAA)|Ref)(?:\'in)?', string):
            return True

        return False


    def is_time(self, string: str) -> bool:
        '''Checks whether string matches a time'''

        if match(r'\d{2}:\d{2}', string):
            return True

        return False


    def is_docket(self, string: str) -> bool:
        '''Checks whether string matches a docket number'''

        if match(r'\d{2,3}\sU?Js\s\d+/\d{2}', string):
            return True

        return False


    def reverse_date(self, string: str, separator: str='-') -> str:
        '''Reverts a given date using `separator` as separator'''

        return separator.join(reversed(string.split('.')))


    def format_person(self, data: list) -> str:
        '''Converts a list of people to a human-readable string'''

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
        '''
        Extracts data from PDF file, utilizing all of the
        above functions & returning the processed results
        '''

        # Import library
        import PyPDF2

        # Create page data array
        pages = []

        # Fetch content from PDF file
        for page in PyPDF2.PdfFileReader(pdf_file).pages:
            pages.append([text.strip() for text in page.extractText().splitlines() if text])

        # Create data array
        data = []

        # Iterate over processed source data
        for item in self.process_data(self.process_pages(pages)):
            # Create data buffer
            details = []

            # Create buffer for place & assignee(s)
            where = []
            who   = []

            # Iterate over indices of each event
            for event in item['events']:
                # Create buffer for time & docket number
                when  = ''
                what  = ''

                for index in range(event[0], event[1]):
                    entry = item['infos']

                    # Parse strings, which are either ..
                    # (1) .. time
                    if self.is_time(entry[index]):
                        # Apply findings
                        when = entry[index]

                    # (2) .. docket number
                    elif self.is_docket(entry[index]):
                        # Apply findings
                        what = entry[index]

                    # (3) .. person
                    elif self.is_person(entry[index]):
                        # If entry before this one is no docket ..
                        if not self.is_docket(entry[index - 1]):
                            # .. add it
                            who.append(entry[index - 1])

                        # Add current entry
                        who.append(entry[index])

                    # (4) .. something else
                    else:
                        # If next entry is not a person ..
                        if not self.is_person(entry[index + 1]):
                            # .. treat current entry as
                            where.append(entry[index])

                # If time & docket number are specified ..
                if when + what:
                    # (1) .. add them to the buffer
                    details.append((when, what, who))

                    # (2) .. reset assignee(s)
                    who = []

                # .. otherwise instead of creating an empty entry ..
                else:
                    # .. add assignee to last entry
                    details[-1] = list(details[-1])[:-1] + [who]

            # Iterate over result in order to ..
            for detail in details:
                # .. combine & store them
                data.append({
                    'date': self.reverse_date(item['date']),
                    'when': detail[0],
                    'who': self.format_person(detail[2]),
                    'where': ' '.join([item['court'].replace(' ,', '')] + where),
                    'what': detail[1],
                })

        return sorted(data, key=itemgetter('date', 'who', 'when', 'where', 'what'))


    def filter(self, query: list) -> list:
        '''
        Filters the currently stored data by each
        `query`term, returning the search results
        '''

        # Create data buffer
        buffer = []

        # Loop over search terms in order to ..
        for term in query:
            # .. filter out relevant items
            buffer += [item for item in self.data if term.lower() in item['who'].lower()]

        # Apply data buffer
        return buffer


    def date_range(self) -> tuple:
        '''Determines date range for the currently stored data'''

        return (self.data[0]['date'], self.data[-1]['date'])
