"""Query namespace classes.

For copyright, license, and warranty, see bottom of file.
"""

import operator
import sys
from schevo.lib import optimize

from schevo import base
from schevo.constant import UNASSIGNED
import schevo.error
from schevo import field
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label, plural
from schevo.lib.odict import odict
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo.trace import log


class ParamChangeHandlers(NamespaceExtension):
    """A namespace of field change handlers."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, query):
        NamespaceExtension.__init__(self, name, query)
        d = self._d
        # Note: could be optimized via using a metaclass with
        # ParamQuery.
        for name in dir(query):
            if name.startswith('h_'):
                func = getattr(query, name)
                name = name[2:]
                d[name] = func


class ParamSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def field_map(self, *filters):
        # Remove fields that should not be included.
        new_fields = self._i._field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        return FieldMap((field.name, field) for field in new_fields)


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
