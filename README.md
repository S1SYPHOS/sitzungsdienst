# sitzungsdienst
[![Release](https://img.shields.io/github/release/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/releases) [![License](https://img.shields.io/github/license/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/blob/main/LICENSE) [![Issues](https://img.shields.io/github/issues/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/issues)

A simple Python utility for converting the weekly assignment PDF by the "Staatsanwaltschaft Freiburg" into `csv`, `json` as well as `ics` files.


## Getting started

Running `setup.bash` will install all dependencies inside a virtual environment, ready for action:

```bash
# Set up & activate virtualenv
virtualenv -p python3 venv

# shellcheck disable=SC1091
source venv/bin/activate

# Install dependencies
python -m pip install --editable .
```


## Usage

Using this library is straightforward:

```text
$ sta --help
Usage: sta [OPTIONS] SOURCE

  Extract weekly assignments from SOURCE file.

Options:
  -o, --output PATH         Output filename, without extension.
  -d, --directory TEXT      Output directory.
  -f, --file-format TEXT    File format, "csv", "json" or "ics".
  -q, --query TEXT          Query assignees, eg for name, department.
  -i, --inquiries FILENAME  JSON file with parameters for automation.
  -v, --verbose             Enable verbose mode.
  --version                 Show the version and exit.
  --help                    Show this message and exit.
```

The following code snippet provides a **very basic** batch processing example:

```bash
#!/bin/bash

# Create multiple calendar files at once
for arg; do
   sta -f ics -q "$arg" -o "$arg" source.pdf
done
```

Calling this script with something like `bash script.bash alice bob charlie` would give you `alice.ics`, `bob.ics` and `charlie.ics`, each containing their respective assignments.

However, you might want to store these information inside a `json` file and pass it via `--inquiries`:

```json
[
    {
        "output": "study-group",
        "query": [
            "123",
            "456",
            "789"
        ]
    },
    {
        "output": "alice",
        "query": [
            "123"
        ]
    },
    {
        "output": "bob",
        "query": [
            "456"
        ]
    },
    {
        "output": "all-events",
        "query": []
    }
]
```

The `output` property resembles the filename whereas `query` contains all search terms. Therefore, the first entry is equivalent to this command: `sta -o study-group -q 123 -q 456 -q 789 source.pdf`.


**Happy coding!**
