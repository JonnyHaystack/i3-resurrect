from i3_resurrect import treeutils


def test_windows_in_container():
    workspace_tree = {
        'id': 93860418230528,
        'type': 'workspace',
        'orientation': 'horizontal',
        'scratchpad_state': 'none',
        'percent': 0.5,
        'urgent': False,
        'focused': False,
        'output': 'HDMI-1-1',
        'layout': 'splith',
        'workspace_layout': 'default',
        'last_split_layout': 'splith',
        'border': 'normal',
        'current_border_width': -1,
        'rect': {'x': 1366, 'y': 0, 'width': 1920, 'height': 1048},
        'deco_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
        'window_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
        'geometry': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
        'name': '2',
        'num': 2,
        'gaps': {'inner': 0, 'outer': 0},
        'window': None,
        'nodes': [
            {
                'id': 93860418434672,
                'type': 'con',
                'orientation': 'vertical',
                'scratchpad_state': 'none',
                'percent': 0.5,
                'urgent': False,
                'focused': False,
                'output': 'HDMI-1-1',
                'layout': 'splitv',
                'workspace_layout': 'default',
                'last_split_layout': 'splitv',
                'border': 'normal',
                'current_border_width': -1,
                'rect': {'x': 1366, 'y': 0, 'width': 960, 'height': 1048},
                'deco_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'window_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'geometry': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'name': None,
                'window': None,
                'nodes': [
                    {
                        'id': 93860418452384,
                        'type': 'con',
                        'orientation': 'none',
                        'scratchpad_state': 'none',
                        'percent': 0.5,
                        'urgent': False,
                        'focused': False,
                        'output': 'HDMI-1-1',
                        'layout': 'splith',
                        'workspace_layout': 'default',
                        'last_split_layout': 'splith',
                        'border': 'pixel',
                        'current_border_width': 2,
                        'rect': {
                            'x': 1376,
                            'y': 10,
                            'width': 945,
                            'height': 509
                        },
                        'deco_rect': {
                            'x': 0,
                            'y': 0,
                            'width': 0,
                            'height': 0
                        },
                        'window_rect': {
                            'x': 2,
                            'y': 2,
                            'width': 941,
                            'height': 505
                        },
                        'geometry': {
                            'x': 0,
                            'y': 0,
                            'width': 724,
                            'height': 412
                        },
                        'name': '~/Projects',
                        'title_format': ' %title ',
                        'window': 52428803,
                        'window_properties': {
                            'class': 'Alacritty',
                            'instance': 'Alacritty',
                            'title': '~/Projects',
                            'transient_for': None
                        },
                        'nodes': [

                        ],
                        'floating_nodes':[

                        ],
                        'focus':[

                        ],
                        'fullscreen_mode':0,
                        'sticky':False,
                        'floating':'auto_off',
                        'swallows':[

                        ]
                    },
                    {
                        'id': 93860418285248,
                        'type': 'con',
                        'orientation': 'none',
                        'scratchpad_state': 'none',
                        'percent': 0.5,
                        'urgent': False,
                        'focused': False,
                        'output': 'HDMI-1-1',
                        'layout': 'splith',
                        'workspace_layout': 'default',
                        'last_split_layout': 'splith',
                        'border': 'pixel',
                        'current_border_width': 2,
                        'rect': {
                            'x': 1376,
                            'y': 529,
                            'width': 945,
                            'height': 509
                        },
                        'deco_rect': {
                            'x': 0,
                            'y': 0,
                            'width': 0,
                            'height': 0
                        },
                        'window_rect': {
                            'x': 2,
                            'y': 2,
                            'width': 941,
                            'height': 505
                        },
                        'geometry': {
                            'x': 0,
                            'y': 0,
                            'width': 724,
                            'height': 412
                        },
                        'name': '~/.dotfiles',
                        'title_format': ' %title ',
                        'window': 6291459,
                        'window_properties': {
                            'class': 'Alacritty',
                            'instance': 'Alacritty',
                            'title': '~/.dotfiles',
                            'transient_for': None
                        },
                        'nodes': [

                        ],
                        'floating_nodes':[

                        ],
                        'focus':[

                        ],
                        'fullscreen_mode':0,
                        'sticky':False,
                        'floating':'auto_off',
                        'swallows':[]
                    }
                ],
                'floating_nodes':[],
                'focus':[93860418285248, 93860418452384],
                'fullscreen_mode':0,
                'sticky':False,
                'floating':'auto_off',
                'swallows':[

                ]
            },
            {
                'id': 93860418798800,
                'type': 'con',
                'orientation': 'vertical',
                'scratchpad_state': 'none',
                'percent': 0.5,
                'urgent': False,
                'focused': False,
                'output': 'HDMI-1-1',
                'layout': 'splitv',
                'workspace_layout': 'default',
                'last_split_layout': 'splitv',
                'border': 'normal',
                'current_border_width': -1,
                'rect': {'x': 2326, 'y': 0, 'width': 960, 'height': 1048},
                'deco_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'window_rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'geometry': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'name': None,
                'window': None,
                'nodes': [
                    {
                        'id': 93860418425760,
                        'type': 'con',
                        'orientation': 'none',
                        'scratchpad_state': 'none',
                        'percent': 0.5,
                        'urgent': False,
                        'focused': False,
                        'output': 'HDMI-1-1',
                        'layout': 'splith',
                        'workspace_layout': 'default',
                        'last_split_layout': 'splith',
                        'border': 'pixel',
                        'current_border_width': 2,
                        'rect': {
                            'x': 2331,
                            'y': 10,
                            'width': 945,
                            'height': 509
                        },
                        'deco_rect': {
                            'x': 0,
                            'y': 0,
                            'width': 0,
                            'height': 0
                        },
                        'window_rect': {
                            'x': 2,
                            'y': 2,
                            'width': 941,
                            'height': 505
                        },
                        'geometry': {
                            'x': 0,
                            'y': 0,
                            'width': 1366,
                            'height': 736
                        },
                        'name': 'System Monitor',
                        'title_format': ' %title ',
                        'window': 54525962,
                        'window_properties': {
                            'class': 'ksysguard',
                            'instance': 'ksysguard',
                            'window_role': 'MainWindow#1',
                            'title': 'System Monitor',
                            'transient_for': None
                        },
                        'nodes': [

                        ],
                        'floating_nodes':[

                        ],
                        'focus':[

                        ],
                        'fullscreen_mode':0,
                        'sticky':False,
                        'floating':'auto_off',
                        'swallows':[

                        ]
                    },
                    {
                        'id': 93860418808208,
                        'type': 'con',
                        'orientation': 'none',
                        'scratchpad_state': 'none',
                        'percent': 0.5,
                        'urgent': False,
                        'focused': False,
                        'output': 'HDMI-1-1',
                        'layout': 'splith',
                        'workspace_layout': 'default',
                        'last_split_layout': 'splith',
                        'border': 'pixel',
                        'current_border_width': 2,
                        'rect': {
                            'x': 2331,
                            'y': 529,
                            'width': 945,
                            'height': 509
                        },
                        'deco_rect': {
                            'x': 0,
                            'y': 0,
                            'width': 0,
                            'height': 0
                        },
                        'window_rect': {
                            'x': 2,
                            'y': 2,
                            'width': 941,
                            'height': 505
                        },
                        'geometry': {
                            'x': 0,
                            'y': 0,
                            'width': 724,
                            'height': 412
                        },
                        'name': '~/.dotfiles',
                        'title_format': ' %title ',
                        'window': 50331651,
                        'window_properties': {
                            'class': 'Alacritty',
                            'instance': 'Alacritty',
                            'title': '~/.dotfiles',
                            'transient_for': None
                        },
                        'nodes': [

                        ],
                        'floating_nodes':[

                        ],
                        'focus':[

                        ],
                        'fullscreen_mode':0,
                        'sticky':False,
                        'floating':'auto_off',
                        'swallows':[

                        ]
                    }
                ],
                'floating_nodes':[],
                'focus':[93860418425760, 93860418808208],
                'fullscreen_mode':0,
                'sticky':False,
                'floating':'auto_off',
                'swallows':[]
            }
        ],
        'floating_nodes': [],
        'focus': [93860418434672, 93860418798800],
        'fullscreen_mode': 0,
        'sticky': False,
        'floating': 'auto_off',
        'swallows': []
    }
    windows = treeutils.get_leaves(workspace_tree)
    assert windows is not None
