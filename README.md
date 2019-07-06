# i3-resurrect

A simple but flexible solution to saving and restoring i3 workspaces

## Table of Contents

* [Introduction](#introduction)
* [Getting Started](#getting-started)
   * [Installation](#installation)
   * [Usage](#usage)
   * [Configuration](#configuration)
* [Contributing](#contributing)
* [Contributors](#contributors)
* [License](#license)

## Introduction

i3-resurrect originated as a mixture of hacked together Python and bash scripts that I
wrote in order to be able to quickly save and load workspaces on the fly.

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

## Getting Started

### Requirements

- i3
- Working i3-save-tree command
  - This requires the package `perl-anyevent-i3`

### Installation

#### From PyPI (recommended)

```
pip3 install --user i3-resurrect
```

#### Manual

Obtain source code
```
git clone git@github.com:JonnyHaystack/i3-resurrect.git
```

Install dependencies then run script directly
```
# Install dependencies
cd i3-resurrect
pip3 install --user -r requirements.txt

# Run script directly
python3 i3-resurrect.py
```

Or just install locally using pip
```
pip3 install --user .
```

### Usage

#### Command line

```
# Save workspace '1'
i3-resurrect save -w 1

# Restore workspace '1'
i3-resurrect restore -w 1
```

#### Example configuration in i3

```
# Save workspace mode.
mode "save" {
  bindsym 1 exec "i3-resurrect save -w 1"
  bindsym 2 exec "i3-resurrect save -w 2"
  bindsym 3 exec "i3-resurrect save -w 3"
  bindsym 4 exec "i3-resurrect save -w 4"
  bindsym 5 exec "i3-resurrect save -w 5"
  bindsym 6 exec "i3-resurrect save -w 6"
  bindsym 7 exec "i3-resurrect save -w 7"
  bindsym 8 exec "i3-resurrect save -w 8"
  bindsym 9 exec "i3-resurrect save -w 9"
  bindsym 0 exec "i3-resurrect save -w 0"

  # Back to normal: Enter, Escape, or s
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym s mode "default"
  bindsym $mod+s mode "default"
}

bindsym $mod+s mode "save"

# Restore workspace mode.
mode "restore" {
  bindsym 1 exec "i3-resurrect restore -w 1"
  bindsym 2 exec "i3-resurrect restore -w 2"
  bindsym 3 exec "i3-resurrect restore -w 3"
  bindsym 4 exec "i3-resurrect restore -w 4"
  bindsym 5 exec "i3-resurrect restore -w 5"
  bindsym 6 exec "i3-resurrect restore -w 6"
  bindsym 7 exec "i3-resurrect restore -w 7"
  bindsym 8 exec "i3-resurrect restore -w 8"
  bindsym 9 exec "i3-resurrect restore -w 9"
  bindsym 0 exec "i3-resurrect restore -w 0"

  # Back to normal: Enter, Escape, or n
  bindsym Return mode "default"
  bindsym Escape mode "default"
  bindsym n mode "default"
  bindsym $mod+n mode "default"
}

bindsym $mod+n mode "restore"
```

### Configuration

The config file should be located at `~/.config/i3-resurrect/config.json`. You will have to create
it yourself if you want to use it.

In the case of a window where the process cmdline is not the same as the command you must run to
launch that program, you can add an explicit window class to command mapping in the config file.

For example, gnome-terminal's process is gnome-terminal-server, but we need to launch it with the
command gnome-terminal. To get this working, you would put the following in your config file:

```
{
  "window_command_mappings": {
    "Gnome-terminal": "gnome-terminal"
  }
}
```

If you need to find out a window's class, type `xprop | grep WM_CLASS` in a terminal and then click
on the desired window.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

### Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/JonnyHaystack/i3-resurrect/tags).

## Built With

* [i3ipc](https://github.com/acrisci/i3ipc-python) - Used to get the list of windows in a specified workspace
* [wmctrl](https://bitbucket.org/antocuni/wmctrl) - Used to get the PIDs of the windows that are retrieved using i3ipc
* [psutil](https://github.com/giampaolo/psutil) - Used to get the cmdline and cwd of each process

## Contributors

* **Jonathan Haylett** - *Creator* - [@JonnyHaystack](https://github.com/JonnyHaystack)

See also the list of [contributors](https://github.com/JonnyHaystack/i3-resurrect/contributors) who participated in this project.

### Acknowledgments

* [@acrisci](https://github.com/acrisci) - for the i3ipc Python library
* [@antocuni](https://bitbucket.org/antocuni) - for the wmctrl Python library
* [@giampaolo](https://github.com/giampaolo) - for the psutil Python library
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
