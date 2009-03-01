"""Introspection functions for Schevo."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from inspect import ismethod as isinstancemethod

__all__ = [
    'commontype',
    'isextentmethod',
    'isinstancemethod',
    'isselectionmethod',
    ]


def commontype(objs):
    types = set(type(obj) for obj in objs)
    if len(types) == 1:
        return types.pop()
    else:
        return None


def isextentmethod(fn):
    return getattr(fn, '_extentmethod', False)


def isselectionmethod(fn):
    return getattr(fn, '_selectionmethod', False)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
