import re

from . import config


def build_tree(con, swallow):
    """
    Recursive function to build a restorable window layout tree using basic
    Python data structures.
    """
    tree = []

    if con is None:
        return tree

    nodes = con['nodes']

    # Base case.
    if nodes == []:
        return tree

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
