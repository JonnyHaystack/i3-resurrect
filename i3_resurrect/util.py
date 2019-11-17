import sys


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
