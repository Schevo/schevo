"""Pack database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path

usage = """\
schevo db pack URL

URL: URL of the database to pack.
"""


def _parser():
    p = opt.parser(usage)
    return p


class Pack(Command):

    name = 'Pack Database'
    description = 'Pack an existing database to reclaim unused space.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify URL.')
        url = args[0]
        # Open the database.
        db = schevo.database.open(url)
        # Pack the database.
        print 'Packing the database...'
        db.pack()
        # Done.
        db.close()
        print 'Database pack complete.'


start = Pack
