"""Repair database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

from schevo.label import label
import schevo.database
import schevo.repair

from schevo.script.command import Command
from schevo.script import opt


usage = """\
schevo db repair [options] DBFILE

DBFILE: The database file to check (and repair if requested).
"""


def _parser():
    p = opt.parser(usage)
    p.add_option('-r', '--repair',
                 dest='repair',
                 help='Perform all applicable repairs to database.',
                 action='store_true',
                 default=False,
                 )
    return p


class Repair(Command):

    name = 'Repair Database'
    description = 'Check and repair problems on an existing database.'

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
        print 'Opening database...'
        db = schevo.database.open(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            )
        print
        print 'Label:', label(db)
        print 'Version:', db.version
        print 'Format:', db.format
        print
        print 'Checking for needed repairs...'
        print
        repairs = schevo.repair.repairs_needed(db, db_filename)
        db.close()
        if len(repairs) == 0:
            print 'No repairs needed.'
            return
        print 'Repairs needed:'
        for repair in repairs:
            print '-', repair.description
            if repair.is_needed_certainty == False:
                print (
                    '    (Could not detect if needed; '
                    'assuming so for safety.)'
                    )
        print
        if not options.repair:
            print 'Use -r or --repair option to perform repairs.'
            return
        print 'Repairing database...'
        for repair in repairs:
            repair.perform()
            print 'Done:', repair.description
        print
        print 'Re-checking for needed repairs...'
        print
        db = schevo.database.open(db_filename)
        repairs_with_certainty = [
            r for r in schevo.repair.repairs_needed(db, db_filename)
            if r.is_needed_certainty == True
            ]
        db.close()
        if len(repairs_with_certainty) > 0:
            print 'WARNING! Repairs needed despite actions taken above:'
            for repair in repairs:
                print '-', repair.description
            print
            return 1
        else:
            print 'No repairs needed.'


start = Repair


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
