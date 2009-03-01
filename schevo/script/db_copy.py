"""Copy database structures to a new database file.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo db copy [options] SRCFILE DESTFILE

SRCFILE: The database file to copy the internal structures from.

DESTFILE: The empty file to copy internal structures to.

Backend options given apply to DESTFILE. The backend for SRCFILE is
determined automatically."""


def _parser():
    p = opt.parser(usage)
    return p


class Copy(Command):

    name = 'Copy'
    description = 'Copy database structures to a new database file.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 2:
            parser.error('Please specify SRCFILE and DESTFILE.')
        src_filename, dest_filename = args
        print 'Copying %r to %r...' % (src_filename, dest_filename)
        schevo.database.copy(
            src_filename=src_filename,
            dest_filename=dest_filename,
            dest_backend_name=options.backend_name,
            dest_backend_args=options.backend_args,
            )
        print 'Copy complete.'


start = Copy


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
