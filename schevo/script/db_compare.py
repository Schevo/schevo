"""Compare database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db compare DBFILE1 DBFILE2

DBFILE1, DBFILE2: The database files to compare.
"""


def _parser():
    p = opt.parser(usage)
    return p


class Compare(Command):

    name = 'Compare Databases'
    description = 'Compare two existing databases.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 2:
            parser.error('Please specify DBFILE1 and DBFILE2.')
        db_filename1, db_filename2 = args
        # Open the databases.
        if not os.path.isfile(db_filename1):
            parser.error('DBFILE1 must be an existing database.')
        if not os.path.isfile(db_filename2):
            parser.error('DBFILE2 must be an existing database.')
        print 'Opening databases...'
        db1 = schevo.database.open(
            filename = db_filename1,
            backend_name = options.backend_name,
            backend_args = options.backend_args,
            )
        db2 = schevo.database.open(
            db_filename2,
            backend_name = options.backend_name,
            backend_args = options.backend_args,
            )
        # Compare them.
        is_equivalent = schevo.database.equivalent(db1, db2)
        # Done.
        db1.close()
        db2.close()
        # Report.
        if is_equivalent:
            print 'Databases are EQUIVALENT.'
            return 0
        else:
            print 'Databases are NOT EQUIVALENT.'
            return 1


start = Compare


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
