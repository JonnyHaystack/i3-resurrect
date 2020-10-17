import sys
from os.path import expandvars
from pathlib import Path


def eprint(*args, **kwargs):
    """
    Function for printing to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def filename_filter(filename):
    """
    Take a string and return a valid filename constructed from the string.
    """
    blacklist = '/\\:*"<>|'
    if filename is None:
        return filename

    # Remove blacklisted chars.
    for char in blacklist:
        filename = filename.replace(char, '')

    return filename


def resolve_directory(directory, profile=None):
    directory = Path(expandvars(directory)).expanduser()
    if profile is not None:
        directory = directory / 'profiles'
    return directory
