from os import makedirs
from os.path import dirname ,exists ,splitext
from json import load

from io import BufferedReader


def create_path(path: str) -> None:
    # Determine if (future) target is appropriate data file
    if splitext(path)[1].lower() in ['.csv', '.json', '.ics']:
        path = dirname(path)

    if not exists(path):
        try:
            makedirs(path)

        # Guard against race condition
        except OSError:
            pass


def load_json(json_file: BufferedReader):
    # Attempt to ..
    try:
        # .. load JSON file object
        return load(json_file)

    # .. otherwise
    except json.decoder.JSONDecodeError:
        # .. throw exception
        raise Exception
