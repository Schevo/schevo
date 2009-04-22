"""Schevo primitive types and constants."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys

from schevo.lib import optimize


class _GLOBAL(type):
    """Base metaclass for global values."""

    def __repr__(cls):
        return cls.__name__

    def __str__(cls):
        return '<%s>' % (cls.__name__, )


class _FALSE(_GLOBAL):
    """Base metaclass for global, false field values."""

    def __nonzero__(cls):
        return False


class _UNASSIGNED(_FALSE):
    """Base metaclass for UNASSIGNED."""

    def __cmp__(cls, other):
        # UNASSIGNED is less than everything, except itself.
        if other is UNASSIGNED:
            return 0
        else:
            return -1

    def __len__(cls):
        return 0

    def __str__(cls):
        return ''  # Particularly useful when exporting to CSV.


class ANY(object):
    """Any entity type is allowed."""

    __metaclass__ = _GLOBAL


class CASCADE(object):
    """Cascade delete on entity field."""

    __metaclass__ = _GLOBAL


class DEFAULT(object):
    """Use the default field value when specifying sample or initial
    data to populate database."""

    __metaclass__ = _GLOBAL


class REMOVE(object):
    """Remove referred-to value from entity field on delete."""

    __metaclass__ = _GLOBAL


class RESTRICT(object):
    """Restrict delete on entity field."""

    __metaclass__ = _GLOBAL


class UNASSIGN(object):
    """Unassign delete on entity field."""

    __metaclass__ = _GLOBAL


class UNASSIGNED(object):
    """Field value or field default value is unassigned."""

    __metaclass__ = _UNASSIGNED

    _label = '<UNASSIGNED>'

    def __init__(self):
        raise TypeError('%r object is not callable' % self.__class__.__name__)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
