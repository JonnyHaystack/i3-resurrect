"""
Lazy-initialized singleton for config.
"""

import json
from pathlib import Path
from typing import Any

from i3_resurrect.types import WindowCommandMapping, WindowSwallowMapping

from . import util


def create_default():
    """
    Creates the default config file.
    """
    global _config
    global _config_dir
    global _config_file

    _config = {
        "directory": "~/.i3/i3-resurrect/",
        "window_command_mappings": [
            {
                "filters": {
                    "class": "^Gnome-terminal$",
                },
                "command": "gnome-terminal",
            },
        ],
        "window_swallow_criteria": [
            {
                "filters": {
                    "class": "^PCSX2$",
                    "title": "^Kingdom Hearts [0-9]*FPS - PCSX2$",
                },
                "swallows": {
                    "class": "",
                    "instance": "",
                    "title": "^Kingdom Hearts [0-9]*FPS - PCSX2$",
                },
            },
        ],
        "terminals": ["Gnome-terminal", "Alacritty"],
    }

    # Make config directory if it doesn't exist.
    Path(_config_dir).mkdir(parents=True, exist_ok=True)

    # Write default config.
    with _config_file.open("w") as f:
        f.write(json.dumps(_config, indent=2))


def get(key: str, default: Any) -> Any:
    """
    Gets a config value.
    """
    global _config

    # Load config if it hasn't already been loaded.
    if _config is None:
        try:
            _config = json.loads(_config_file.read_text())
        except json.decoder.JSONDecodeError as e:
            util.eprint(f'Error in config file: "{str(e)}"')
            exit(1)
        except PermissionError as e:
            util.eprint(f"Could not read config file: {str(e)}")
            exit(1)
        except FileNotFoundError:
            # Create default config if no config exists.
            create_default()
        except Exception as e:
            util.eprint(f"Unknown error")

    if _config is not None:
        return _config.get(key, default)

    return None


def get_window_command_mappings() -> list[WindowCommandMapping]:
    return [
        WindowCommandMapping(
            command_mapping["filters"], command_mapping.get("command", None)
        )
        for command_mapping in get("window_command_mappings", [])
    ]


def get_window_swallow_mappings() -> list[WindowSwallowMapping]:
    return [
        WindowSwallowMapping(
            swallow_mapping.get("filters", {}), swallow_mapping.get("swallows", [])
        )
        for swallow_mapping in get("window_swallow_criteria", [])
    ]


_config: dict | None = None

_config_dir = Path("~/.config/i3-resurrect/").expanduser()
_config_file = _config_dir / "config.json"

if not _config_file.is_file():
    # Create default config if no config exists.
    create_default()
