import errno
import json
import os
import shlex
import string
import subprocess
import sys
from json.decoder import JSONDecodeError

import click
import i3ipc
import psutil
from wmctrl import Window


TERMINALS = []
CONFIG = {}


@click.group()
def main():
    global CONFIG
    global TERMINALS
    # Load config
    config_file = shlex.quote(
        os.path.expanduser('~/.config/i3-resurrect/config.json'))
    try:
        CONFIG = json.loads(open(config_file).read())
    except JSONDecodeError as e:
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

    pass


@main.command('save')
@click.option('--workspace', '-w', required=True, help='The workspace to save')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=os.path.expanduser('~/.i3/i3-resurrect/'),
              help='The directory to save the workspace to')
def save_workspace(workspace, directory):
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
    save_layout(workspace, directory)

    # Save commands to file.
    save_commands(workspace, directory)


def save_layout(workspace, directory):
    """
    Saves an i3 workspace layout to a file.
    """
    # Sanitise inputs properly.
    layout_file = shlex.quote(
        os.path.join(directory, f'workspace_{workspace}_layout.json'))
    workspace = shlex.quote(workspace)

    json_tree = subprocess.getoutput(f'i3-save-tree --workspace {workspace}')

    json_lines = iter(json_tree.splitlines())
    with open(layout_file, 'w') as file:
        # Strip out the comments that i3-save-tree includes, and remove
        # unwanted swallow criteria.
        for line in json_lines:
            if line.strip().startswith('// '):
                if 'class' in line:
                    processed_line = line.replace('// ', '   ', 1)
                    file.write(f'{processed_line}\n')
                elif 'instance' in line:
                    processed_line = line.replace('// ', '   ', 1)[:-1]
                    file.write(f'{processed_line}\n')
            else:
                file.write(f'{line}\n')


def save_commands(workspace, directory):
    """
    Saves the commands to launch the programs open in the specified workspace
    to a file.
    """
    i3 = i3ipc.Connection()

    commands = []

    with open(os.path.join(
            directory, f'workspace_{workspace}_commands.json'), 'w') as file:
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
              help='The directory to restore the workspace from')
def restore_workspace(workspace, directory):
    """
    Restore an i3 workspace including running programs.
    """
    # Load workspace layout
    layout_file = shlex.quote(
        os.path.join(directory, f'workspace_{workspace}_layout.json'))
    workspace = shlex.quote(workspace)
    subprocess.Popen(
        shlex.split(f'i3-msg "workspace --no-auto-back-and-forth {workspace}; '
                    f'append_layout {layout_file}"'),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Restore programs.
    commands_file = shlex.quote(
        os.path.join(directory, f'workspace_{workspace}_commands.json'))
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
