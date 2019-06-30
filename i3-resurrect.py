import sys
from subprocess import getoutput

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

def main():
    i3 = i3ipc.Connection()
    json_tree = getoutput('i3-save-tree --workspace 1')
    json_lines = list(iter(json_tree.splitlines()))
    for line in json_lines:
        print(line)

    # Loop through windows.
    for con in i3.get_tree():
        if (not con.window
                or con.parent.type == 'dockarea'
                or con.workspace().name != sys.argv[1]):
            continue

        # Get information on this window.
        try:
            window = Window.by_id(con.window)[0]
        except ValueError:
            continue
        try:
            window
        except NameError:
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
            working_directory = str(con.name.encode('ascii', 'ignore').strip())

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
            # If the program has no special mapping, launch it by cd'ing to its
            # working directory (obtained by psutil) and then executing the
            # first index of the cmdline (hopefully this will work for almost
            # all programs I use at least).
            command = '(cd {0}; {1} &)'.format(
                working_directory,
                procinfo.cmdline()[0],
            )
        # Print the command.
        print('\n{0}'.format(command))


if __name__ == '__main__':
    main()
