import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import click
import i3ipc
import psutil
from wmctrl import Window

from . import config
from . import util

i3 = i3ipc.Connection()


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def main():
    pass


@main.command('save')
@click.option('--workspace', '-w',
              default=i3.get_tree().find_focused().workspace().name,
              help='The workspace to save.')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help='The directory to save the workspace to.',
              show_default=True)
@click.option('--swallow', '-s',
              default='class,instance',
              help=('The swallow criteria to use. '
                    'Options: class, instance, title, window_role'),
              show_default=True)
@click.option('--layout-only', 'target',
              flag_value='layout_only',
              help='Only save layout.')
@click.option('--programs-only', 'target',
              flag_value='programs_only',
              help='Only save running programs.')
def save_workspace(workspace, directory, swallow, target):
    """
    Save an i3 workspace's layout and running programs to a file.
    """
    # Create directory if non-existent.
    Path(directory).mkdir(parents=True, exist_ok=True)

    if target != 'programs_only':
        # Save workspace layout to file.
        swallow_criteria = swallow.split(',')
        save_layout(workspace, directory, swallow_criteria)

    if target != 'layout_only':
        # Save running programs to file.
        save_commands(workspace, directory)


def save_layout(workspace, directory, swallow_criteria):
    """
    Save an i3 workspace layout to a file.
    """
    layout_file = Path(directory) / f'workspace_{workspace}_layout.json'

    workspace_tree = get_workspace_tree(workspace)

    with layout_file.open('w') as f:
        # Build new workspace tree suitable for restoring and write it to a
        # file.
        f.write(
            json.dumps(
                util.build_tree(workspace_tree, swallow_criteria),
                indent=2,
            )
        )


def save_commands(workspace, directory):
    """
    Save the commands to launch the programs open in the specified workspace
    to a file.
    """
    commands_file = Path(directory) / f'workspace_{workspace}_programs.json'

    window_command_mappings = config.get('window_command_mappings', {})
    terminals = config.get('terminals', [])

    # Loop through windows and save commands to launch programs on saved
    # workspace.
    commands = []
    for (con, window) in windows_in_workspace(workspace):
        pid = window.pid

        if pid == 0:
            continue

        # Get process info for the window.
        procinfo = psutil.Process(pid)

        window_class = con['window_properties']['class']
        try:
            # Obtain working directory using psutil.
            if window_class in terminals:
                # If the program is a terminal emulator, get the working
                # directory from its first subprocess.
                working_directory = procinfo.children()[0].cwd()
            else:
                working_directory = procinfo.cwd()
        except Exception:
            working_directory = str(Path.home())

        # Create command to launch program.
        # If there is a special command mapping for this program, use that.
        if window_class in window_command_mappings:
            command = window_command_mappings[window_class]
        else:
            # If the program has no special mapping, just use the process's
            # cmdline.
            command = procinfo.cmdline()

        # Add the command to the list.
        commands.append({
            'command': command,
            'working_directory': working_directory
        })

        # Write list of commands to file as JSON.
    with commands_file.open('w') as f:
        f.write(json.dumps(commands, indent=2))


@main.command('restore')
@click.option('--workspace', '-w',
              default=i3.get_tree().find_focused().workspace().name,
              help='The workspace to restore.')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help='The directory to restore the workspace from.',
              show_default=True)
@click.option('--layout-only', 'target',
              flag_value='layout_only',
              help='Only restore layout.')
@click.option('--programs-only', 'target',
              flag_value='programs_only',
              help='Only restore running programs.')
def restore_workspace(workspace, directory, target):
    """
    Restore i3 workspace layout and programs.
    """
    # Switch to the workspace which we are loading.
    i3.command(f'workspace --no-auto-back-and-forth {workspace}')

    if target != 'programs_only':
        # Load workspace layout.
        restore_layout(workspace, directory)

    if target != 'layout_only':
        # Restore programs.
        restore_programs(workspace, directory)


def restore_programs(workspace, directory):
    """
    Restore the running programs from an i3 workspace.
    """
    commands_file = Path(directory) / f'workspace_{workspace}_programs.json'
    commands = json.loads(commands_file.read_text())
    for entry in commands:
        command = entry['command']
        working_directory = entry['working_directory']

        # If the working directory does not exist, set working directory to
        # user's home directory.
        if not Path(working_directory).exists():
            working_directory = Path.home()

        # If command has multiple arguments, split them into an array.
        if isinstance(command, list):
            cmdline = command
        else:
            cmdline = shlex.split(command)

        # Execute command as subprocess.
        subprocess.Popen(
            cmdline,
            cwd=working_directory,
            env={**os.environ, **{'PWD': working_directory}},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )


def restore_layout(workspace, directory):
    """
    Restore an i3 workspace layout.
    """
    # Switch to the workspace which we are loading.
    i3.command(f'workspace --no-auto-back-and-forth {workspace}')

    # Get ids of all placeholder or normal windows in workspace.
    window_ids = []
    placeholder_window_ids = []
    for (con, window) in windows_in_workspace(workspace):
        pid = window.pid

        # If window has no process, add it to list of placeholder windows.
        if pid == 0:
            placeholder_window_ids.append(int(window.id, 16))
            continue

        # Otherwise, add it to the list of regular windows.
        window_ids.append(int(window.id, 16))

    # Unmap all windows in workspace.
    for window_id in window_ids:
        xdo_unmap_window(window_id)

    # Remove any remaining placeholder windows in workspace.
    for window_id in placeholder_window_ids:
        xdo_kill_window(window_id)

    # Create fresh placeholder windows by appending layout to workspace.
    layout_file = shlex.quote(
        str(Path(directory) / f'workspace_{workspace}_layout.json')
    )
    i3.command(f'append_layout {layout_file}')

    # Map all unmapped windows.
    for window_id in window_ids:
        xdo_map_window(window_id)


def eprint(*args, **kwargs):
    """
    Function for printing to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def get_workspace_tree(workspace):
    """
    Get full workspace layout tree from i3.
    """
    root = json.loads(i3.message(i3ipc.MessageType.GET_TREE, ''))
    for output in root['nodes']:
        for container in output['nodes']:
            if container['type'] != 'con':
                pass
            for ws in container['nodes']:
                if ws['name'] == workspace:
                    return ws
    return {}


def windows_in_container(container):
    """
    Generator to iterate over windows in a container.

    Args:
        container: The container to traverse.
    """
    # Base case.
    if container is None:
        return

    nodes = container['nodes']

    if nodes == []:
        return

    # Step case.
    for node in nodes:
        if 'window_properties' in node:
            yield node
        yield from windows_in_container(node)


def windows_in_workspace(workspace):
    """
    Generator to iterate over windows in a workspace.

    Args:
        workspace: The name of the workspace whose windows to iterate over.
    """
    ws = get_workspace_tree(workspace)
    for con in windows_in_container(ws):
        # Get information on the window.
        try:
            window = Window.by_id(con['window'])[0]
        except ValueError as e:
            eprint(str(e))
            continue

        # Pre-emptively attempt to catch error
        try:
            window
        except NameError as e:
            eprint(str(e))
            continue

        if not window:
            continue

        yield (con, window)


def xdo_unmap_window(window_id):
    command = shlex.split(f'xdotool windowunmap {window_id}')
    subprocess.call(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def xdo_map_window(window_id):
    command = shlex.split(f'xdotool windowmap {window_id}')
    subprocess.call(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def xdo_kill_window(window_id):
    command = shlex.split(f'xdotool windowkill {window_id}')
    subprocess.call(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


if __name__ == '__main__':
    main()
