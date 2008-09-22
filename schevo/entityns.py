"""Entity namespace classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from functools import wraps
import inspect
from string import digits, ascii_letters

from schevo import base
from schevo.constant import UNASSIGNED
from schevo.decorator import (
    extentclassmethod, extentmethod, isextentmethod, isselectionmethod,
    selectionmethod, with_label)
from schevo.error import (
    EntityDoesNotExist, ExtentDoesNotExist, FieldDoesNotExist, KeyIndexOverlap)
from schevo.fieldspec import field_spec_from_class
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import (
    LabelMixin, label_from_name, plural_from_name, relabel)
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo import query
from schevo import transaction
from schevo import view


class EntityClassExtenders(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_c']

    def __init__(self, cls):
        self._c = cls


class EntityExtenders(NamespaceExtension):
    """A namespace of entity-level methods."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        for x_name in entity._x_names:
            func = getattr(entity, x_name)
            name = x_name[2:]
            d[name] = func


class EntityFields(object):

    __slots__ = ['_entity']

    def __init__(self, entity):
        self._entity = entity

    def __getattr__(self, name):
        e = self._entity
        FieldClass = e._field_spec[name]
        field = FieldClass(e, getattr(e, name))
        return field

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __iter__(self):
        return iter(self._entity._field_spec)

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(iter(self))


class EntityOneToMany(NamespaceExtension):

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        e = entity
        db = e._db
        extent_name = e._extent.name
        oid = e._oid
        last_extent_name = ''
        for other_extent_name, other_field_name in e._extent.relationships:
            # The first field for an other_extent becomes the default.
            if other_extent_name == last_extent_name:
                continue
            last_extent_name = other_extent_name
            many_name = _many_name(db.extent(other_extent_name)._plural)
            many_func = _many_func(db, extent_name, oid,
                                   other_extent_name, other_field_name)
            d[many_name] = many_func

def _many_func(db, extent_name, oid, other_extent_name, other_field_name):
    """Return a many function."""
    links = db._entity_links
    def many(other_field_name=other_field_name):
        return links(extent_name, oid, other_extent_name, other_field_name)
    return many

_ALLOWED = digits + ascii_letters + ' '
def _many_name(name):
    """Return a canonical many name."""
    # Strip all but alphanumeric and spaces.
    name = ''.join(c for c in name if c in _ALLOWED)
    # Convert to lowercase 8-bit string.
    name = str(name).lower()
    # Replace spaces with underscores.
    name = name.replace(' ', '_')
    return name


class EntityClassQueries(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_c']

    def __init__(self, cls):
        self._c = cls


class EntityQueries(NamespaceExtension):
    """A namespace of entity-level queries."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for q_name in entity._q_names:
            func = getattr(entity, q_name)
            name = q_name[2:]
            d[name] = func

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._e._hidden_queries)


class EntitySys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_entity']

    def __init__(self, entity):
        """Create a sys namespace for the `entity`."""
        NamespaceExtension.__init__(self)
        self._entity = entity

    def as_data(self):
        """Return tuple of entity values in a form suitable for
        initial or sample data in a schema."""
        def resolve(entity, fieldname):
            field = entity.f[fieldname]
            value = getattr(entity, fieldname)
            if isinstance(value, base.Entity):
                entity = value
                values = []
                for fieldname in entity.sys.extent.default_key:
                    value = resolve(entity, fieldname)
                    values.append(value)
                if len(field.allow) > 1:
                    values = (entity.sys.extent.name, tuple(values))
                return tuple(values)
            else:
                return value
        values = []
        create = self._entity.t_create()
        e = self._entity
        for f_name in e.f:
            if (f_name not in create.f
                or create.f[f_name].hidden or create.f[f_name].readonly):
                # Don't include a field that doesn't exist in the
                # create transaction, or is hidden or readonly.
                continue
            f = e.f[f_name]
            if f.fget is not None or f.hidden:
                pass
            else:
                value = resolve(e, f_name)
                values.append(value)
        return tuple(values)

    def count(self, other_extent_name=None, other_field_name=None):
        """Return count of all links, or specific links if
        `other_extent_name` and `other_field_name` are supplied."""
        e = self._entity
        return e._db._entity_links(e._extent.name, e._oid, other_extent_name,
                                   other_field_name, return_count=True)

    @property
    def db(self):
        """Return the database to which this entity belongs."""
        return self._entity._db

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        entity = self._entity
        oid = entity._oid
        extent = entity._extent
        return oid in extent

    @property
    def extent(self):
        """Return the extent to which this entity belongs."""
        return self._entity._extent

    @property
    def extent_name(self):
        """Return the name of the extent to which this entity belongs."""
        return self._entity._extent.name

    def field_map(self, *filters):
        """Return field_map for the entity, filtered by optional
        callable objects specified in `filters`."""
        e = self._entity
        db = e._db
        stored_values = e._db._entity_fields(e._extent.name, e._oid)
        entity_field_map = e._field_spec.field_map(e, stored_values)
        # Remove fields that should not be included.
        new_fields = entity_field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        entity_field_map = FieldMap(
            (field.name, field) for field in new_fields)
        for field in entity_field_map.itervalues():
            if field.fget is not None:
                # Update fields that have fget callables.
                value = field.fget[0](e)
            else:
                # Allow fields to restore themselves from a stored
                # value.
                field._restore(db)
        return entity_field_map

    def links(self, other_extent_name=None, other_field_name=None):
        """Return dictionary of (extent_name, field_name): entity_list
        pairs, or list of linking entities if `other_extent_name` and
        `other_field_name` are supplied."""
        e = self._entity
        return e._db._entity_links(e._extent.name, e._oid,
                                   other_extent_name, other_field_name)

    def links_filter(self, other_extent_name, other_field_name):
        """Return a callable that returns the current list of linking
        entities whenever called."""
        db = self._entity._db
        try:
            extent = db.extent(other_extent_name)
        except KeyError:
            raise ExtentDoesNotExist(other_extent_name)
        if other_field_name not in extent.field_spec:
            raise FieldDoesNotExist(other_extent_name, other_field_name)
        def _filter():
            return self.links(other_extent_name, other_field_name)
        return _filter

    @property
    def oid(self):
        """Return the OID of the entity."""
        return self._entity._oid

    @property
    def rev(self):
        """Return the revision number of the entity."""
        return self._entity._rev


class EntityClassTransactions(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_c']

    def __init__(self, cls):
        self._c = cls


class EntityTransactions(NamespaceExtension):
    """A namespace of entity-level transactions."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for t_name in entity._t_names:
            func = getattr(entity, t_name)
            name = t_name[2:]
            d[name] = func

    def __call__(self, *filters):
        if filters == (isselectionmethod, ):
            hidden = self._hidden_actions()
            return (k for k, v in self._d.iteritems()
                    if (k not in hidden
                        and isselectionmethod(v)
                        )
                    )
        else:
            # XXX: Should actually scan through transaction methods
            # and run them through a filter, returning names of those
            # methods that match.
            return []

    def __iter__(self):
        hidden = self._hidden_actions()
        return (k for k, v in self._d.iteritems()
                if (k not in hidden
                    and not isselectionmethod(v)
                    )
                )

    def _hidden_actions(self):
        entity = self._e
        hidden = entity._hidden_actions.copy()
        hidden_t_methods = getattr(entity, '_hidden_t_methods', None)
        if hidden_t_methods is not None:
            hidden.update(hidden_t_methods() or [])
        return hidden


class EntityClassViews(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_c']

    def __init__(self, cls):
        self._c = cls


class EntityViews(NamespaceExtension):
    """A namespace of entity-level views."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for v_name in entity._v_names:
            func = getattr(entity, v_name)
            name = v_name[2:]
            d[name] = func

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._e._hidden_views)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2007 Orbtech, L.L.C. and contributors
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
