"""Transaction namespace classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.change import summarize
from schevo.constant import (CASCADE, DEFAULT, REMOVE, RESTRICT,
                             UNASSIGN, UNASSIGNED)
from schevo.error import (
    DeleteRestricted,
    KeyCollision,
    SchemaError,
    TransactionExecuteRedefinitionRestricted,
    TransactionExpired,
    TransactionFieldsNotChanged,
    TransactionNotExecuted,
    )
from schevo.field import Entity, _EntityBase, not_fget
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo.trace import log


class TransactionExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, tx):
        NamespaceExtension.__init__(self, name, tx)
        d = self._d
        for x_name in tx._x_names:
            func = getattr(tx, x_name)
            name = x_name[2:]
            d[name] = func


class TransactionChangeHandlers(NamespaceExtension):
    """A namespace of field change handlers."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, tx):
        NamespaceExtension.__init__(self, name, tx)
        d = self._d
        for h_name in tx._h_names:
            func = getattr(tx, h_name)
            name = h_name[2:]
            d[name] = func


class TransactionSys(NamespaceExtension):

    @property
    def changes(self):
        return self._i._changes

    @property
    def current_field_map(self):
        return self._i._field_map

    @property
    def executed(self):
        return self._i._executed

    @property
    def extent_name(self):
        if hasattr(self._i, '_extent_name'):
            return self._i._extent_name

    def field_map(self, *filters):
        # Remove fields that should not be included.
        new_fields = self._i._field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        return FieldMap((field.name, field) for field in new_fields)

    @property
    def field_was_changed(self):
        """True if at least one field was changed."""
        return self._i._field_was_changed

    @property
    def requires_changes(self):
        return getattr(self._i, '_requires_changes', False)

    def summarize(self):
        return summarize(self._i)


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
