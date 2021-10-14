# sitzungsdienst
[![Release](https://img.shields.io/github/release/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/releases) [![License](https://img.shields.io/github/license/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/blob/main/LICENSE) [![Issues](https://img.shields.io/github/issues/S1SYPHOS/sitzungsdienst.svg)](https://github.com/S1SYPHOS/sitzungsdienst/issues)

A simple Python utility for converting the weekly assignment PDF by the "Staatsanwaltschaft Freiburg" into `csv`, `json` as well as `ics` files.


## Getting started

Running `setup.sh` will install all dependencies inside a virtual environment, ready for action:

```shell
# Set up & activate virtualenv
virtualenv -p python3 venv && source venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
```


## Usage

Using this library is straightforward:

```text
$ python main.py --help

Usage: main.py [OPTIONS] INPUT

  Extract weekly assignments from INPUT file.

Options:
  -o, --output-file PATH    Output filename, without extension.
  -d, --directory PATH      Output directory.
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
   python sta.py -i kw42.pdf -f ics -q "$arg" -o "$arg"
done
```

Calling this script with something like `bash script.bash alice bob charlie` would give you `alice.ics`, `bob.ics` and `charlie.ics`, each containing their respective assignments.

**Happy coding!**
