"""Namespace extension classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from warnings import warn

from schevo import base
from schevo.fieldspec import FieldDefinition
from schevo.label import label_from_name


# Global objects used during Schevo schema loading.
EVOLVING = False
SCHEMADEF = None
SCHEMADB = None


class SchemaDefinition(object):
    """Keeps track of information about a schema during import."""

    def __init__(self):
        self.E = EntityClasses('E', self)
        self.F = FieldClasses('F', self)
        self.f = FieldConstructors('f', self)
        self.Q = QueryClasses('Q', self)
        self.q = DatabaseQueries('q', self)
        self.T = TransactionClasses('T', self)
        self.t = DatabaseTransactions('t', self)
        self.V = ViewClasses('V', self)
        self.relationships = {}


class namespaceproperty(object):

    def __init__(self, name, cls=None, instance=None, deprecated=False):
        self.name = name
        self.cls_class = cls
        self.instance_class = instance
        self.deprecated = deprecated
        self.prefixed_name_cls = '__' + name
        self.prefixed_name_instance = '_' + name

    def __get__(self, instance, owner):
        if self.deprecated:
            warning = "'sys' namespace is deprecated; use 's' instead."
            warn(warning, DeprecationWarning, 2)
        namespace = None
        if instance is None and self.cls_class is not None:
            # Create the class namespace if needed, then return it.
            name = self.prefixed_name_cls
            namespace = getattr(owner, name, None)
            if namespace is None:
                namespace = self.cls_class(self.name, owner)
                setattr(owner, name, namespace)
        elif instance is not None:
            # Create the instance namespace if needed, then return it.
            name = self.prefixed_name_instance
            namespace = getattr(instance, name, None)
            if namespace is None:
                namespace = self.instance_class(self.name, instance)
                setattr(instance, name, namespace)
        return namespace


class Fields(object):
    """A namespace that gives attribute access to an object's field
    instances."""

    def __init__(self, name, obj):
        d = self.__dict__
        d['_n'] = name
        d['_i'] = obj

    def __delattr__(self, name):
        f = self._i._field_map
        if name not in f:
            raise AttributeError(name)
        del f[name]

    __delitem__ = __delattr__

    def __getattr__(self, name):
        return self._i._field_map[name]

    __getitem__ = __getattr__

    def __iter__(self):
        return iter(self._i._field_map)

    def __length_hint__(self):
        return len(self._i._field_map)

    def __repr__(self):
        return '<%r namespace on %r>' % (self._n, self._i)

    def __setattr__(self, name, value):
        field_map = self._i._field_map
        if name in field_map:
            raise AttributeError('%r already exists.' % name)
        if isinstance(value, FieldDefinition):
            value = value.field(name=name, instance=self._i)
        elif isinstance(value, base.Field):
            value._instance = self._i
            if not value.label:
                # Assign a label to the field based on the name.
                value.label = label_from_name(name)
        else:
            msg = '%r is not a Field or FieldDefinition instance.' % value
            raise ValueError(msg)
        field_map[name] = value

    __setitem__ = __setattr__

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(self._i._field_map.keys())


class NamespaceExtension(object):
    """A namespace extension with index syntax support."""

    __slots__ = [
        '_d',                         # Dictionary of stored key/value pairs.
        '_i',                         # Instance or class attached to.
        '_n',                         # Name of namespace.
        ]

    _readonly = True

    def __init__(self, name, instance):
        self._d = {}
        self._n = name
        self._i = instance

    def __getattr__(self, name):
        try:
            return self._d[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        return self._d[name]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __repr__(self):
        return '<%r namespace on %r>' % (self._n, self._i)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        elif self._readonly:
            msg = 'Readonly namespace, cannot set %r to %r.' % (name, value)
            raise AttributeError(msg)
        else:
            self._d[name] = value

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(self._d.keys())

    def _set(self, name, value):
        """Backdoor method to set `name` to `value`."""
        self._d[name] = value


class DatabaseQueries(NamespaceExtension):
    """A namespace of database-level queries."""
    __slots__ = NamespaceExtension.__slots__


class DatabaseTransactions(NamespaceExtension):
    """A namespace of database-level transactions."""
    __slots__ = NamespaceExtension.__slots__


class EntityClasses(NamespaceExtension):
    """A namespace of Entity classes."""
    __slots__ = NamespaceExtension.__slots__ + ['Entity']


class FieldClasses(NamespaceExtension):
    """A namespace of field classes."""
    __slots__ = NamespaceExtension.__slots__


class FieldConstructors(NamespaceExtension):
    """A namespace of field constructor factories."""
    __slots__ = NamespaceExtension.__slots__


class QueryClasses(NamespaceExtension):
    """A namespace of query classes."""
    __slots__ = NamespaceExtension.__slots__


class TransactionClasses(NamespaceExtension):
    """A namespace of transaction classes."""
    __slots__ = NamespaceExtension.__slots__


class ViewClasses(NamespaceExtension):
    """A namespace of view classes."""
    __slots__ = NamespaceExtension.__slots__


optimize.bind_all(sys.modules[__name__])  # Last line of module.
