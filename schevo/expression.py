"""Utilities for forming search expressions based on field classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize


class Expression(object):

    def __init__(self, field, op, value):
        self.field = field
        self.op = op
        self.value = value


optimize.bind_all(sys.modules[__name__])  # Last line of module.
