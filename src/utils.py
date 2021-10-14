import os


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
