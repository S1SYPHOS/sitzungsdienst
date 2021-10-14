from io import BufferedReader
from os.path import join

import click

from src.sta import Sitzungsdienst
from src.utils import create_path


@click.command()
@click.argument('input-file', type=click.File('rb'))
@click.option('-o', '--output-file', default='data', type=click.Path(), help='Output filename, without extension.')
@click.option('-d', '--directory', default='dist', help='Output directory.')
@click.option('-f', '--file-format', default='csv', help='File format, "csv", "json" or "ics".')
@click.option('-q', '--query', multiple=True, help='Query assignees, eg for name, department.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose mode.')
@click.version_option('1.2.0')
def cli(input_file: BufferedReader, output_file: str, directory: str, file_format: str, query: str, verbose: bool) -> None:
    """Extract weekly assignments from INPUT_FILE."""

    # If file format is invalid ..
    if file_format.lower() not in ['csv', 'json', 'ics']:
        # (1) .. report falling back
        click.echo('Invalid file format "{}", falling back to "csv".'.format(file_format))

        # (2) .. actually fall back
        file_format = 'csv'

    # Process data
    sta = Sitzungsdienst(input_file)

    # If query is present, filter data
    if query:
        # Make report on query human-readable
        # (1) Build list of verbose search terms
        query_report = ['{}) {}'.format(index + 1, term) for index, term in enumerate(query)]

        # (2) Simplify report for single term
        if len(query_report) == 1:
            query_report = ['"{}"'.format(query[0])]

        # (3) Report filtering
        click.echo('Querying data for {} ..'.format(' '.join(query_report)), nl=False)

        # Filter data
        sta.filter(query)

        # Report back
        click.echo(' done.')

    # If results are empty ..
    if not sta.data:
        # (1) .. report back
        click.echo('No results found!')

        # (2) .. abort further execution
        click.Context.abort('')

    # Build output path
    output_file = join(directory, '{}.{}'.format(output_file.lower(), file_format))

    # Create output path (if necessary)
    create_path(output_file)

    # Report saving the file
    click.echo('Saving file as "{}" ..'.format(output_file), nl=False)

    # Write data as ..
    if file_format == 'csv':
        # (1) .. CSV
        sta.dump_csv(output_file)

    if file_format == 'json':
        # (2) .. JSON
        sta.dump_json(output_file)

    if file_format == 'ics':
        # (3) .. ICS
        sta.dump_ics(output_file)

    # Report back
    click.echo(' done.')

    # If verbose mode is activated ..
    if verbose:
        # Get data
        data = sta.data

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


if __name__ == '__main__':
    cli()
