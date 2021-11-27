import setuptools

# Load README
with open('README.md', 'r', encoding='utf8') as file:
    long_description = file.read()

# Define package metadata
setuptools.setup(
    name='sitzungsdienst',
    version='1.4.6',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    description='A simple Python utility for converting the weekly assignment PDF by the "Staatsanwaltschaft Freiburg"',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/S1SYPHOS/sitzungsdienst',
    license='MIT',
    project_urls={
        'Issues': 'https://github.com/S1SYPHOS/sitzungsdienst/issues',
    },
    entry_points='''
        [console_scripts]
        sta=src.cli:cli
    ''',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'click',
        'ics',
        'pandas',
        'pypdf2',
        'pytz',
    ],
    python_requires='>=3.6',
)
