import re


def build_tree(con, swallow_criteria):
    """
    Recursive function to build a restorable window layout tree using basic
    Python data structures.
    """
    tree = []

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
            'focused',
            'fullscreen_mode',
            'geometry',
            'last_split_layout',
            'layout',
            'name',
            'orientation',
            'percent',
            'scratchpad_state',
            'sticky',
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
            for criterion in swallow_criteria:
                if criterion in node['window_properties']:
                    # Escape special characters in swallow criteria.
                    escaped = re.escape(node['window_properties'][criterion])
                    # Regex formatting.
                    value = f'^{escaped}$'
                    container['swallows'][0][criterion] = value
        container['nodes'] = build_tree(node, swallow_criteria)

        tree.append(container)

    return tree
