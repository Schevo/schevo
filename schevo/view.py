"""View classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.constant import UNASSIGNED
from schevo import field
from schevo.fieldspec import (
    FieldDefinition, FieldSpecMap, field_spec_from_class)
from schevo.label import label, label_from_name
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension


class View(base.View):
    """Views mimic the behavior of entities, while providing
    alternative information about them."""

    __metaclass__ = schema_metaclass('V')

    __slots__ = ['_entity', '_fields', 'f', 'q', 'sys', 't', 'v', 'x']

    _field_spec = FieldSpecMap()

    def __init__(self, entity):
        self._entity = entity
        f = self._fields = self._field_spec.field_map(instance=self)
        f.update_values(entity.sys.fields())
        # All fields should be readonly by default.
        for field in f.itervalues():
            field.readonly = True
        self.f = schevo.namespace.Fields(self)
        self.sys = ViewSys(self)
        # XXX: This should be looked at more closely.
        if entity is not None:
            self.q = entity.q
            self.t = entity.t
            self.v = entity.v
        # /XXX
        self.x = ViewExtenders()

    def __getattr__(self, name):
        return self._fields[name].get()

    def __setattr__(self, name, value):
        if name == 'sys' or name.startswith('_') or len(name) == 1:
            return base.View.__setattr__(self, name, value)
        else:
            self._fields[name].assign(value)

    def __str__(self):
        return str(self._entity)

    def __unicode__(self):
        return unicode(self._entity)


class ViewExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False


class ViewSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_view']

    def __init__(self, view):
        NamespaceExtension.__init__(self)
        self._view = view

    @property
    def entity(self):
        return self._view._entity

    def fields(self):
        return self._view._fields

    @property
    def extent(self):
        return self._view._entity.sys.extent

    @property
    def extent_name(self):
        return self.extent.name

    @property
    def count(self):
        return self._view._entity.sys.count

    @property
    def links(self):
        return self._view._entity.sys.links

    @property
    def oid(self):
        return self._view._entity.sys.oid


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
