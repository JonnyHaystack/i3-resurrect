import json
import re
import shlex
import subprocess

from i3_resurrect.types import WindowSwallowMapping

from . import config

# The tree node attributes that we want to save.
REQUIRED_ATTRIBUTES = [
    "border",
    "current_border_width",
    "floating",
    "fullscreen_mode",
    "geometry",
    "layout",
    "marks",
    "name",
    "orientation",
    "percent",
    "scratchpad_state",
    "sticky",
    "type",
    "workspace_layout",
]


def process_node(original: dict, swallow: list[str]):
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

    # Keep output attribute for workspace nodes.
    if "type" in original and original["type"] == "workspace":
        processed["output"] = original["output"]

    # Keep rect attribute for floating nodes.
    if "type" in original and original["type"] == "floating_con":
        processed["rect"] = original["rect"]

    # Set swallow criteria if the node is a window.
    if "window_properties" in original:
        processed["swallows"] = get_window_swallow_values(
            original["window_properties"], swallow
        )

    # Recurse over child nodes (normal and floating).
    for node_type in ["nodes", "floating_nodes"]:
        if node_type in original and original[node_type] != []:
            processed[node_type] = []
            for child in original[node_type]:
                # Step case.
                processed[node_type].append(process_node(child, swallow))

    return processed


def get_window_swallow_values(
    window_properties: dict, swallow: list[str]
) -> list[dict[str, str]]:
    """
    Get swallow criteria for window
    """
    # Look for matching swallow criteria mapping from config, or fall back to param from CLI if not
    # found.
    swallow_mapping = WindowSwallowMapping.find_best_matching_rule(
        window_properties, config.get_window_swallow_mappings()
    ) or WindowSwallowMapping({}, swallow)

    return [swallow_mapping.get_swallow_values(window_properties)]


def get_workspace_tree(workspace: str, numeric: bool):
    """
    Get full workspace layout tree from i3.
    """
    root = json.loads(subprocess.check_output(shlex.split("i3-msg -t get_tree")))
    for output in root["nodes"]:
        for container in output["nodes"]:
            if container["type"] != "con":
                pass
            for ws in container["nodes"]:
                # Select workspace and trigger name and num field
                if numeric:
                    if (
                        workspace.isdigit()
                        and "num" in ws
                        and ws["num"] == int(workspace)
                    ):
                        return ws
                elif ws["name"] == workspace:
                    return ws
    return {}


def get_leaves(container: dict | None):
    """
    Recursive generator for retrieving a list of a container's leaf nodes.

    Args:
        container: The container to traverse.
    """
    # Base cases.
    if container is None:
        return

    nodes = container.get("nodes", []) + container.get("floating_nodes", [])

    # Step case.
    for node in nodes:
        if "window_properties" in node:
            yield node
        yield from get_leaves(node)
