import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import i3ipc

from . import programs
from . import treeutils
from . import util


def list(i3, numeric):
    # List all active workspaces
    workspaces_data = i3.get_workspaces()
    workspaces = []
    for n, workspace_data in enumerate(workspaces_data):
        # Get all active workspaces from session
        if numeric:
            workspaces.append(str(workspace_data.num))
        else:
            workspaces.append(workspace_data.name)
    return workspaces

def save(workspace, numeric, directory, swallow_criteria):
    """
    Save an i3 workspace layout to a file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f'workspace_{workspace_id}_layout.json'
    layout_file = Path(directory) / filename

    workspace_tree = treeutils.get_workspace_tree(workspace, numeric)

    with layout_file.open('w') as f:
        # Build new workspace tree suitable for restoring and write it to a
        # file.
        f.write(
            json.dumps(
                build_layout(workspace_tree, swallow_criteria),
                indent=2,
            )
        )


def read(workspace, directory):
    """
    Read saved layout file.
    """
    workspace_id = util.filename_filter(workspace)
    filename = f'workspace_{workspace_id}_layout.json'
    layout_file = Path(directory) / filename

    layout = None
    try:
        layout = json.loads(layout_file.read_text())
    except FileNotFoundError:
        util.eprint('Could not find saved layout for workspace '
                        f'"{workspace}"')
    return layout


def remove_windows_from_workspace(normal_windows, kill=False):
    for window in normal_windows:
        #  window and program instance that don't match to saved list have to be killed
        if kill:
            xdo_kill_window(window['window'])
        else:
            xdo_map_window(window['window'])
            xdo_focus_window(window['window'])
            i3.command(f'move scratchpad') 


def clean_workspace(layout, saved_programs, normal_windows, target, kill=False):
    """"
    Move windows that don't match saved programs in layout to scatchpad or kill it.
    """
    i3 = i3ipc.Connection()
    preserved_windows = []
    saved_windows = treeutils.get_leaves(layout)
    for saved_program in saved_programs:
        current_score = 0
        best_match = None
        # Get swallow criterias of saved program to restore
        rule = saved_program['window_properties']

        for window in normal_windows:
            window_properties = window['window_properties']
            if rule['class'] == window_properties['class']:
                # The window is part of the saved layout
                # calculate match score of window
                score = programs.calc_rule_match_score(rule, window_properties)
                if score > current_score:
                    current_score = score
                    # Bestmatched window
                    best_match = window

        if current_score != 0:
            # saved window already open
            preserved_windows.append(best_match)
            normal_windows.remove(best_match)

    remove_windows_from_workspace(normal_windows, target)

    return preserved_windows


def restore(workspace_name, layout, saved_programs, target, kill=False):
    """
    Restore an i3 workspace layout.
    """
    normal_windows = []
    placeholder_windows = []

    # Get ids of all placeholder or normal windows in workspace.
    ws = treeutils.get_workspace_tree(workspace_name, False)
    windows = treeutils.get_leaves(ws)

    for window in windows:
        if is_placeholder(window):
            # If window is a placeholder, add it to list of placeholder
            # windows.
            placeholder_windows.append(window)
        else:
            # Otherwise, add it to the list of regular windows.
            normal_windows.append(window)

    if target == 'clean':
        preserved_windows = clean_workspace(layout, saved_programs, normal_windows, target, kill)
    elif target == 'reload':
        remove_windows_from_workspace(normal_windows, target, kill)
    else:
        preserved_windows = normal_windows

    # Remove any remaining placeholder windows in workspace so that we don't
    # have duplicates.
    for window in placeholder_windows:
        xdo_kill_window(window['window'])

    if layout == {}:
        return

    # Unmap all non-placeholder windows in workspace.
    for window in preserved_windows:
        xdo_unmap_window(window['window'])

    try:
        i3 = i3ipc.Connection()

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
    except Exception as e:
        util.eprint('Error occurred restoring workspace layout. Note that if '
                    'the layout was saved by a version prior to 1.4.0 it must '
                    'be recreated.')
        util.eprint(str(e))
    finally:
        # Map all unmapped windows. We use finally because we don't want the
        # user to lose their windows no matter what.
        for window in preserved_windows:
            xdo_map_window(window['window'])


def build_layout(tree, swallow):
    """
    Builds a restorable layout tree with basic Python data structures which are
    JSON serialisable.
    """
    processed = treeutils.process_node(tree, swallow)
    return processed


def is_placeholder(container):
    """
    Check if a container is a placeholder window.

    Args:
        container: The container to check.
    """
    return container['swallows'] not in [[], None]


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
