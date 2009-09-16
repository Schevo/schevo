"""Compare database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db compare URL1 URL2

URL1, URL2: URLs of databases to compare.
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
            parser.error('Please specify URL1 and URL2.')
        url1, url2 = args
        # Open the databases.
        print 'Opening databases...'
        db1 = schevo.database.open(url1)
        db2 = schevo.database.open(url2)
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
