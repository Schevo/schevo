"""Installed backends command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from textwrap import dedent

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo backends

Shows a list of installed backends and the options that each one
accepts."""


def _parser():
    p = opt.parser(usage)
    return p


class Backends(Command):

    name = 'Installed Backends'
    description = 'Show a list of installed backends.'

    def main(self, arg0, args):
        print
        print
        from schevo.backend import backends
        for backend_name, backend_class in sorted(backends.iteritems()):
            print backend_name, '-', backend_class.description
            print '=' * (len(backend_name) + len(backend_class.description) + 3)
            print 'Available options for --backend-args:'
            print dedent(backend_class.backend_args_help).strip()
            print


start = Backends
