"""Pack database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path

usage = """\
schevo db pack DBFILE

DBFILE: The database file to pack.
"""


def _parser():
    p = opt.parser(usage)
    return p


class Pack(Command):

    name = 'Pack Database'
    description = 'Pack an existing database.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify DBFILE.')
        db_filename = args[0]
        # Open the database.
        if not os.path.isfile(db_filename):
            parser.error('DBFILE must be an existing database.')
        db = schevo.database.open(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            )
        # Pack the database.
        print 'Packing the database...'
        db.pack()
        # Done.
        db.close()
        print 'Database pack complete.'


start = Pack


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
