"""View namespace classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo import base
from schevo.field import not_fget
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.introspect import isselectionmethod
from schevo.label import label_from_name
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension, namespaceproperty


class ViewClassExtenders(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class ViewExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, view):
        NamespaceExtension.__init__(self, name, view)
        d = self._d
        cls = view.__class__
        x_names = []
        for attr in dir(cls):
            if attr.startswith('x_'):
                x_name = attr
                func = getattr(cls, x_name)
                x_names.append(x_name)
        for x_name in x_names:
            name = x_name[2:]
            func = getattr(view, x_name)
            d[name] = func


class ViewClassFields(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class ViewOneToMany(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view):
        NamespaceExtension.__init__(self, name, view)
        # Copy one-to-many methods from the view's entity to the view
        # itself.
        self._d.update(view._entity.v._d)


class ViewClassQueries(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class ViewQueries(NamespaceExtension):
    """A namespace of view-level queries."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view):
        NamespaceExtension.__init__(self, name, view)
        d = self._d
        entity = view._entity
        # Start with the actions defined on the entity.
        for q_name in entity._q_instancemethod_names:
            func = getattr(entity, q_name)
            name = q_name[2:]
            d[name] = func
        # The add or override with actions defined on the view.
        cls = view.__class__
        q_names = []
        for attr in dir(cls):
            if attr.startswith('q_'):
                q_name = attr
                func = getattr(cls, q_name)
                q_names.append(q_name)
        for q_name in q_names:
            name = q_name[2:]
            func = getattr(view, q_name)
            # Assign a label if none exists.
            new_label = None
            if getattr(func, '_label', None) is None:
                new_label = label_from_name(name)
                if new_label is not None:
                    cls.__dict__[q_name]._label = new_label
            d[name] = func

    def __iter__(self):
        if self._i._hidden_queries is None:
            hidden_queries = self._i._entity._hidden_queries
        else:
            hidden_queries = self._i._hidden_queries
        return (k for k in self._d.iterkeys()
                if k not in hidden_queries)


class ViewSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    @property
    def entity(self):
        return self._i._entity

    def field_map(self, *filters):
        """Return field_map for the view, filtered by optional
        callable objects specified in `filters`."""
        # Remove fields that should not be included.
        new_fields = self._i._field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        return FieldMap((field.name, field) for field in new_fields)

    @property
    def count(self):
        return self._i._entity.s.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._i._entity.s.exists

    @property
    def count(self):
        return self._i._entity.s.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._i._entity.s.exists

    @property
    def extent(self):
        return self._i._entity.s.extent

    @property
    def extent_name(self):
        return self.extent.name

    @property
    def links(self):
        return self._i._entity.s.links

    @property
    def oid(self):
        return self._i._entity.s.oid

    @property
    def rev(self):
        return self._i._entity.s.rev


class ViewClassTransactions(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, cls):
        NamespaceExtension.__init__(self, name, cls)
        for key in dir(cls):
            if key.startswith('t_'):
                method = getattr(cls, key)
                if isselectionmethod(method):
                    name = key[2:]
                    self._set(name, method)


class ViewTransactions(NamespaceExtension):
    """A namespace of view-level transactions."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view):
        NamespaceExtension.__init__(self, name, view)
        d = self._d
        # Start with the actions defined on the entity.
        entity = view._entity
        if entity is not None:
            for t_name in entity._t_instancemethod_names:
                func = getattr(entity, t_name)
                name = t_name[2:]
                d[name] = func
        # The add or override with actions defined on the view.
        cls = view.__class__
        t_names = []
        for attr in dir(cls):
            if attr.startswith('t_'):
                t_name = attr
                func = getattr(cls, t_name)
                t_names.append(t_name)
        for t_name in t_names:
            name = t_name[2:]
            func = getattr(view, t_name)
            # Assign a label if none exists.
            new_label = None
            if getattr(func, '_label', None) is None:
                new_label = label_from_name(name)
                if new_label is not None:
                    cls.__dict__[t_name]._label = new_label
            d[name] = func

    def __iter__(self):
        hidden = self._hidden_actions()
        return (k for k, v in self._d.iteritems()
                if (k not in hidden
                    and not isselectionmethod(v)
                    )
                )

    def _hidden_actions(self):
        view = self._i
        if view._hidden_actions is not None:
            # Use view's _hidden_actions if available.
            hidden = view._hidden_actions.copy()
        else:
            # Fall back to entity's.
            hidden = view._entity._hidden_actions.copy()
        # Use view's _hidden_t_methods if available.
        hidden_t_methods = getattr(view, '_hidden_t_methods', None)
        # Fall back to entity's.
        if hidden_t_methods is None:
            hidden_t_methods = getattr(view._entity, '_hidden_t_methods', None)
        # Combine _hidden_t_methods results with _hidden_actions.
        if hidden_t_methods is not None:
            hidden.update(hidden_t_methods() or [])
        return hidden


class ViewClassViews(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__


class ViewViews(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view):
        NamespaceExtension.__init__(self, name, view)
        # Copy view methods from the view's entity to the view itself.
        self._d.update(view._entity.v._d)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
