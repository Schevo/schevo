"""Pack database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
