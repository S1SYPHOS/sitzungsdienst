from io import BufferedReader


def dedupe(duped_data, encoding: str = 'utf-8'):
    """
    Removes duplicates from a given data structure
    """

    # Import libraries
    from hashlib import md5

    codes = set()
    deduped_data = []

    for item in duped_data:
        hash_digest = md5(str(item).encode(encoding)).hexdigest()

        if hash_digest not in codes:
            codes.add(hash_digest)
            deduped_data.append(item)

    return deduped_data


def load_json(json_file: BufferedReader):
    """
    Loads contents of given JSON file
    """

    # Import library
    from json import load
    from json.decoder import JSONDecodeError

    # Attempt to ..
    try:
        # .. load JSON file object
        return load(json_file)

    # .. otherwise
    except JSONDecodeError:
        # .. throw exception
        raise Exception


def dump_csv(data: list, csv_file: str) -> None:
    """
    Stores data as given CSV file
    """

    # Import library
    from pandas import DataFrame

    # Write data to CSV file
    dataframe = DataFrame(data)
    dataframe.to_csv(csv_file, index = False)


def dump_json(data: list, json_file: str, indent: int = 4) -> None:
    """
    Stores data as given JSON file
    """

    # Import libraries
    from json import dump

    # Write data to JSON file
    with open(json_file, 'w') as file:
        dump(data, file, ensure_ascii = False, indent = indent)


def data2calendar(data: list, duration: int = 1):
    """
    Converts data to iCalendar text
    """

    # Import libraries
    from os.path import exists
    from json import dumps
    from hashlib import md5
    from datetime import datetime, timedelta

    # Add fallback for Python < v3.9
    try:
        import zoneinfo

    except ImportError:
        from backports import zoneinfo

    from ics import Calendar, Event, Attendee

    # Define database file
    db_file = 'database.json'

    # Create database array
    database = {}

    # If database file exists ..
    if exists(db_file):
        # open it and ..
        with open(db_file, 'r') as file:
            # .. load its contents
            database = load_json(file)

    # Create calendar object
    calendar = Calendar(creator = 'S1SYPHOS')

    # Determine timezone
    timezone = zoneinfo.ZoneInfo('Europe/Berlin')

    # Iterate over items
    for item in data:
        # Define timezone, date & times
        time = datetime.strptime(item['date'] + item['when'], '%Y-%m-%d%H:%M')
        begin = time.replace(tzinfo = timezone)
        end = begin + timedelta(hours = duration)

        # Create event object
        event = Event(
            uid = md5(dumps(item).encode('utf-8')).hexdigest(),
            name = 'Sitzungsdienst ({})'.format(item['what']),
            created = datetime.now(timezone),
            begin = begin,
            end = end,
            location = item['where']
        )

        # Add assignee(s) as attendee(s)
        for person in item['who'].split(';'):
            # Check database for matching emails
            emails = [email for query, email in database.items() if query in person]

            # Default to empty email, but use first match (if available)
            email = '' if not emails else emails[0]

            # Build attendee object from email
            attendee = Attendee(email)

            # Add name (= title, full name & department as string)
            attendee.common_name = person

            # Add attendee to event object
            event.add_attendee(attendee)

        # Add event to calendar
        calendar.events.add(event)

    return calendar


def dump_ics(data: list, ics_file: str) -> None:
    """
    Stores data as given ICS file
    """

    # Write calendar object to ICS file
    with open(ics_file, 'w') as file:
        file.writelines(data2calendar(data))
