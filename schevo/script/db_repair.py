"""Repair database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

from schevo.label import label
import schevo.database
import schevo.repair

from schevo.script.command import Command
from schevo.script import opt


usage = """\
schevo db repair [options] URL

URL: URL of the database file to check (and repair if requested).
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
            parser.error('Please specify URL.')
        url = args[0]
        # Open the database.
        print 'Opening database...'
        db = schevo.database.open(url)
        print
        print 'Label:', label(db)
        print 'Version:', db.version
        print 'Format:', db.format
        print
        print 'Checking for needed repairs...'
        print
        repairs = schevo.repair.repairs_needed(db, url)
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
        db = schevo.database.open(url)
        repairs_with_certainty = [
            r for r in schevo.repair.repairs_needed(db, url)
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
