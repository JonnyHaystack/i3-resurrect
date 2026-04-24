import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import i3ipc
import psutil

from i3_resurrect.types import WindowCommandMapping

from . import config
from . import treeutils
from . import util


def save(workspace, numeric, directory, profile):
    """
    Save the commands to launch the programs open in the specified workspace
    to a file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f"workspace_{workspace_id}_programs.json"
    if profile is not None:
        filename = f"{profile}_programs.json"
    programs_file = Path(directory) / filename

    programs = get_programs(workspace, numeric)

    # Write list of commands to file as JSON.
    with programs_file.open("w") as f:
        f.write(json.dumps(programs, indent=2))


def read(workspace: str, directory: Path, profile: str | None) -> list[dict]:
    """
    Read saved programs file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f"workspace_{workspace_id}_programs.json"
    if profile is not None:
        filename = f"{profile}_programs.json"
    programs_file = Path(directory) / filename

    programs = None
    try:
        programs = json.loads(programs_file.read_text())
    except FileNotFoundError:
        if profile is not None:
            util.eprint(f'Could not find saved programs for profile "{profile}"')
        else:
            util.eprint(f'Could not find saved programs for workspace "{workspace}"')
        sys.exit(1)
    return programs


def restore(workspace_name: str, saved_programs: list[dict]):
    """
    Restore the running programs from an i3 workspace.
    """
    # Remove already running programs from the list of program to restore.
    running_programs = get_programs(workspace_name, False)
    for program in running_programs:
        if program in saved_programs:
            saved_programs.remove(program)

    i3 = i3ipc.Connection()
    for entry in saved_programs:
        cmdline = entry["command"]
        working_directory = entry["working_directory"]

        # If the working directory does not exist, set working directory to
        # user's home directory.
        if not Path(working_directory).exists():
            working_directory = Path.home()

        # If cmdline is array, join it into one string for use with i3's exec
        # command.
        if isinstance(cmdline, list):
            # Quote each argument of the command in case some of
            # them contain spaces. Also protect quotes contained in the
            # arguments and those to be added from i3's command parser.
            cmdline = [
                '\\"' + arg.replace('"', '\\\\\\"') + '\\"'
                for arg in cmdline
                if arg != ""
            ]
            command = " ".join(cmdline)
        else:
            command = cmdline

        # Execute command via i3 exec.
        i3.command(f'exec "cd \\"{working_directory}\\" && {command}"')


def get_programs(workspace: str, numeric: bool) -> list[dict]:
    """
    Get running programs in specified workspace.

    Args:
        workspace: The workspace to search.
        numeric: Identify workspace by number instead of name.
    """
    # Loop through windows and save commands to launch programs on saved
    # workspace.
    programs = []
    for con, pid in windows_in_workspace(workspace, numeric):
        if pid == 0:
            continue

        # Get process info for the window.
        procinfo = psutil.Process(pid)

        # Try to get absolute path to executable.
        exe = None
        try:
            exe = procinfo.exe()
        except Exception:
            pass

        # Create command to launch program.
        command = get_window_command(
            con["window_properties"],
            procinfo.cmdline(),
            exe,
        )
        if command in ([], ""):
            continue

        # Remove empty string arguments from command.
        command = [arg for arg in command if arg != ""]

        terminals = config.get("terminals", [])

        try:
            # Obtain working directory using psutil.
            if con["window_properties"]["class"] in terminals:
                # If the program is a terminal emulator, get the working
                # directory from its first subprocess.
                working_directory = procinfo.children()[0].cwd()
            else:
                working_directory = procinfo.cwd()
        except Exception:
            working_directory = str(Path.home())

        # Add the command to the list.
        programs.append({"command": command, "working_directory": working_directory})

    return programs


def windows_in_workspace(workspace: str, numeric: bool):
    """
    Generator to iterate over windows in a workspace.

    Args:
        workspace: The name of the workspace whose windows to iterate over.
    """
    ws = treeutils.get_workspace_tree(workspace, numeric)
    for con in treeutils.get_leaves(ws):
        pid = get_window_pid(con)
        yield (con, pid)


def get_window_pid(con) -> int:
    """
    Get window PID using xprop.

    Args:
        con: The window container node whose PID to look up.
    """
    window_id = con["window"]
    if window_id is None:
        return 0

    try:
        xprop_output = (
            subprocess.check_output(
                shlex.split(f"xprop _NET_WM_PID -id {window_id}"),
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .split(" ")
        )
        pid = int(xprop_output[len(xprop_output) - 1])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 0

    return pid


def get_window_command(
    window_properties: dict, cmdline: list[str], exe: str | None
) -> list[str]:
    """
    Gets a window command.

    This function starts with the process's cmdline, then loops through the
    window mappings and scores each matching rule. The command mapping with the
    highest score is then returned.
    """
    # Remove empty args from cmdline.
    cmdline = [arg for arg in cmdline if arg != ""]

    # If cmdline has only one argument which is not a known executable path,
    # try to split it. This means we can cover cases where the process
    # overwrote its own cmdline, with the tradeoff that legitimate single
    # argument cmdlines with a relative executable path containing spaces will
    # be broken.
    if len(cmdline) == 1 and shutil.which(cmdline[0]) is None:
        cmdline = shlex.split(cmdline[0])
    # Use the absolute executable path in case a relative path was used.
    if exe is not None:
        cmdline[0] = exe

    best_match = WindowCommandMapping.find_best_matching_rule(
        window_properties, config.get_window_command_mappings()
    )

    # If no match found, just use the original cmdline.
    if best_match is None:
        return cmdline

    return best_match.format_cmdline(cmdline)
