import i3ipc
import json
import re
import shlex
import subprocess
import sys

from . import config

# The tree node attributes that we want to save.
REQUIRED_ATTRIBUTES = [
    'border',
    'current_border_width',
    'floating',
    'fullscreen_mode',
    'geometry',
    'layout',
    'marks',
    'name',
    'orientation',
    'percent',
    'scratchpad_state',
    'sticky',
    'type',
    'workspace_layout',
]


def eprint(*args, **kwargs):
    """
    Function for printing to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def build_layout(tree, swallow):
    """
    Builds a restorable layout tree with basic Python data structures which are
    JSON serialisable.
    """
    processed = process_node(tree, swallow)
    return processed


def process_node(original, swallow):
    """
    Recursive function which traverses a layout tree and builds a new tree from
    it which can be restored using append_layout and only contains attributes
    necessary for accurately restoring the layout.
    """
    processed = {}

    # Base case.
    if original is None or original == {}:
        return processed

    # Set attributes.
    for attribute in REQUIRED_ATTRIBUTES:
        if attribute in original:
            processed[attribute] = original[attribute]

    # Keep rect attribute for floating nodes.
    if 'type' in original and original['type'] == 'floating_con':
        processed['rect'] = original['rect']

    # Set swallow criteria if the node is a window.
    if 'window_properties' in original:
        processed['swallows'] = [{}]
        # Local variable for swallow criteria.
        swallow_criteria = swallow
        # Get swallow criteria from config.
        window_swallow_mappings = config.get('window_swallow_criteria', {})
        window_class = original['window_properties'].get('class', '')
        # Swallow criteria from config override the command line parameters
        # if present.
        if window_class in window_swallow_mappings:
            swallow_criteria = window_swallow_mappings[window_class]
        for criterion in swallow_criteria:
            if criterion in original['window_properties']:
                # Escape special characters in swallow criteria.
                escaped = re.escape(original['window_properties'][criterion])
                # Regex formatting.
                value = f'^{escaped}$'
                processed['swallows'][0][criterion] = value

    # Recurse over child nodes (normal and floating).
    for node_type in ['nodes', 'floating_nodes']:
        if node_type in original and original[node_type] != []:
            processed[node_type] = []
            for child in original[node_type]:
                # Step case.
                processed[node_type].append(process_node(child, swallow))

    return processed


def get_workspace_tree(workspace):
    """
    Get full workspace layout tree from i3.
    """
    root = json.loads(
        subprocess.check_output(shlex.split('i3-msg -t get_tree'))
    )
    for output in root['nodes']:
        for container in output['nodes']:
            if container['type'] != 'con':
                pass
            for ws in container['nodes']:
                if ws['name'] == workspace:
                    return ws
    return {}


def get_leaves(container):
    """
    Recursive generator for retrieving a list of a container's leaf nodes.

    Args:
        container: The container to traverse.
    """
    # Base cases.
    if container is None:
        return

    nodes = container.get('nodes', []) + container.get('floating_nodes', [])

    # Step case.
    for node in nodes:
        if 'window_properties' in node:
            yield node
        yield from get_leaves(node)


def windows_in_workspace(workspace):
    """
    Generator to iterate over windows in a workspace.

    Args:
        workspace: The name of the workspace whose windows to iterate over.
    """
    ws = get_workspace_tree(workspace)
    for con in get_leaves(ws):
        pid = get_window_pid(con)
        yield (con, pid)


def is_placeholder(container):
    """
    Check if a container is a placeholder window.

    Args:
        container: The container to check.
    """
    return container['swallows'] not in [[], None]


def get_window_pid(con):
    """
    Get window PID using xprop.

    Args:
        con: The window container node whose PID to look up.
    """
    window_id = con['window']
    if window_id in [[], None]:
        return 0

    xprop_output = subprocess.check_output(
        shlex.split(f'xprop _NET_WM_PID -id {window_id}')
    ).decode('utf-8').split(' ')

    pid = int(xprop_output[len(xprop_output) - 1])

    return pid


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
