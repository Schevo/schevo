"""Main 'schevo' script runner."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import pkg_resources

from schevo.script.command import CommandSet


# Get version information from installed package.
dist = pkg_resources.get_distribution('Schevo')
NAME = dist.project_name
VERSION = dist.version


class Main(CommandSet):

    name = '%s %s' % (NAME, VERSION)

    def __init__(self):
        commands = self.commands = {}
        for p in pkg_resources.iter_entry_points('schevo.schevo_command'):
            name = p.name
            command = p.load()
            commands[name] = command


start = Main()


def start_hotshot():
    import hotshot
    import hotshot.stats
    import os
    import schevo
    filename = 'schevo.prof'
    prof = hotshot.Profile(filename)
    prof.runcall(start)
    prof.close()
    stats = hotshot.stats.load(filename)
    # Print reports including all code, even dependencies.
    stats.sort_stats('cumulative', 'calls')
    stats.print_stats(50)
    stats.sort_stats('time', 'calls')
    stats.print_stats(50)
    # Print reports showing only Schevo code.
    stats.sort_stats('cumulative', 'calls')
    schevo_package_path = os.path.dirname(schevo.__file__)
    schevo_package_path = schevo_package_path.replace('\\', '\\\\')
    # Hotshot stores a lowercase form of the path so we need to
    # lowercase our path or the regular expression will fail.
    schevo_package_path = schevo_package_path.lower()
    stats.print_stats(schevo_package_path, 50)
    stats.sort_stats('time', 'calls')
    stats.print_stats(schevo_package_path, 50)
