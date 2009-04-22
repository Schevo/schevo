"""Copy database structures to a new database file."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
