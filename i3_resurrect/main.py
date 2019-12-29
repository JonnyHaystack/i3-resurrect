import sys
from pathlib import Path

import click
import i3ipc
from natsort import natsorted

from . import config
from . import layout
from . import programs
from . import util

DEFAULT_DIRECTORY = config.get('directory', '~/.i3/i3-resurrect/')


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
              default=DEFAULT_DIRECTORY,
              help=('The directory to save the workspace to.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p',
              default=None,
              help=('The profile to save.'))
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

    directory = util.resolve_directory(directory, profile)

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
              default=DEFAULT_DIRECTORY,
              help=('The directory to restore the workspace from.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p',
              default=None,
              help=('The profile to restore.'))
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

    directory = util.resolve_directory(directory, profile)

    if numeric and not workspace.isdigit():
        util.eprint('Invalid workspace number.')
        sys.exit(1)

    # Get layout name from file.
    workspace_layout = layout.read(workspace, directory)
    if 'name' in workspace_layout and profile is None:
        workspace_name = workspace_layout['name']
    else:
        workspace_name = workspace

    # Switch to the workspace which we are loading.
    i3.command(f'workspace --no-auto-back-and-forth "{workspace_name}"')

    if target != 'programs_only':
        # Load workspace layout.
        layout.restore(workspace_name, workspace_layout)

    if target != 'layout_only':
        # Restore programs.
        saved_programs = programs.read(workspace, directory)
        programs.restore(workspace_name, saved_programs)


@main.command('ls')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=DEFAULT_DIRECTORY,
              help=('The directory to search in.\n'
                    '[default: ~/.i3/i3-resurrect]'))
@click.option('--profile', '-p',
              default=None,
              help=('list saved workspaces from given profile.'))
@click.option('--profiles', '-P',
              is_flag=True,
              help=('list saved profiles names.'))
def list_workspaces(directory, profile, profiles):
    """
    List saved workspaces or profiles.
    """
    directory = util.resolve_directory(directory, profile)

    directory = Path(directory)
    items = []
    # import ipdb; ipdb.set_trace()
    for entry in directory.iterdir():
        if not profiles and entry.is_file():
            # List workspaces
            name = entry.name
            if name.rfind('workspace_') != -1:
                name = name[name.index('_') + 1:]
                workspace = name[:name.rfind('_')]
                file_type = name[name.rfind('_') + 1:name.index('.json')]
                items.append(f'Workspace {workspace} {file_type}')
        elif profiles and entry.is_dir():
            # List profiles names
            profile = entry.name
            items.append(f'Profile {profile}')
    items = natsorted(items)
    for item in items:
        print(item)


@main.command('rm')
@click.option('--workspace', '-w',
              default=None,
              help='The saved workspace to delete.')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False),
              default=DEFAULT_DIRECTORY,
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
    directory = util.resolve_directory(directory, profile)

    if workspace is not None:
        workspace_id = util.filename_filter(workspace)
        programs_filename = f'workspace_{workspace_id}_programs.json'
        layout_filename = f'workspace_{workspace_id}_layout.json'
    else:
        util.eprint('--workspace must be specified.')
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
