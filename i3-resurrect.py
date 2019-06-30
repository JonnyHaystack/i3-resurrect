import errno
import os
import subprocess
import sys

import click
import i3ipc
import psutil
from wmctrl import Window


# Function for printing to stderr.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Command mappings for specific programs whose process command is not the same
# as the one that should be used to launch it.
# Format: 'class': 'command'
window_class_command_mappings = {
    'Gnome-terminal': 'gnome-terminal',
    'Alacritty': 'alacritty',
    'qutebrowser': 'qutebrowser',
}

# Specify which window classes are terminals so that we know to extract the
# working directory from the window title.
TERMINALS = ['Gnome-terminal', 'Alacritty']

@click.group()
def main():
    pass

@main.command()
@click.option('--workspace', '-w', help='The workspace to save')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=os.path.expanduser('~/.i3/i3-resurrect/'),
              help='Directory to use for saving/restoring workspaces')
def save(workspace, directory):
    """
    Saves an i3 workspace's layout and commands to launch open programs to a
    file.
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
    json_tree = subprocess.getoutput(f'i3-save-tree --workspace {workspace}')
    json_lines = iter(json_tree.splitlines())
    with open(os.path.join(
            directory, f'workspace_{workspace}.json'), 'w') as file:
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
    with open(os.path.join(
            directory, f'workspace_{workspace}.sh'), 'w') as file:
        # Write hashbang to start of file.
        file.write('#!/usr/bin/env bash')

        i3 = i3ipc.Connection()

        # Loop through windows and save commands to launch programs on saved
        # workspace.
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
                working_directory = procinfo.cwd()
            except Exception:
                working_directory = '$HOME'

            # If the program is a terminal, get the working directory from the
            # window title.
            if con.window_class in TERMINALS:
                # Remove any non-ASCII characters.
                working_directory = str(con.name
                                        .encode('ascii', 'ignore')
                                        .strip())

            # Change ~ to $HOME.
            working_directory = working_directory.replace('~', '$HOME')

            # Create command to launch program.
            # If there is a special command mapping for this program, use that.
            if con.window_class in window_class_command_mappings:
                command = '(cd {0}; {1} &)'.format(
                    working_directory,
                    window_class_command_mappings[con.window_class],
                )
            else:
                # If the program has no special mapping, launch it by cd'ing to
                # its working directory (obtained by psutil) and then executing
                # the first index of the cmdline (this works for almost all
                # programs I use at least).
                command = '(cd {0}; {1} &)'.format(
                    working_directory,
                    procinfo.cmdline()[0],
                )
            # Print the command.
            file.write(f'\n\n{command}')


if __name__ == '__main__':
    main()
