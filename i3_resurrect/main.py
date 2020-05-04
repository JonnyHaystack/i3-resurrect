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
              is_flag=True,
              help='Save workspace(s).')
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
@click.argument('workspaces', nargs=-1, default=None)
def save_workspace(workspace, numeric, directory, profile, swallow, target, workspaces):
    """
    Save i3 workspace(s) layout(s) or whole session and running programs to a file.

    Use cases:

    i3-resurrect save [--workspace] WORKSPACES

    WORKSPACES are the workspace(s) to save. [default: current workspace]
    """
    i3 = i3ipc.Connection()
    if not workspaces:
        # set default value
        workspaces = (i3.get_tree().find_focused().workspace().name, )

    directory = util.resolve_directory(directory, profile)

    # Create directory if non-existent.
    Path(directory).mkdir(parents=True, exist_ok=True)

    if target != 'programs_only':
        swallow_criteria = swallow.split(',')

    for workspace_id in workspaces:
        if target != 'programs_only':
            # Save workspace layout to file.
            layout.save(workspace_id, numeric, directory, swallow_criteria)

        if target != 'layout_only':
            # Save running programs to file.
            programs.save(workspace_id, numeric, directory)


def restore_workspace(i3, saved_layout, saved_programs, target):
    if saved_layout == None:
        return

    # Get layout name from file.
    if 'name' in saved_layout:
        workspace_name = saved_layout['name']
    else:
        util.eprint('Workspace name not found.')
        sys.exit(1)

    i3.command(f'workspace --no-auto-back-and-forth {workspace_name}')

    if target != 'programs_only':
        # Load workspace layout.
        layout.restore(workspace_name, saved_layout)

    if target != 'layout_only':
        # Restore programs.
        programs.restore(workspace_name, saved_programs)


@main.command('restore')
@click.option('--workspace', '-w',
              is_flag=True,
              help='Restore workspace(s).')
@click.option('--numeric', '-n',
              is_flag=True,
              help='Select workspace(s) by number instead of name.')
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
@click.argument('workspaces', nargs=-1)
def restore_workspaces(workspace, numeric, directory, profile, target,
        workspaces):
    """
    Restore i3 workspace(s) layout(s) and programs.

    Use cases:

    i3-resurrect restore [--workspace] WORKSPACES

    i3-resurrect restore WORKSPACE_LAYOUT TARGET_WORKSPACE

    WORKSPACES are the workspace(s) to restore.
    [default: current workspace]

    WORKSPACE_LAYOUT is the workspace file to load.
    TARGET_WORKSPACE is the target workspace
    [default: current workspace]
    """
    i3 = i3ipc.Connection()

    focused_workspace = i3.get_tree().find_focused().workspace().name

    if not workspaces:
        if numeric:
            workspaces = (str(i3.get_tree().find_focused().workspace().num), )
        else:
            workspaces = (focused_workspace, )

    directory = util.resolve_directory(directory, profile)

    if workspace:
        for workspace_id in workspaces:
            if numeric and not workspace_id.isdigit():
                util.eprint('Invalid workspace number.')
                sys.exit(1)
            saved_layout = layout.read(workspace_id, directory)
            saved_programs = programs.read(workspace_id, directory)
            restore_workspace(i3, saved_layout, saved_programs, target)
    else:
        workspace_layout = workspaces[0]
        # Get layout from file.
        saved_layout = layout.read(workspace_layout, directory)
        saved_programs = programs.read(workspace_layout, directory)

        for target_workspace in workspaces[1:]:
            # Make eventualy possible to restore layout in multiples workspaces
            if numeric:
                if not workspace_layout.isdigit():
                    util.eprint('Invalid workspace number.')
                    sys.exit(1)

                if not target_workspace:
                    target_workspace = str(i3.get_tree().find_focused().workspace().num)
                elif not target_workspace.isdigit():
                    util.eprint('Invalid workspace number.')
                    sys.exit(1)
            else:
                if not target_workspace:
                    target_workspace = i3.get_tree().find_focused().workspace().name

            if numeric:
                i3.command(f'workspace --no-auto-back-and-forth number \
                        {target_workspace}')
            else:
                i3.command(f'workspace --no-auto-back-and-forth {target_workspace}')

            if target != 'programs_only':
                # Load workspace layout.
                layout.restore(target_workspace, saved_layout,
                        saved_programs)

            if target != 'layout_only':
                # Restore programs.
                programs.restore(target_workspace, saved_programs)


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


def delete(layout_file, programs_file, target):
    if target != 'programs_only':
        # Delete programs file.
        programs_file.unlink()

    if target != 'layout_only':
        # Delete layout file.
        layout_file.unlink()


@main.command('rm')
@click.option('--workspace', '-w',
              is_flag=True,
              help='Delete workspace(s) files.')
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
@click.argument('workspaces', nargs=-1)
def remove(workspace, directory, profile, target, workspaces):
    """
    Remove saved worspace(s) layout(s), or programs.
    """
    directory = util.resolve_directory(directory, profile)

    if workspace:
        for workspace_id in workspaces:
            workspace_id = util.filename_filter(workspace_id)
            programs_filename = f'workspace_{workspace_id}_programs.json'
            layout_filename = f'workspace_{workspace_id}_layout.json'
            programs_file = Path(directory) / programs_filename
            layout_file = Path(directory) / layout_filename
            delete(layout_file, programs_file, target)
    else:
        util.eprint('--workspace must be specified.')
        sys.exit(1)


if __name__ == '__main__':
    main()
