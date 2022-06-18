"""
Lazy-initialized singleton for config.
"""
import json
from pathlib import Path


def create_default():
    """
    Creates the default config file.
    """
    global _config
    global _config_dir
    global _config_file

    _config = {
        'directory': '~/.i3/i3-resurrect/',
        'window_command_mappings': [
            {
                'class': 'Gnome-terminal',
                'command': 'gnome-terminal',
            },
        ],
        'window_swallow_criteria': {},
        'terminals': ['Gnome-terminal', 'Alacritty'],
    }

    # Make config directory if it doesn't exist.
    Path(_config_dir).mkdir(parents=True, exist_ok=True)

    # Write default config.
    with _config_file.open('w') as f:
        f.write(json.dumps(_config, indent=2))


def get(key, default):
    """
    Gets a config value.
    """
    global _config

    # Load config if it hasn't already been loaded.
    if _config is None:
        try:
            _config = json.loads(_config_file.read_text())
        except json.decoder.JSONDecodeError as e:
            print(f'Error in config file: "{str(e)}"')
            exit(1)
        except PermissionError as e:
            print(f'Could not read config file: {str(e)}')
            exit(1)
        except FileNotFoundError:
            # Create default config if no config exists.
            create_default()

    return _config.get(key, default)


_config = None

_config_dir = Path('~/.config/i3-resurrect/').expanduser()
_config_file = _config_dir / 'config.json'

if not _config_file.is_file():
    # Create default config if no config exists.
    create_default()
