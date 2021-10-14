from io import BufferedReader
from json import dump, dumps
from hashlib import md5
from datetime import datetime, timedelta


def create_path(path: str) -> None:
    # Import library
    import os

    # Determine if (future) target is appropriate data file
    if os.path.splitext(path)[1].lower() in ['.csv', '.json', '.ics']:
        path = os.path.dirname(path)

    if not os.path.exists(path):
        try:
            os.makedirs(path)

        # Guard against race condition
        except OSError:
            pass


def load_json(json_file: BufferedReader):
    # Import library
    import json

    # Attempt to ..
    try:
        # .. load JSON file object
        return json.load(json_file)

    # .. otherwise
    except json.decoder.JSONDecodeError:
        # .. throw exception
        raise Exception


def dump_csv(data: list, csv_file: str) -> None:
    # Import library
    import pandas

    # Write data to CSV file
    dataframe = pandas.DataFrame(data)
    dataframe.to_csv(csv_file, index=False)


def dump_json(data: list, json_file: str) -> None:
    # Write data to JSON file
    with open(json_file, 'w') as file:
        dump(data, file, ensure_ascii=False, indent=4)


def dump_ics(data: list, ics_file: str) -> None:
    # Import libraries
    import os
    import ics
    import pytz

    # Define database file
    db_file = 'database.json'

    # Create database array
    database = {}

    # If database file exists ..
    if os.path.exists(db_file):
        # open it and ..
        with open(db_file, 'r') as file:
            # .. load its contents
            database = load_json(file)

    # Create calendar object
    calendar = ics.Calendar(creator='S1SYPHOS')

    # Iterate over items
    for item in data:
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
        for person in item['who'].split(';'):
            emails = [email for query, email in database.items() if query in person]

            if emails:
                attendee = ics.Attendee(emails[0])
                attendee.common_name = person

                event.add_attendee(attendee)

        # Add event to calendar
        calendar.events.add(event)

    # Write calendar object to ICS file
    with open(ics_file, 'w') as file:
        file.writelines(calendar)
