"""Copy database structures to a new database file."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo db copy [options] SRCURL DESTURL

SRCURL: The database to copy the internal structures from.

DESTURL: The empty database to copy internal structures to."""


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
            parser.error('Please specify SRCURL and DESTURL.')
        src_url, dest_url = args
        print 'Copying %r to %r...' % (src_url, dest_url)
        schevo.database.copy(src_url, dest_url)
        print 'Copy complete.'


start = Copy
