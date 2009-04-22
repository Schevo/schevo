"""Test base classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

__all__ = [
    'BaseTest',
    'ComparesDatabases',
    'CreatesDatabase',
    'CreatesSchema',
    'DocTest',
    'DocTestEvolve',
    'EvolvesSchemata',
    'PREAMBLE',
    'raises',
    ]

import sys

import schevo.trace
from schevo.trace import log
# XXX Problems with nose 0.8.7, so disable detailed tracing for now.
## schevo.trace.TRACE_TO = sys.stdout
## schevo.trace.monitor_level = 3

from schevo.test.base import (
    BaseTest,
    ComparesDatabases,
    CreatesDatabase,
    CreatesSchema,
    DocTest,
    DocTestEvolve,
    EvolvesSchemata,
    PREAMBLE,
    raises,
    )
