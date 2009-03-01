"""Python shell command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys

import schevo.database

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo shell [options] DBFILE

DBFILE: The database file to open.  The database will be present as
the 'db' variable in the shell.

If IPython is available, it will be used automatically."""


def _parser():
    p = opt.parser(usage)
    return p


class Shell(Command):

    name = 'Python Shell'
    description = 'Start a Python shell with an open database.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            print 'DBFILE must be specified.'
            return 1
        db_filename = args[0]
        # Open the database.
        print 'Opened database', db_filename
        db = schevo.database.open(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            )
        # Set up environment.
        locals = dict(
            __name__='schevo-shell',
            db=db,
            )
        # sys.argv can clobber the shell if we're not careful.
        old_argv = sys.argv
        sys.argv = sys.argv[0:1]
        try:
            # Try to use IPython if available.
            try:
                import IPython
            except ImportError:
                import code
                code.interact(local=locals)
            else:
                shell = IPython.Shell.IPShell(user_ns=locals)
                shell.mainloop()
        finally:
            sys.argv = old_argv


start = Shell
