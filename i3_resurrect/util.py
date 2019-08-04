import json
import re
import shlex
import subprocess
import sys

import i3ipc
from wmctrl import Window

from . import config


def eprint(*args, **kwargs):
    """
    Function for printing to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def build_tree(con, swallow):
    """
    Recursive function to build a restorable window layout tree using basic
    Python data structures.
    """
    tree = []

    # Base cases.
    if con is None or 'nodes' not in con or con['nodes'] == []:
        return tree

    nodes = con['nodes']

    # Step case.
    for node in nodes:
        container = {}
        attributes = [
            'border',
            'current_border_width',
            'floating',
            'fullscreen_mode',
            'geometry',
            'layout',
            'name',
            'orientation',
            'percent',
            'scratchpad_state',
            'type',
            'workspace_layout',
        ]

        # Set attributes.
        for attribute in attributes:
            if attribute in node:
                container[attribute] = node[attribute]

        # Set swallow criteria.
        if 'window_properties' in node:
            container['swallows'] = [{}]
            # Local variable for swallow criteria.
            swallow_criteria = swallow
            # Get swallow criteria from config.
            window_swallow_mappings = config.get('window_swallow_criteria', {})
            window_class = node['window_properties']['class']
            # Swallow criteria from config override the command line parameters
            # if present.
            if window_class in window_swallow_mappings:
                swallow_criteria = window_swallow_mappings[window_class]
            for criterion in swallow_criteria:
                if criterion in node['window_properties']:
                    # Escape special characters in swallow criteria.
                    escaped = re.escape(node['window_properties'][criterion])
                    # Regex formatting.
                    value = f'^{escaped}$'
                    container['swallows'][0][criterion] = value
        container['nodes'] = build_tree(node, swallow)

        tree.append(container)

    return tree


def get_workspace_tree(workspace):
    """
    Get full workspace layout tree from i3.
    """
    i3 = i3ipc.Connection()

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
    Recursive generator for iterating over windows in a container.

    Args:
        container: The container to traverse.
    """
    # Base cases.
    if (container is None
            or 'nodes' not in container
            or container['nodes'] == []):
        return

    nodes = container['nodes']

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


def get_window_command(window_properties, cmdline):
    """
    Gets a window command.

    This function starts with the process's cmdline, then loops through the
    window mappings and scores each matching rule. The command mapping with the
    highest score is then returned.
    """
    window_command_mappings = config.get('window_command_mappings', [])
    command = cmdline

    # If window command mappings is a dictionary in the config file, use the
    # old way.
    # TODO: Remove in 2.0.0
    if isinstance(window_command_mappings, dict):
        window_class = window_properties['class']
        if window_class in window_command_mappings:
            command = window_command_mappings[window_class]
        return command

    # Find the mapping that gets the highest score.
    current_score = 0
    for rule in window_command_mappings:
        # Calculate score.
        score = calc_rule_match_score(rule, window_properties)

        if score > current_score:
            current_score = score
            if 'command' not in rule:
                command = []
            elif isinstance(rule['command'], list):
                command = rule['command']
            else:
                command = shlex.split(rule['command'])
    return command


def calc_rule_match_score(rule, window_properties):
    """
    Score window command mapping match based on which criteria match.

    Scoring is done based on which criteria are considered "more specific".
    """
    # Window properties and value to add to score when match is found.
    criteria = {
        'window_role': 1,
        'class': 2,
        'instance': 3,
        'title': 10,
    }

    score = 0
    for criterion in criteria:
        if criterion in rule:
            # Score is zero if there are any non-matching criteria.
            if rule[criterion] != window_properties[criterion]:
                return 0
            score += criteria[criterion]
    return score


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
