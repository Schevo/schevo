"""Introspection functions for Schevo.

For copyright, license, and warranty, see bottom of file.
"""

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


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
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
