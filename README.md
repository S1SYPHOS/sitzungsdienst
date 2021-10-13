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
$ python sta.py --help

Usage: sta.py [OPTIONS] INPUT_FILE

  Extract weekly assignments from INPUT_FILE.

Options:
  -o, --output-file PATH  Output filename, without extension.
  -d, --directory PATH    Output directory.
  -f, --file-format TEXT  File format, "csv", "json" or "ics".
  -q, --query TEXT        Query assignees, eg for name, department.
  -v, --verbose           Enable verbose mode.
  --version               Show the version and exit.
  --help                  Show this message and exit.
```


**Happy coding!**
