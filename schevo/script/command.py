"""Command-runner class.

For copyright, license, and warranty, see bottom of file.
"""

import sys


class Command(object):
    """A specific command to be made available using the 'schevo'
    script."""

    name = None
    description = None
    requires_args = False

    _call_level = 0

    def __call__(self, *args):
        if self._call_level:
            print '::',
        print self.name,
        Command._call_level += 1
        if not args:
            args = sys.argv[:]
        if args:
            arg0 = args[0]
            args = args[1:]
        else:
            arg0 = None
            args = []
        return self.main(arg0, args)

    def help(self):
        pass

    def main(self, arg0, args):
        if ((self.requires_args and not args)
            or (args and (args[0] in ('--help')))
            ):
            self.help()
            return 1


class CommandSet(Command):
    """A set of sub-commands to be made available using the 'schevo'
    script."""

    commands = []
    requires_args = True

    def help(self):
        print
        print
        print 'Available commands:'
        print
        commands = self.commands
        longest = max(len(key) for key in commands)
        format = '%' + str(longest) + 's: %s'
        for command_name, command in sorted(commands.items()):
            print format % (command_name, command.description)
        print

    def main(self, arg0, args):
        if not Command.main(self, arg0, args):
            # Replace arg0 with the command specified and take it off
            # of args.
            command_name = args[0]
            if command_name not in self.commands:
                self.help()
                print 'NOTE: Command %r not found.' % command_name
                return 1
            command = self.commands[command_name]
            return command()(*args)


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
# http://orbtech.com/
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
