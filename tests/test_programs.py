from i3_resurrect import config
from i3_resurrect import programs


def test_get_window_command(monkeypatch):
    # Monkeypatch config.
    monkeypatch.setattr(
        config,
        '_config',
        {
            'window_command_mappings': [
                {
                    'class': 'Program1'
                },
                {
                    'class': 'Program1',
                    'title': 'Main window title',
                    'command': 'run_program1'
                },
                {
                    'title': 'Some arbitrary title'
                }
            ],
        },
    )

    # Test class + title mapping.
    program1_main = {
        'class': 'Program1',
        'title': 'Main window title'
    }
    assert programs.get_window_command(program1_main, ['program1']) == [
        'run_program1',
    ]

    # Test class only mapping.
    program1_secondary = {
        'class': 'Program1',
        'title': 'Blah random title'
    }
    assert programs.get_window_command(program1_secondary, ['program1']) == []

    # Test with separate program window with matching title but not class.
    program2_main = {
        'class': 'Program2',
        'title': 'Main window title',
    }
    assert programs.get_window_command(program2_main, ['program2']) == ['program2']

    # Test that title only mapping matches any window with matching title.
    program3 = {
        'class': 'Program3',
        'title': 'Some arbitrary title',
    }
    assert programs.get_window_command(program3, ['program3']) == []
