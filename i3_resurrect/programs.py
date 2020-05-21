import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import i3ipc
import psutil

from . import config
from . import treeutils
from . import util


def save(workspace, numeric, directory, profile):
    """
    Save the commands to launch the programs open in the specified workspace
    to a file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f'workspace_{workspace_id}_programs.json'
    if profile is not None:
        filename = f'{profile}_programs.json'
    programs_file = Path(directory) / filename

    # Print deprecation warning if using old dictionary method of writing
    # window command mappings.
    # TODO: Remove in 2.0.0
    window_command_mappings = config.get('window_command_mappings', [])
    if isinstance(window_command_mappings, dict):
        print('Warning: Defining window command mappings using a dictionary '
              'is deprecated and will be removed in favour of the list method '
              'in the next major version.')

    programs = get_programs(workspace, numeric)

    # Write list of commands to file as JSON.
    with programs_file.open('w') as f:
        f.write(json.dumps(programs, indent=2))


def read(workspace, directory, profile):
    """
    Read saved programs file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f'workspace_{workspace_id}_programs.json'
    if profile is not None:
        filename = f'{profile}_programs.json'
    programs_file = Path(directory) / filename

    programs = None
    try:
        programs = json.loads(programs_file.read_text())
    except FileNotFoundError:
        if profile is not None:
            util.eprint('Could not find saved programs for profile '
                        f'"{profile}"')
        else:
            util.eprint('Could not find saved programs for workspace '
                        f'"{workspace}"')
        sys.exit(1)
    return programs


def restore(workspace_name, saved_programs):
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
        cmdline = entry['command']
        working_directory = entry['working_directory']

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
            command = ' '.join(cmdline)
        else:
            command = cmdline

        # Execute command via i3 exec.
        i3.command(f'exec "cd \\"{working_directory}\\" && {command}"')


def get_programs(workspace, numeric):
    """
    Get running programs in specified workspace.

    Args:
        workspace: The workspace to search.
        numeric: Identify workspace by number instead of name.
    """
    # Loop through windows and save commands to launch programs on saved
    # workspace.
    programs = []
    for (con, pid) in windows_in_workspace(workspace, numeric):
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
            con['window_properties'],
            procinfo.cmdline(),
            exe,
        )
        if command in ([], ''):
            continue

        # Remove empty string arguments from command.
        command = [arg for arg in command if arg != '']

        terminals = config.get('terminals', [])

        try:
            # Obtain working directory using psutil.
            if con['window_properties']['class'] in terminals:
                # If the program is a terminal emulator, get the working
                # directory from its first subprocess.
                working_directory = procinfo.children()[0].cwd()
            else:
                working_directory = procinfo.cwd()
        except Exception:
            working_directory = str(Path.home())

        # Add the command to the list.
        programs.append({
            'command': command,
            'working_directory': working_directory
        })

    return programs


def windows_in_workspace(workspace, numeric):
    """
    Generator to iterate over windows in a workspace.

    Args:
        workspace: The name of the workspace whose windows to iterate over.
    """
    ws = treeutils.get_workspace_tree(workspace, numeric)
    for con in treeutils.get_leaves(ws):
        pid = get_window_pid(con)
        yield (con, pid)


def get_window_pid(con):
    """
    Get window PID using xprop.

    Args:
        con: The window container node whose PID to look up.
    """
    window_id = con['window']
    if window_id is None:
        return 0

    try:
        xprop_output = subprocess.check_output(
            shlex.split(f'xprop _NET_WM_PID -id {window_id}'),
            stderr=subprocess.DEVNULL,
        ).decode('utf-8').split(' ')
        pid = int(xprop_output[len(xprop_output) - 1])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 0

    return pid


def get_window_command(window_properties, cmdline, exe):
    """
    Gets a window command.

    This function starts with the process's cmdline, then loops through the
    window mappings and scores each matching rule. The command mapping with the
    highest score is then returned.
    """
    window_command_mappings = config.get('window_command_mappings', [])

    # Remove empty args from cmdline.
    cmdline = [arg for arg in cmdline if arg != '']

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

    command = cmdline

    # If window command mappings is a dictionary in the config file, use the
    # old way.
    # TODO: Remove in 2.0.0
    if isinstance(window_command_mappings, dict):
        window_class = window_properties['class']
        if window_class in window_command_mappings:
            command = window_command_mappings[window_class]
        return command

    # Find the mapping that gets the highest score.
    current_score = 0
    best_match = None
    for rule in window_command_mappings:
        # Calculate score.
        score = calc_rule_match_score(rule, window_properties)

        if score > current_score:
            current_score = score
            best_match = rule

    # If no match found, just use the original cmdline.
    if best_match is None:
        return command

    try:
        if 'command' not in best_match:
            command = []
        elif isinstance(best_match['command'], list):
            command = [arg.format(*cmdline) for arg in best_match['command']]
        else:
            command = shlex.split(best_match['command'].format(*cmdline))
    except IndexError:
        util.eprint('IndexError occurred while processing command mapping:\n'
                    f'  Mapping: {best_match}\n'
                    f'  Process cmdline: {cmdline}')

    return command


def calc_rule_match_score(rule, window_properties):
    """
    Score window command mapping match based on which criteria match.

    Scoring is done based on which criteria are considered "more specific".
    """
    # Window properties and value to add to score when match is found.
    criteria = {
        'window_role': 1,
        'class': 2,
        'instance': 3,
        'title': 10,
    }

    score = 0
    for criterion in criteria:
        if criterion in rule:
            # Score is zero if there are any non-matching criteria.
            if (criterion not in window_properties
                    or rule[criterion] != window_properties[criterion]):
                return 0
            score += criteria[criterion]
    return score
