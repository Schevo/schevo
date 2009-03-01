"""Command-runner class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
