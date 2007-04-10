"""Convert database structure to new format.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo db convert [options] DBFILE

DBFILE: The database file to convert to a new format."""


def _parser():
    p = opt.parser(usage)
    p.add_option('-f', '--format', dest='format',
                 help='Convert to a specific format. (Default: latest format.)',
                 metavar='FORMAT',
                 default=2,
                 )
    return p


class Format(Command):

    name = 'Convert Format'
    description = 'Convert a database file to a new storage format.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify DBFILE.')
        db_filename = args[0]
        format = int(options.format)
        if format is not None:
            format = int(format)
        print 'Converting %r to format %i...' % (db_filename, format)
        schevo.database.convert_format(db_filename, format)
        print 'Conversion complete.'


start = Format


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
