# i3-resurrect

A simple but flexible solution to saving and restoring i3 workspaces

## Table of Contents

* [Introduction](#introduction)
* [Background](#background)
* [Getting Started](#getting-started)
   * [Requirements](#requirements)
   * [Installation](#installation)
   * [Usage](#usage)
   * [Configuration](#configuration)
* [Contributing](#contributing)
* [Contributors](#contributors)
* [License](#license)

## Introduction

i3-resurrect is a program which can save and restore the layout and running
programs in your i3 workspaces.

Layouts are saved by using i3ipc to take necessary information from the
workspace tree and write it to a JSON file.

Programs are saved by looking up each process in the workspace and writing their
`cmdline` (the command used to launch the program) and `cwd` (current working
directory) to a JSON file.

When restoring programs, Python's subprocess module is used to launch the saved
programs with the correct working directory.

When restoring layouts, i3's built-in ability layout restoring functionality is
used. This creates placeholder windows where each one will "swallow" any window
that appears and matches specified criteria (window class, instance, title etc).

xdotool is used to make i3 see existing windows as new windows.
This is necessary for matching by window title because the title must match
when the window first appears and programs usually only update the title after
the window is created
(see [here](https://i3wm.org/docs/layout-saving.html#_placeholders_using_window_title_matches_don_8217_t_swallow_the_window)
for more details).

## Background

This project originated as a mixture of hacked together Python and bash scripts
that I wrote in order to be able to quickly save and load workspaces on the fly.

I hate having to reboot my computer because it disrupts everything I have open
(which tends to be a lot).

To cope with this problem, I try to make it as easy as possible for myself to get everything
back to its pre-reboot state.

I quickly found out about the `i3-save-tree` utility and i3's `append-layout` command, but these
weren't much use to me on their own, as you are expected to customise a layout manually after
saving it and relaunch all your programs manually when you restore the layout.

My solution was to create a script that would extract just the bits from i3-save-tree that are
needed, and use the [i3ipc](https://github.com/acrisci/i3ipc-python),
[wmctrl](https://bitbucket.org/antocuni/wmctrl), and
[psutil](https://github.com/giampaolo/psutil) Python libraries to obtain the commands necessary
to launch the programs in a saved workspace.

Since I decided to release this publicly, I have improved the standard of the code a great deal
and gotten rid of the hacky bash parts.
The code is all Python now, and i3-save-tree is no longer needed as I have
reimplemented it in Python.

## Getting Started

### Requirements

- Python 3
- i3
- xdotool

### Installation

#### From the AUR using yay (recommended for Arch Linux users)
```
yay -S i3-resurrect-git
```

#### From PyPI (recommended for everyone else)

```
pip3 install --user --upgrade i3-resurrect
```

Make sure ~/.local/bin is in your PATH environment variable.

#### Manual

Obtain source code
```
git clone git@github.com:JonnyHaystack/i3-resurrect.git
```

Install locally using pip
```
cd i3-resurrect
pip3 install --user .
```

### Usage

#### Command line

Full command line documentation:
```
Usage: i3_resurrect.py save [OPTIONS]

  Save an i3 workspace's layout and running programs to a file.

Options:
  -w, --workspace TEXT       The workspace to save.
  -d, --directory DIRECTORY  The directory to save the workspace to.
                             [default: ~/.i3/i3-resurrect]
  -s, --swallow TEXT         The swallow criteria to use.
                             Options: class, instance, title, window_role
                             [default: class,instance]
  --layout-only              Only save layout.
  --programs-only            Only save running programs.


Usage: i3_resurrect.py restore [OPTIONS]

  Restore i3 workspace layout and programs.

Options:
  -w, --workspace TEXT       The workspace to restore.
  -d, --directory DIRECTORY  The directory to restore the workspace from.
                             [default: ~/.i3/i3-resurrect]
  --layout-only              Only restore layout.
  --programs-only            Only restore running programs.
```

Basic usage, matching only window class/instance:
```
# Save workspace '1'
i3-resurrect save -w 1

# Restore workspace '1'
i3-resurrect restore -w 1
```

More accurate layout restoring by matching title:
```
# Save workspace '1'
i3-resurrect save -w 1 --swallow=class,instance,title

# Restore workspace '1' programs
i3-resurrect restore -w 1 --programs-only

# Apply workspace '1' layout
i3-resurrect restore -w 1 --layout-only
```
When matching windows by title, the programs must be restored before the layout,
because the title often won't match when the window first appears.

When restoring a layout, i3-resurrect uses xdotool to unmap and remap every
window on the workspace which causes i3 to see them as new windows so they will
be swallowed by the placeholder windows.

#### Example configuration in i3

A very basic setup without window title matching:
```
set $i3_resurrect i3-resurrect

# Save workspace mode.
mode "save" {
  bindsym 1 exec $i3_resurrect save -w 1
  bindsym 2 exec $i3_resurrect save -w 2
  bindsym 3 exec $i3_resurrect save -w 3
  bindsym 4 exec $i3_resurrect save -w 4
  bindsym 5 exec $i3_resurrect save -w 5
  bindsym 6 exec $i3_resurrect save -w 6
  bindsym 7 exec $i3_resurrect save -w 7
  bindsym 8 exec $i3_resurrect save -w 8
  bindsym 9 exec $i3_resurrect save -w 9
  bindsym 0 exec $i3_resurrect save -w 0

  # Back to normal: Enter, Escape, or s
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym s mode "default"
  bindsym $mod+s mode "default"
}

bindsym $mod+s mode "save"

# Restore workspace mode.
mode "restore" {
  bindsym 1 exec $i3_resurrect restore -w 1
  bindsym 2 exec $i3_resurrect restore -w 2
  bindsym 3 exec $i3_resurrect restore -w 3
  bindsym 4 exec $i3_resurrect restore -w 4
  bindsym 5 exec $i3_resurrect restore -w 5
  bindsym 6 exec $i3_resurrect restore -w 6
  bindsym 7 exec $i3_resurrect restore -w 7
  bindsym 8 exec $i3_resurrect restore -w 8
  bindsym 9 exec $i3_resurrect restore -w 9
  bindsym 0 exec $i3_resurrect restore -w 0

  # Back to normal: Enter, Escape, or n
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym n mode "default"
  bindsym $mod+n mode "default"
}

bindsym $mod+n mode "restore"
```

A more advanced setup where windows are matched by title:
```
set $i3_resurrect i3-resurrect

# Save workspace mode.
mode "save" {
  bindsym 1 exec "$i3_resurrect save -w 1 --swallow=class,instance,title"
  bindsym 2 exec "$i3_resurrect save -w 2 --swallow=class,instance,title"
  bindsym 3 exec "$i3_resurrect save -w 3 --swallow=class,instance,title"
  bindsym 4 exec "$i3_resurrect save -w 4 --swallow=class,instance,title"
  bindsym 5 exec "$i3_resurrect save -w 5 --swallow=class,instance,title"
  bindsym 6 exec "$i3_resurrect save -w 6 --swallow=class,instance,title"
  bindsym 7 exec "$i3_resurrect save -w 7 --swallow=class,instance,title"
  bindsym 8 exec "$i3_resurrect save -w 8 --swallow=class,instance,title"
  bindsym 9 exec "$i3_resurrect save -w 9 --swallow=class,instance,title"
  bindsym 0 exec "$i3_resurrect save -w 10 --swallow=class,instance,title"

  # Back to normal: Enter, Escape, or s
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym s mode "default"
  bindsym $mod+s mode "default"
}

bindsym $mod+s mode "save"

# Restore workspace mode.
mode "restore" {
  bindsym 1 exec "$i3_resurrect restore -w 1 --programs-only"
  bindsym 2 exec "$i3_resurrect restore -w 2 --programs-only"
  bindsym 3 exec "$i3_resurrect restore -w 3 --programs-only"
  bindsym 4 exec "$i3_resurrect restore -w 4 --programs-only"
  bindsym 5 exec "$i3_resurrect restore -w 5 --programs-only"
  bindsym 6 exec "$i3_resurrect restore -w 6 --programs-only"
  bindsym 7 exec "$i3_resurrect restore -w 7 --programs-only"
  bindsym 8 exec "$i3_resurrect restore -w 8 --programs-only"
  bindsym 9 exec "$i3_resurrect restore -w 9 --programs-only"
  bindsym 0 exec "$i3_resurrect restore -w 10 --programs-only"

  bindsym $mod+1 exec "$i3_resurrect restore -w 1 --layout-only"
  bindsym $mod+2 exec "$i3_resurrect restore -w 2 --layout-only"
  bindsym $mod+3 exec "$i3_resurrect restore -w 3 --layout-only"
  bindsym $mod+4 exec "$i3_resurrect restore -w 4 --layout-only"
  bindsym $mod+5 exec "$i3_resurrect restore -w 5 --layout-only"
  bindsym $mod+6 exec "$i3_resurrect restore -w 6 --layout-only"
  bindsym $mod+7 exec "$i3_resurrect restore -w 7 --layout-only"
  bindsym $mod+8 exec "$i3_resurrect restore -w 8 --layout-only"
  bindsym $mod+9 exec "$i3_resurrect restore -w 9 --layout-only"
  bindsym $mod+0 exec "$i3_resurrect restore -w 10 --layout-only"

  # Back to normal: Enter, Escape, or n
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym n mode "default"
  bindsym $mod+n mode "default"
}

bindsym $mod+n mode "restore"
```

[Example of usage with the second configuration](https://gfycat.com/blankinsidiousgopher)

### Configuration

The config file should be located at `~/.config/i3-resurrect/config.json`.
A default config file will be created when you first run i3-resurrect.

In the case of a window where the process `cmdline` is not the same as the command you must run to
launch that program, you can add an explicit window class to command mapping in the config file.

For example, gnome-terminal's process is gnome-terminal-server, but we need to launch it with the
command `gnome-terminal`. To get this working, you would put the following in your config file:

```
{
  ...
  "window_command_mappings": {
    "Gnome-terminal": "gnome-terminal"
  }
  ...
}
```

Hint:
If you need to find out a window's class, type `xprop | grep WM_CLASS` in a
terminal and then click on the desired window.

For terminal emulator windows, we must get the working directory from the
first subprocess (usually this will be your shell) instead of the window's root
process (the terminal emulator).

i3-resurrect deals with this by allowing you to specify a list of terminal
emulator window classes in your config file.

For example, if you use both Alacritty and gnome-terminal and you want their
working directories to be restored correctly, you would put the following in
your config file:

```
{
  ...
  "terminals": [
    "Gnome-terminal",
    "Alacritty"
  ]
  ...
}
```

These examples are included in the default config. If you would like me to add
more command mappings or terminals to the default config, please open an issue
for it.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

### Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/JonnyHaystack/i3-resurrect/tags).

## Built With

* [Click](https://github.com/pallets/click) - Used to create the command line interface
* [i3ipc](https://github.com/acrisci/i3ipc-python) - Used to get/build the workspace tree
* [wmctrl](https://bitbucket.org/antocuni/wmctrl) - Used to get the PIDs of the windows that are retrieved using i3ipc
* [psutil](https://github.com/giampaolo/psutil) - Used to get the cmdline and cwd of each process
* [xdotool](https://www.semicomplete.com/projects/xdotool/) - Used to unmap and remap windows

## Contributors

* **Jonathan Haylett** - *Creator* - [@JonnyHaystack](https://github.com/JonnyHaystack)

See also the list of [contributors](https://github.com/JonnyHaystack/i3-resurrect/contributors) who participated in this project.

### Acknowledgments

* [@pallets](https://github.com/pallets) - for Click
* [@acrisci](https://github.com/acrisci) - for the i3ipc Python library
* [@antocuni](https://bitbucket.org/antocuni) - for the wmctrl Python library
* [@giampaolo](https://github.com/giampaolo) - for the psutil Python library
* [@jordansissel](https://github.com/jordansissel) - for xdotool
* Everyone who has worked on i3

## Related projects

For those interested, other excellent software I use to get things up and running quickly includes:
- [tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect) - which obviously also inspired
the name of this project
- [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) - an excellent companion to
tmux-resurrect
- [qutebrowser](https://github.com/qutebrowser/qutebrowser) - which has excellent session
management, especially if you create bindings for saving and loading individual windows

## License

This project is licensed under the GNU GPL Version 3 - see the [LICENSE](LICENSE) file for details
