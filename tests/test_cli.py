import os
import glob
import json

from click.testing import CliRunner
from sitzungsdienst.cli import cli


def test_cli_no_argument():
    runner = CliRunner()

    # Run function
    result = runner.invoke(cli)

    # Assert result
    assert result.exception


def test_cli(tmp_path):
    runner = CliRunner()

    # Loop over PDF source files
    for pdf_file in glob.glob('archive/*.pdf'):
        # Define subdirectory
        pdf_slug = os.path.basename(pdf_file).replace('.pdf', '')

        # Create directory
        path = tmp_path / pdf_slug
        path.mkdir(parents=True)

        # Test 1 :: File Format
        for ext in ['csv', 'ics', 'json']:
            # Define slug
            slug = 'file_format'

            # Build filename
            file_name = '{}.{}'.format(slug, ext)

            # Define filepath
            file = path / file_name

            # Define CLI arguments
            args = [
                '-f', '{}'.format(ext),
                '-o', '{}'.format(slug),
                '-d', '{}'.format(str(path.resolve())),
                pdf_file,
            ]

            # Run function
            result = runner.invoke(cli, args)

            # Assert existence
            assert file.exists()

            # TODO: Creation timestamp differs on every run
            if ext == 'ics':
                continue

            # Compare data
            with open(str(file.resolve()), 'r') as data_file:
                created = data_file.readlines()

            with open('tests/fixtures/{}/{}'.format(pdf_slug, file_name), 'r') as data_file:
                expected = data_file.readlines()

            assert created == expected

        # Test 2 :: Query
        for ext in ['csv', 'ics', 'json']:
            # Skip PDFs without matching assignment
            if pdf_slug in [
                'kw35',
                'kw36',
                'kw37',
                'loerrach',
            ]:
                continue

            # Define slug
            slug = 'query'

            # Build filename
            file_name = '{}.{}'.format(slug, ext)

            # Define filepath
            file = path / file_name

            # Define CLI arguments
            args = [
                '-q', '210',
                '-f', '{}'.format(ext),
                '-o', '{}'.format(slug),
                '-d', '{}'.format(str(path.resolve())),
                pdf_file,
            ]

            # Run function
            result = runner.invoke(cli, args)

            # Assert existence
            assert file.exists()

            # TODO: Creation timestamp differs on every run
            if ext == 'ics':
                continue

            # Compare data
            with open(str(file.resolve()), 'r') as data_file:
                created = data_file.readlines()

            with open('tests/fixtures/{}/{}'.format(pdf_slug, file_name), 'r') as data_file:
                expected = data_file.readlines()

            assert created == expected

        # Test 3 :: Inquiries

        # Create file with test data
        inquiries_file = path / 'inquiries.json'

        inquiries = [
            {
                'output': 'me',
                'query': ['210'],
            },
            {
                'output': 'random',
                'query': [
                    '210',
                    '520',
                    '850'
                ],
            },
            {
                'output': 'all',
                'query': [],
            },
        ]

        inquiries_file.write_text(json.dumps(inquiries))

        inquiries_slugs = [item['output'] for item in inquiries]

        for ext in ['csv', 'ics', 'json']:
            # Skip PDFs without matching assignment
            if pdf_slug in [
                'kw35',
                'kw36',
                'kw37',
                'loerrach',
            ]:
                continue

            # Define CLI arguments
            args = [
                '-i', '{}'.format(inquiries_file.resolve()),
                '-f', '{}'.format(ext),
                '-d', '{}'.format(str(path.resolve())),
                pdf_file,
            ]

            # Run function
            result = runner.invoke(cli, args)

            for slug in inquiries_slugs:
                # Build filename
                file_name = '{}.{}'.format(slug, ext)

                # Define filepath
                file = path / file_name

                # Assert existence
                assert file.exists()

            # TODO: Creation timestamp differs on every run
            if ext == 'ics':
                continue

            # Compare data
            for slug in inquiries_slugs:
                # Build filename
                file_name = '{}.{}'.format(slug, ext)

                # Define filepath
                file = path / file_name

                with open(str(file.resolve()), 'r') as data_file:
                    created = data_file.readlines()

                with open('tests/fixtures/{}/{}'.format(pdf_slug, file_name), 'r') as data_file:
                    expected = data_file.readlines()

                assert created == expected
