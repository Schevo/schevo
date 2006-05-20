"""Schevo primitive types and constants.

For copyright, license, and warranty, see bottom of file.
"""

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


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
