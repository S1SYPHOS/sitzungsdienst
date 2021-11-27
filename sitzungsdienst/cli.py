from io import BufferedReader
from pathlib import Path

import click

from .sta import Sitzungsdienst
from .utils import dedupe, dump_csv, dump_ics, dump_json, load_json


@click.command()
@click.argument('source', type=click.File('rb'))
@click.option('-o', '--output', default='data', type=click.Path(), help='Output filename, without extension.')
@click.option('-d', '--directory', default='dist', help='Output directory.')
@click.option('-f', '--file-format', default='csv', help='File format, "csv", "json" or "ics".')
@click.option('-q', '--query', multiple=True, help='Query assignees, eg for name, department.')
@click.option('-i', '--inquiries', type=click.File('rb'), help='JSON file with parameters for automation.')
@click.option('-c', '--clear-cache', is_flag=True, help='Remove existing files in directory first.')
@click.option('-v', '--verbose', count=True, help='Enable verbose mode.')
@click.version_option('1.4.6')
def cli(source: BufferedReader, output: str, directory: str, file_format: str, query: str, inquiries: BufferedReader, clear_cache: bool, verbose: int) -> None:
    """Extract weekly assignments from SOURCE file."""

    # If file format is invalid ..
    if file_format.lower() not in ['csv', 'json', 'ics']:
        # (1) .. report falling back
        if verbose > 0: click.echo('Invalid file format "{}", falling back to "csv".'.format(file_format))

        # (2) .. actually fall back
        file_format = 'csv'

    # Process data
    sta = Sitzungsdienst(source)

    # If results are empty ..
    if not sta.data:
        # (1) .. report back
        if verbose > 0: click.echo('No results found!')

        # (2) .. abort further execution
        click.Context.abort('')

    # Build default request
    requests = [{
        'output': output,
        'query': query,
    }]

    # If inquiries exist ..
    if inquiries:
        # .. load its content
        requests = load_json(inquiries)

    # Create output path (if necessary)
    Path(directory).mkdir(parents=True, exist_ok=True)

    # If enabled ..
    if clear_cache:
        # .. loop over CSV, JSON & ICS files ..
        for path in [file.resolve() for file in Path(directory).glob('**/*') if file.suffix in ['.csv', '.json', '.ics']]:
            # .. deleting each on of them
            path.unlink()

    # Iterate over requests
    for request in requests:
        # Get data
        data = sta.data

        # If query is present, filter data
        if request['query']:
            # If verbose mode is enabled ..
            if verbose > 0:
                # .. display query terms in human-readable fashion
                # (1) Build list of verbose search terms
                query_report = ['{}) {}'.format(index + 1, term) for index, term in enumerate(request['query'])]

                # (2) Simplify report for single term
                if len(query_report) == 1:
                    query_report = ['"{}"'.format(request['query'][0])]

                # (3) Report filtering
                click.echo('Querying data for {} ..'.format(' '.join(query_report)), nl=False)

            # Filter data
            data = sta.filter(request['query'])

            # If results are empty ..
            if not data:
                # (1) .. report failure
                if verbose > 0: click.echo(' failed!')

                # (2) .. proceed with next request
                continue

            # Report back
            if verbose > 0: click.echo(' done.')

        # Build output path
        output_file = Path(directory, '{}.{}'.format(request['output'].lower(), file_format))

        # Report saving the file
        if verbose > 0: click.echo('Saving file as "{}" ..'.format(output_file), nl=False)

        # Remove duplicate entries
        data = dedupe(data)

        # Write data as ..
        if file_format == 'csv':
            # (1) .. CSV
            dump_csv(data, output_file)

        if file_format == 'json':
            # (2) .. JSON
            dump_json(data, output_file)

        if file_format == 'ics':
            # (3) .. ICS
            dump_ics(data, output_file)

        # Report back
        if verbose > 0: click.echo(' done.')

        # If verbose mode is activated ..
        if verbose > 1:
            # Add newline & delimiter
            click.echo()
            click.echo('----')

            # .. print results, consisting of ..
            # (1) .. date range
            start, end = sta.date_range()
            click.echo('Zeitraum: {} - {}'.format(start, end))

            # Add delimiter before first entry
            click.echo('----')

            # (2) .. data entries, namely ..
            for index, item in enumerate(data):
                # (a) .. entry number
                click.echo('Eintrag {}:'.format(index + 1))

                # (b) .. its key-value pairs
                for key, value in item.items():
                    click.echo('{}: {}'.format(key, value))

                # Add delimiter before each subsequent entry
                click.echo('--')
