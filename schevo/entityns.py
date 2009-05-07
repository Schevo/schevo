"""Entity namespace classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from functools import wraps
import inspect
from string import digits, ascii_letters

from schevo import base
from schevo.constant import UNASSIGNED
from schevo.decorator import (
    extentclassmethod, extentmethod, selectionmethod, with_label)
from schevo.error import (
    EntityDoesNotExist, ExtentDoesNotExist, FieldDoesNotExist, KeyIndexOverlap)
from schevo.fieldspec import field_spec_from_class
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.introspect import isextentmethod, isselectionmethod
from schevo.label import (
    LabelMixin, label_from_name, plural_from_name, relabel)
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo import query
from schevo import transaction
from schevo import view


class EntityClassExtenders(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class EntityExtenders(NamespaceExtension):
    """A namespace of entity-level methods."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        for x_name in instance._x_instancemethod_names:
            func = getattr(instance, x_name)
            name = x_name[2:]
            d[name] = func


class EntityClassFields(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class EntityFields(object):

    __slots__ = ['_n', '_i', '_f']

    def __init__(self, name, instance):
        self._n = name
        self._i = instance
        self._f = {}

    def __getattr__(self, name):
        if name in self._f:
            return self._f[name]
        else:
            instance = self._i
            FieldClass = instance._field_spec[name]
            field = FieldClass(instance, getattr(instance, name))
            self._f[name] = field
            return field

    __getitem__ = __getattr__

    def __iter__(self):
        return iter(self._i._field_spec)

    def __length_hint__(self):
        return len(self._i._field_spec)

    def __repr__(self):
        return '<%r namespace on %r>' % (self._n, self._i)

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(iter(self))


class EntityOneToMany(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        i = instance
        db = i._db
        extent_name = i._extent.name
        oid = i._oid
        last_extent_name = ''
        for other_extent_name, other_field_name in i._extent.relationships:
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

    __slots__ = NamespaceExtension.__slots__


class EntityQueries(NamespaceExtension):
    """A namespace of entity-level queries."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        for q_name in instance._q_instancemethod_names:
            func = getattr(instance, q_name)
            name = q_name[2:]
            d[name] = func

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._i._hidden_queries)


class EntitySys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def as_data(self):
        """Return tuple of entity values in a form suitable for
        initial or sample data in a schema."""
        def resolve(entity, fieldname):
            field = entity.f[fieldname]
            value = getattr(entity, fieldname)
            if isinstance(value, base.Entity):
                entity = value
                values = []
                for fieldname in entity.s.extent.default_key:
                    value = resolve(entity, fieldname)
                    values.append(value)
                if len(field.allow) > 1:
                    values = (entity.s.extent.name, tuple(values))
                return tuple(values)
            else:
                return value
        values = []
        instance = self._i
        create = instance.t_create()
        for f_name in instance.f:
            if (f_name not in create.f
                or create.f[f_name].hidden or create.f[f_name].readonly):
                # Don't include a field that doesn't exist in the
                # create transaction, or is hidden or readonly.
                continue
            f = instance.f[f_name]
            if f.fget is not None or f.hidden:
                pass
            else:
                value = resolve(instance, f_name)
                values.append(value)
        return tuple(values)

    def count(self, other_extent_name=None, other_field_name=None):
        """Return count of all links, or specific links if
        `other_extent_name` and `other_field_name` are supplied."""
        i = self._i
        return i._db._entity_links(i._extent.name, i._oid, other_extent_name,
                                   other_field_name, return_count=True)

    @property
    def db(self):
        """Return the database to which this entity belongs."""
        return self._i._db

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        instance = self._i
        oid = instance._oid
        extent = instance._extent
        return oid in extent

    @property
    def extent(self):
        """Return the extent to which this entity belongs."""
        return self._i._extent

    @property
    def extent_name(self):
        """Return the name of the extent to which this entity belongs."""
        return self._i._extent.name

    def field_map(self, *filters):
        """Return field_map for the entity, filtered by optional
        callable objects specified in `filters`."""
        i = self._i
        db = i._db
        stored_values = i._db._entity_fields(i._extent.name, i._oid)
        entity_field_map = i._field_spec.field_map(i, stored_values)
        # Remove fields that should not be included.
        new_fields = entity_field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        entity_field_map = FieldMap(
            (field.name, field) for field in new_fields)
        for field in entity_field_map.itervalues():
            if field.fget is not None:
                # Update fields that have fget callables.
                value = field.fget[0](i)
            else:
                # Allow fields to restore themselves from a stored
                # value.
                field._restore(db)
        return entity_field_map

    def links(self, other_extent_name=None, other_field_name=None):
        """Return dictionary of (extent_name, field_name): entity_list
        pairs, or list of linking entities if `other_extent_name` and
        `other_field_name` are supplied."""
        i = self._i
        return i._db._entity_links(i._extent.name, i._oid,
                                   other_extent_name, other_field_name)

    def links_filter(self, other_extent_name, other_field_name):
        """Return a callable that returns the current list of linking
        entities whenever called."""
        db = self._i._db
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
        return self._i._oid

    @property
    def rev(self):
        """Return the revision number of the entity."""
        return self._i._rev


class EntityClassTransactions(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        for t_name in instance._t_selectionmethod_names:
            func = getattr(instance, t_name)
            name = t_name[2:]
            d[name] = func

    def __iter__(self):
        hidden = self._i._hidden_actions
        return (k for k, v in self._d.iteritems()
                if (k not in hidden
                    and isselectionmethod(v)
                    )
                )


class EntityTransactions(NamespaceExtension):
    """A namespace of entity-level transactions."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        for t_name in instance._t_instancemethod_names:
            func = getattr(instance, t_name)
            name = t_name[2:]
            d[name] = func

    def __iter__(self):
        # Find hidden actions.
        instance = self._i
        hidden = instance._hidden_actions.copy()
        hidden_t_methods = getattr(instance, '_hidden_t_methods', None)
        if hidden_t_methods is not None:
            hidden.update(hidden_t_methods() or [])
        # Find instance methods.
        return (k for k, v in self._d.iteritems()
                if (k not in hidden
                    and not isselectionmethod(v)
                    )
                )

class EntityClassViews(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class EntityViews(NamespaceExtension):
    """A namespace of entity-level views."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, instance):
        NamespaceExtension.__init__(self, name, instance)
        d = self._d
        for v_name in instance._v_instancemethod_names:
            func = getattr(instance, v_name)
            name = v_name[2:]
            d[name] = func

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._i._hidden_views)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
