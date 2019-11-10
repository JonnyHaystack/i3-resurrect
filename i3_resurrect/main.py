import sys
from pathlib import Path

import click
import i3ipc
from natsort import natsorted

from . import layout
from . import programs
from . import util


@click.group(context_settings=dict(help_option_names=['-h', '--help'],
                                   max_content_width=150))
@click.version_option()
def main():
    pass


@main.command('save')
@click.option('--workspace', '-w',
              help='The workspace to save.\n[default: current workspace]')
@click.option('--numeric', '-n',
              is_flag=True,
              help='Select workspace by number instead of name.')
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
def save_workspace(workspace, numeric, directory, profile, swallow, target):
    """
    Save an i3 workspace's layout and running programs to a file.
    """
    if workspace is None:
        i3 = i3ipc.Connection()
        workspace = i3.get_tree().find_focused().workspace().name

    if profile is not None:
        directory = Path(directory) / 'profiles'

    # Create directory if non-existent.
    Path(directory).mkdir(parents=True, exist_ok=True)

    if target != 'programs_only':
        # Save workspace layout to file.
        swallow_criteria = swallow.split(',')
        layout.save(workspace, numeric, directory, profile, swallow_criteria)

    if target != 'layout_only':
        # Save running programs to file.
        programs.save(workspace, numeric, directory, profile)


@main.command('restore')
@click.option('--workspace', '-w',
              help='The workspace to restore.\n[default: current workspace]')
@click.option('--numeric', '-n',
              is_flag=True,
              help='Select workspace by number instead of name.')
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
def restore_workspace(workspace, numeric, directory, profile, target):
    """
    Restore i3 workspace layout and programs.
    """
    i3 = i3ipc.Connection()

    if workspace is None:
        workspace = i3.get_tree().find_focused().workspace().name

    if profile is not None:
        directory = Path(directory) / 'profiles'

    # Switch to the workspace which we are loading.
    if numeric:
        if workspace.isdigit():
            i3.command(
                f'workspace --no-auto-back-and-forth number {workspace}'
            )
        else:
            util.eprint('Invalid workspace number.')
            sys.exit(1)
    else:
        i3.command(f'workspace --no-auto-back-and-forth {workspace}')

    if target != 'programs_only':
        # Load workspace layout.
        layout.restore(workspace, numeric, directory, profile)

    if target != 'layout_only':
        # Restore programs.
        programs.restore(workspace, directory, profile)


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
