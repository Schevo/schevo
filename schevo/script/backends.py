"""Installed backends command.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo backends

Shows a list of installed backends and the options that each one
accepts."""


def _parser():
    p = opt.parser(usage)
    return p


class Backends(Command):

    name = 'Installed Backends'
    description = 'Show a list of installed backends.'

    def main(self, arg0, args):
        print
        print
        from schevo.backend import backends
        for backend_name, backend_class in sorted(backends.iteritems()):
            print backend_name, '-', backend_class.description
            print '=' * (len(backend_name) + len(backend_class.description) + 3)
            print 'Available options for --backend-args:'
            print dedent(backend_class.backend_args_help).strip()
            print


start = Backends


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
