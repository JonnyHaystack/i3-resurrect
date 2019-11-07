import json
import sys
import tempfile
from pathlib import Path

import click
import i3ipc
from natsort import natsorted
import psutil

from . import config
from . import util

i3 = i3ipc.Connection()


@click.group(context_settings=dict(help_option_names=['-h', '--help'],
                                   max_content_width=150))
@click.version_option()
def main():
    pass


@main.command('save')
@click.option('--workspace', '-w',
              default=i3.get_tree().find_focused().workspace().name,
              help='The workspace to save.\n[default: current workspace]')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help=('The directory to save the workspace to.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p',
              default=None,
              help=('The profile to save the workspace to.'))
@click.option('--swallow', '-s',
              default='class,instance',
              help=('The swallow criteria to use.\n'
                    '[options: class,instance,title,window_role]\n'
                    '[default: class,instance]'))
@click.option('--layout-only', 'target',
              flag_value='layout_only',
              help='Only save layout.')
@click.option('--programs-only', 'target',
              flag_value='programs_only',
              help='Only save running programs.')
def save_workspace(workspace, directory, profile, swallow, target):
    """
    Save an i3 workspace's layout and running programs to a file.
    """
    if profile is not None:
        directory = Path(directory) / 'profiles'

    # Create directory if non-existent.
    Path(directory).mkdir(parents=True, exist_ok=True)

    if target != 'programs_only':
        # Save workspace layout to file.
        swallow_criteria = swallow.split(',')
        save_layout(workspace, directory, profile, swallow_criteria)

    if target != 'layout_only':
        # Save running programs to file.
        save_programs(workspace, directory, profile)


def save_layout(workspace, directory, profile, swallow_criteria):
    """
    Save an i3 workspace layout to a file.
    """
    filename = f'workspace_{workspace}_layout.json'
    if profile is not None:
        filename = f'{profile}_layout.json'
    layout_file = Path(directory) / filename

    workspace_tree = util.get_workspace_tree(workspace)

    with layout_file.open('w') as f:
        # Build new workspace tree suitable for restoring and write it to a
        # file.
        f.write(
            json.dumps(
                util.build_layout(workspace_tree, swallow_criteria),
                indent=2,
            )
        )


def save_programs(workspace, directory, profile):
    """
    Save the commands to launch the programs open in the specified workspace
    to a file.
    """
    filename = f'workspace_{workspace}_programs.json'
    if profile is not None:
        filename = f'{profile}_programs.json'
    programs_file = Path(directory) / filename

    terminals = config.get('terminals', [])

    # Print deprecation warning if using old dictionary method of writing
    # window command mappings.
    # TODO: Remove in 2.0.0
    window_command_mappings = config.get('window_command_mappings', [])
    if isinstance(window_command_mappings, dict):
        print('Warning: Defining window command mappings using a dictionary '
              'is deprecated and will be removed in favour of the list method '
              'in the next major version.')

    # Loop through windows and save commands to launch programs on saved
    # workspace.
    programs = []
    for (con, pid) in util.windows_in_workspace(workspace):
        if pid == 0:
            continue

        # Get process info for the window.
        procinfo = psutil.Process(pid)

        # Create command to launch program.
        command = util.get_window_command(
            con['window_properties'],
            procinfo.cmdline(),
        )
        if command in ([], ''):
            continue

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

        # Write list of commands to file as JSON.
    with programs_file.open('w') as f:
        f.write(json.dumps(programs, indent=2))


@main.command('restore')
@click.option('--workspace', '-w',
              default=i3.get_tree().find_focused().workspace().name,
              help='The workspace to restore.\n[default: current workspace]')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help=('The directory to restore the workspace from.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p',
              default=None,
              help=('The profile to restore the workspace from.'))
@click.option('--layout-only', 'target',
              flag_value='layout_only',
              help='Only restore layout.')
@click.option('--programs-only', 'target',
              flag_value='programs_only',
              help='Only restore running programs.')
def restore_workspace(workspace, directory, profile, target):
    """
    Restore i3 workspace layout and programs.
    """
    if profile is not None:
        directory = Path(directory) / 'profiles'

    # Switch to the workspace which we are loading.
    i3.command(f'workspace --no-auto-back-and-forth {workspace}')

    if target != 'programs_only':
        # Load workspace layout.
        restore_layout(workspace, directory, profile)

    if target != 'layout_only':
        # Restore programs.
        restore_programs(workspace, directory, profile)


def restore_programs(workspace, directory, profile):
    """
    Restore the running programs from an i3 workspace.
    """
    filename = f'workspace_{workspace}_programs.json'
    if profile is not None:
        filename = f'{profile}_programs.json'
    programs_file = Path(directory) / filename

    # Read saved programs file.
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

    for entry in programs:
        cmdline = entry['command']
        working_directory = entry['working_directory']

        # If the working directory does not exist, set working directory to
        # user's home directory.
        if not Path(working_directory).exists():
            working_directory = Path.home()

        # If cmdline is array, join it into one string for use with i3's exec
        # command.
        if isinstance(cmdline, list):
            # Quote each argument of the command in case some of them contain
            # spaces.
            for i in range(0, len(cmdline)):
                cmdline[i] = f'"{cmdline[i]}"'
            command = ' '.join(cmdline)
        else:
            command = cmdline

        # Execute command via i3 exec.
        i3.command(f'exec cd "{working_directory}" && {command}')


def restore_layout(workspace, directory, profile):
    """
    Restore an i3 workspace layout.
    """
    filename = f'workspace_{workspace}_layout.json'
    if profile is not None:
        filename = f'{profile}_layout.json'
    layout_file = Path(directory) / filename

    # Read saved layout file.
    layout = None
    try:
        layout = json.loads(layout_file.read_text())
        if layout == {}:
            return
    except FileNotFoundError:
        if profile is not None:
            util.eprint(f'Could not find saved layout for profile "{profile}"')
        else:
            util.eprint('Could not find saved layout for workspace '
                        f'"{workspace}"')
        sys.exit(1)

    window_ids = []
    placeholder_window_ids = []

    # Get ids of all placeholder or normal windows in workspace.
    ws = util.get_workspace_tree(workspace)
    windows = util.get_leaves(ws)
    for con in windows:
        if util.is_placeholder(con):
            # If window is a placeholder, add it to list of placeholder
            # windows.
            placeholder_window_ids.append(con['window'])
        else:
            # Otherwise, add it to the list of regular windows.
            window_ids.append(con['window'])

    # Unmap all non-placeholder windows in workspace.
    for window_id in window_ids:
        util.xdo_unmap_window(window_id)

    # Remove any remaining placeholder windows in workspace so that we don't
    # have duplicates.
    for window_id in placeholder_window_ids:
        util.xdo_kill_window(window_id)

    try:
        # append_layout can only insert nodes so we must separately change the
        # layout mode of the workspace node.
        ws_layout_mode = layout.get('layout', 'default')
        tree = i3.get_tree()
        focused = tree.find_focused()
        workspace_node = focused.workspace()
        workspace_node.command(f'layout {ws_layout_mode}')

        # We don't want to pass the whole layout file because we don't want to
        # append a new workspace. append_layout requires a file path so we must
        # extract the part of the json that we want and store it in a tempfile.
        restorable_layout = (
            layout.get('nodes', []) + layout.get('floating_nodes', []),
        )
        restorable_layout_file = tempfile.NamedTemporaryFile(
            mode='w',
            prefix='i3-resurrect_',
        )
        restorable_layout_file.write(json.dumps(restorable_layout))
        restorable_layout_file.flush()

        # Create fresh placeholder windows by appending layout to workspace.
        i3.command(f'append_layout {restorable_layout_file.name}')

        # Delete tempfile.
        restorable_layout_file.close()
    except FileNotFoundError:
        if profile is not None:
            util.eprint(f'Could not find saved layout for profile "{profile}"')
        else:
            util.eprint('Could not find saved layout for workspace '
                        f'"{workspace}"')
    except Exception as e:
        util.eprint('Error occurred restoring workspace layout. Note that if '
                    'the layout was saved by a version prior to 1.4.0 it must '
                    'be recreated.')
        util.eprint(str(e))
    finally:
        # Map all unmapped windows. We use finally because we don't want the
        # user to lose their windows no matter what.
        for window_id in window_ids:
            util.xdo_map_window(window_id)


@main.command('ls')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help=('The directory to search in.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.argument('item',
                type=click.Choice(['workspaces', 'profiles']),
                default='workspaces')
def list_workspaces(directory, item):
    """
    List saved workspaces or profiles.
    """
    if item == 'workspaces':
        directory = Path(directory)
        workspaces = []
        for entry in directory.iterdir():
            if entry.is_file():
                tokens = entry.name.split('_')
                workspace = tokens[1]
                temp = tokens[2]
                file_type = temp[:temp.index('.json')]
                workspaces.append(f'Workspace {workspace} {file_type}')
        workspaces = natsorted(workspaces)
        for workspace in workspaces:
            print(workspace)
    else:
        directory = Path(directory) / 'profiles'
        profiles = []
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    tokens = entry.name.split('_')
                    profile = tokens[0]
                    temp = tokens[1]
                    file_type = temp[:temp.index('.json')]
                    profiles.append(f'Profile {profile} {file_type}')
            profiles = natsorted(profiles)
            for profile in profiles:
                print(profile)
        except FileNotFoundError:
            print('No profiles found')


@main.command('rm')
@click.option('--workspace', '-w',
              default=None,
              help='The saved workspace to delete.')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=Path('~/.i3/i3-resurrect/').expanduser(),
              help=('The directory to delete from.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p', default=None, help=('The profile to delete.'))
@click.option('--layout-only', 'target',
              flag_value='layout_only',
              help='Only delete saved layout.')
@click.option('--programs-only', 'target',
              flag_value='programs_only',
              help='Only delete saved programs.')
def remove(workspace, directory, profile, target):
    """
    Remove saved layout or programs.
    """
    if profile is not None:
        directory = Path(directory) / 'profiles'
        programs_filename = f'{profile}_programs.json'
        layout_filename = f'{profile}_layout.json'
    elif workspace is not None:
        programs_filename = f'workspace_{workspace}_programs.json'
        layout_filename = f'workspace_{workspace}_layout.json'
    else:
        util.eprint('Either --profile or --workspace must be specified.')
        sys.exit(1)
    programs_file = Path(directory) / programs_filename
    layout_file = Path(directory) / layout_filename

    if target != 'programs_only':
        # Delete programs file.
        programs_file.unlink()

    if target != 'layout_only':
        # Delete layout file.
        layout_file.unlink()


if __name__ == '__main__':
    main()
