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
                    'title': 'Some arbitrary title',
                },
                {
                    'class': 'Program4',
                    'command': 'run_program4 {1}'
                },
                {
                    'class': 'Program6',
                    'command': 'chrome {1}'
                },
                {
                    'class': 'Program7',
                    'command': ['/opt/Pulse SMS/pulse-sms'],
                }
            ],
        },
    )

    # Test class + title mapping.
    program1_main = {
        'class': 'Program1',
        'title': 'Main window title',
    }
    assert programs.get_window_command(
        program1_main,
        ['program1'],
        '/usr/bin/program1',
    ) == [
        'run_program1',
    ]

    # Test class only mapping.
    program1_secondary = {
        'class': 'Program1',
        'title': 'Blah random title',
    }
    assert programs.get_window_command(
        program1_secondary,
        ['program1'],
        '/usr/bin/program1',
    ) == []

    # Test with separate program window with matching title but not class.
    program2_main = {
        'class': 'Program2',
        'title': 'Main window title',
    }
    assert programs.get_window_command(
        program2_main,
        ['program2'],
        '/usr/bin/program2'
    ) == ['/usr/bin/program2']

    # Test that title only mapping matches any window with matching title.
    program3 = {
        'class': 'Program3',
        'title': 'Some arbitrary title',
    }
    assert programs.get_window_command(
        program3,
        ['program3'],
        '/usr/bin/program3',
    ) == []

    # Test cmdline arg interpolation.
    program4 = {
        'class': 'Program4',
        'title': 'Blah random title',
    }
    assert programs.get_window_command(
        program4,
        ['/opt/Program4/program4', '/tmp/test.txt'],
        '/opt/Program4/program4',
    ) == ['run_program4', '/tmp/test.txt']

    # Test splitting of single arg command.
    program5 = {
        'class': 'Program5',
        'title': 'program 5 title',
    }
    assert programs.get_window_command(
        program5,
        ['/opt/google/chrome/chrome --profile-directory=Default '
         '--app=http://instacalc.com --user-data-dir=.config'],
        '/opt/google/chrome/chrome',
    ) == [
        '/opt/google/chrome/chrome',
        '--profile-directory=Default',
        '--app=http://instacalc.com',
        '--user-data-dir=.config',
    ]

    # Test splitting of single arg command when used with mapping and cmdline
    # interpolation.
    program6 = {
        'class': 'Program6',
    }
    assert programs.get_window_command(
        program6,
        ['/opt/google/chrome/chrome --profile-directory=Default '
         '--app=http://instacalc.com --user-data-dir=.config'],
        '/opt/google/chrome/chrome',
    ) == [
        'chrome',
        '--profile-directory=Default',
    ]

    # Test single arg command with space in executable path.
    program7 = {
        'class': 'Program7',
    }
    assert programs.get_window_command(
        program7,
        ['/opt/Pulse SMS/pulse-sms'],
        None
    ) == ['/opt/Pulse SMS/pulse-sms']

    # Test single arg command with space in executable path with exe available.
    program8 = {
        'class': 'Program8',
    }
    assert programs.get_window_command(
        program8,
        ['/opt/Pulse SMS/pulse-sms'],
        '/opt/Pulse SMS/pulse-sms',
    ) == ['/opt/Pulse SMS/pulse-sms', 'SMS/pulse-sms']

    # Test cmdline with empty args is processed correctly.
    assert programs.get_window_command(
        program5,
        ['/opt/google/chrome/chrome --profile-directory=Default '
         '--app=http://instacalc.com --user-data-dir=.config', '', '', '', ''],
        '/opt/google/chrome/chrome',
    ) == [
        '/opt/google/chrome/chrome',
        '--profile-directory=Default',
        '--app=http://instacalc.com',
        '--user-data-dir=.config',
    ]
