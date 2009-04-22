"""Convert database structure to new format."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
                 default=None,
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
        format = options.format
        if format is not None:
            format = int(format)
            print 'Converting %r to format %r...' % (db_filename, format)
        else:
            print 'Converting %r to latest format...' % db_filename
        schevo.database.convert_format(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            format=format,
            )
        print 'Conversion complete.'


start = Format
