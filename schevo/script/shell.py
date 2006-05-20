"""Python shell command.

For copyright, license, and warranty, see bottom of file.
"""

import sys

import schevo.database

from schevo.script.command import Command
from schevo.script import opt

usage = """\
evo shell [options] DBFILE

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
        db = schevo.database.open(db_filename)
        # Set up environment.
        locals = dict(
            __name__='evo-shell',
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
                code.interact(locals=locals)
            else:
                shell = IPython.Shell.IPShell(user_ns=locals)
                shell.mainloop()
        finally:
            sys.argv = old_argv


start = Shell


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
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
