import errno
import json
import os
import shlex
import string
import subprocess
import sys

import click
import i3ipc
import psutil
from wmctrl import Window

import util

TERMINALS = []
CONFIG = {}
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    global CONFIG
    global TERMINALS

    # Load config
    config_file = os.path.expanduser('~/.config/i3-resurrect/config.json')
    try:
        CONFIG = json.loads(open(config_file).read())
    except json.decoder.JSONDecodeError as e:
        print(f'Error in config file: "{str(e)}"')
        exit(1)
    except PermissionError as e:
        print(f'Could not read config file: {str(e)}')
        exit(1)
    except FileNotFoundError:
        CONFIG = {}

    # Specify which window classes are terminals so that we know to extract the
    # working directory from the window title.
    TERMINALS = ['Gnome-terminal', 'Alacritty']


@main.command('save')
@click.option('--workspace', '-w', required=True, help='The workspace to save')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=os.path.expanduser('~/.i3/i3-resurrect/'),
              help='The directory to save the workspace to',
              show_default=True)
@click.option('--swallow', '-s',
              default='class,instance',
              help=('The swallow criteria to use. '
                    'Options: class, instance, title, window_role'),
              show_default=True)
def save_workspace(workspace, directory, swallow):
    """
    Save an i3 workspace's layout and commands to a file.
    """
    # Create directory if non-existent.
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Save workspace layout to file.
    swallow_criteria = swallow.split(',')
    save_layout(workspace, directory, swallow_criteria)

    # Save commands to file.
    save_commands(workspace, directory)


def save_layout(workspace, directory, swallow_criteria):
    """
    Saves an i3 workspace layout to a file.
    """
    layout_file = os.path.join(directory, f'workspace_{workspace}_layout.json')

    i3 = i3ipc.Connection()

    # Get full workspace layout tree from i3.
    root = json.loads(i3.message(i3ipc.MessageType.GET_TREE, ''))
    workspace_tree = None
    for output in root['nodes']:
        for container in output['nodes']:
            if container['type'] != 'con':
                pass
            for ws in container['nodes']:
                if ws['name'] == workspace:
                    workspace_tree = ws

    with open(layout_file, 'w') as file:
        # Build new workspace tree suitable for restoring and write it to a
        # file.
        file.write(
            json.dumps(
                util.build_tree(workspace_tree, swallow_criteria),
                indent=2,
            )
        )


def save_commands(workspace, directory):
    """
    Saves the commands to launch the programs open in the specified workspace
    to a file.
    """
    i3 = i3ipc.Connection()

    commands = []

    commands_file = os.path.join(
        directory,
        f'workspace_{workspace}_commands.json',
    )

    with open(commands_file, 'w') as file:
        # Loop through windows and save commands to launch programs on saved
        # workspace.
        commands = []
        for con in i3.get_tree():
            if (not con.window
                    or con.parent.type == 'dockarea'
                    or con.workspace().name != workspace):
                continue

            # Get information on the window.
            try:
                window = Window.by_id(con.window)[0]
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

            pid = window.pid

            if pid == 0:
                continue

            # Get process info for the window.
            procinfo = psutil.Process(pid)

            try:
                # Obtain working directory using psutil.
                working_directory = procinfo.cwd()
            except Exception:
                working_directory = '~'

            # If the program is a terminal, get the working directory from the
            # window title. Yes, this is a complete hack.
            if con.window_class in TERMINALS:
                working_directory = con.name.strip()
                # Remove any non-ASCII characters.
                filter(lambda x: x in set(string.printable), working_directory)

            # Expand ~ to full path to home directory.
            working_directory = os.path.expanduser(working_directory)

            # Create command to launch program.
            # If there is a special command mapping for this program, use that.
            window_command_mappings = CONFIG.get('window_command_mappings', {})
            if con.window_class in window_command_mappings:
                command = window_command_mappings[con.window_class]
            else:
                # If the program has no special mapping, launch it by executing
                # the first index of the cmdline. This should work for almost
                # all programs.
                command = procinfo.cmdline()

            # Add the command to the list.
            commands.append({
                'command': command,
                'working_directory': working_directory
            })

        # Write list of commands to file as JSON.
        file.write(json.dumps(commands, indent=2))


@main.command('restore')
@click.option('--workspace', '-w', required=True,
              help='The workspace to restore')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=os.path.expanduser('~/.i3/i3-resurrect/'),
              help='The directory to restore the workspace from',
              show_default=True)
def restore_workspace(workspace, directory):
    """
    Restores an i3 workspace including running programs.
    """
    # Load workspace layout.
    restore_layout(workspace, directory)

    # Restore programs.
    restore_programs(workspace, directory)


def restore_layout(workspace, directory):
    """
    Restores an i3 workspace layout.
    """
    layout_file = shlex.quote(
        os.path.join(directory, f'workspace_{workspace}_layout.json'))

    i3 = i3ipc.Connection()
    # Switch to the workspace which we are loading.
    i3.command(f'workspace --no-auto-back-and-forth {workspace}')
    # Load the layout into the workspace.
    i3.command(f'append_layout {layout_file}')


def restore_programs(workspace, directory):
    """
    Restores the running programs from an i3 workspace.
    """
    commands_file = os.path.join(
        directory,
        f'workspace_{workspace}_commands.json',
    )
    commands = json.loads(open(commands_file).read())
    for entry in commands:
        command = entry['command']
        working_directory = entry['working_directory']

        # If the working directory does not exist, set working directory to
        # user's home directory.
        if not os.path.exists(working_directory):
            working_directory = os.path.expanduser('~')

        # If command has multiple arguments, split them into an array.
        if isinstance(command, list):
            cmdline = command
        else:
            cmdline = shlex.split(command)

        # Execute command as subprocess.
        subprocess.Popen(
            cmdline,
            cwd=working_directory,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


# Function for printing to stderr.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


if __name__ == '__main__':
    main()
