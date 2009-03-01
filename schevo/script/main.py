"""Main 'schevo' script runner.

For copyright, license, and warranty, see bottom of file.
"""

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


# Copyright (C) 2001-2009 ElevenCraft Inc.
#
# Schevo
# http://schevo.org/
#
# ElevenCraft Inc.
# Bellingham, WA
# http://11craft.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
