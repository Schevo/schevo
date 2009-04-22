"""General option parser."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from optparse import OptionParser

from schevo import trace


def set_trace(option, opt, value, parser):
    trace.print_history(value)
    trace.monitor_level = value
    trace.log(1, 'Tracing level set to', value)


def parser(usage):
    p = OptionParser(usage)
    p.add_option('-B', '--backend',
                 dest='backend_name',
                 help='Use the named backend.',
                 metavar='NAME',
                 default=None,
                 )
    p.add_option('-A', '--backend-args',
                 dest='backend_args',
                 help='Pass the given arguments to the backend.',
                 metavar='ARGS',
                 default=None,
                 )
    p.add_option('-T', '--trace',
                 help='Set Schevo tracing level.',
                 action='callback',
                 callback=set_trace,
                 type=int,
                 )
    return p
