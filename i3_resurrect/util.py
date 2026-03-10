import sys
from natsort import natsorted
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
        filename = filename.replace(char, "")

    return filename


def resolve_directory(directory, profile=None, session=None):
    directory = Path(expandvars(directory)).expanduser()
    if profile is not None:
        directory = directory / "profiles"
    if session is not None:
        directory = directory / "sessions"
    return directory


def resolve_filetype(file):
    """
    Extract from file name if it is a layout of a program file.
    """
    name = file.name
    name = name[name.index("_") + 1 :]
    file_type = name[name.rfind("_") + 1 : name.index(".json")]
    return file_type


def resolve_workspace_name(file, is_profile=False):
    """
    Extract the name of the workspace or the profile from the file name.
    """
    name = file.name
    if not is_profile:
        name = name[name.index("_") + 1 :]
    workspace = name[: name.rfind("_")]
    return workspace


def get_list_of_workspaces(directory, is_profile=False):
    """
    Generate a list of all the workspaces or profiles present in a directory
    """
    workspaces = []
    for entry in directory.iterdir():
        if entry.is_file():
            workspaces.append(f'{resolve_workspace_name(entry, is_profile)} {resolve_filetype(entry)}')
    workspaces = natsorted(workspaces)
    return workspaces
