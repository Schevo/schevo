"""View classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.decorator import isclassmethod, isselectionmethod
from schevo.field import not_fget
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label_from_name
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension


class View(base.View):
    """Views mimic the behavior of entities, while providing
    alternative information about them."""

    __metaclass__ = schema_metaclass('V')

    __slots__ = ['_entity', '_extent', '_field_map', '_oid', '_rev',
                 'f', 'm', 'q', 'sys', 't', 'v', 'x']

    _field_spec = FieldSpecMap()

    _hidden_actions = None
    _hidden_queries = None
    _hidden_views = None

    def __init__(self, entity, *args, **kw):
        self._entity = entity
        self._extent = getattr(entity, '_extent', None)
        self._oid = getattr(entity, '_oid', 0)
        self._rev = getattr(entity, '_rev', 0)
        f_map = self._field_map = self._field_spec.field_map(instance=self)
        sys = getattr(entity, 'sys', None)
        if sys is not None:
            f_map.update_values(sys.field_map(not_fget))
        self._setup(entity, *args, **kw)
        # All fields should be readonly by default.
        for field in f_map.itervalues():
            field.readonly = True

    def _setup(self, entity, *args, **kw):
        """Override this in subclasses to customize a view."""
        pass

    def __getattr__(self, name):
        if name == 'sys':
            self.sys = attr = ViewSys('sys', self)
        elif name == 'f':
            self.f = attr = schevo.namespace.Fields('f', self)
        elif name == 'm' and self._entity is not None:
            self.m = attr = self._entity.m
        elif name == 'q' and self._entity is not None:
            self.q = attr = ViewQueries('q', self, self._entity)
        elif name == 't' and self._entity is not None:
            self.t = attr = ViewTransactions('t', self, self._entity)
        elif name == 'v' and self._entity is not None:
            self.v = attr = self._entity.v
        elif name == 'x':
            self.x = attr = ViewExtenders('x', self)
        elif name in self._field_map:
            attr = self._field_map[name].get_immutable()
        else:
            msg = 'Field %r does not exist on %r.' % (name, self)
            raise AttributeError(msg)
        return attr

    def __setattr__(self, name, value):
        if name == 'sys' or name.startswith('_') or len(name) == 1:
            return base.View.__setattr__(self, name, value)
        elif name in self._field_map:
            self._field_map[name].set(value)
        else:
            msg = 'Field %r does not exist on %r.' % (name, self)
            raise AttributeError(msg)

    def __str__(self):
        return str(self._entity)

    def __unicode__(self):
        return unicode(self._entity)


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
                if not isclassmethod(func):
                    x_names.append(x_name)
        for x_name in x_names:
            name = x_name[2:]
            func = getattr(view, x_name)
            d[name] = func


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
        return self._i._entity.sys.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._i._entity.sys.exists

    @property
    def count(self):
        return self._i._entity.sys.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._i._entity.sys.exists

    @property
    def extent(self):
        return self._i._entity.sys.extent

    @property
    def extent_name(self):
        return self.extent.name

    @property
    def links(self):
        return self._i._entity.sys.links

    @property
    def oid(self):
        return self._i._entity.sys.oid

    @property
    def rev(self):
        return self._i._entity.sys.rev


class ViewTransactions(NamespaceExtension):
    """A namespace of view-level transactions."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view, entity):
        NamespaceExtension.__init__(self, name, view)
        d = self._d
        # Start with the actions defined on the entity.
        for t_name in entity._t_names:
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
                if not isclassmethod(func):
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


class ViewQueries(NamespaceExtension):
    """A namespace of view-level queries."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, name, view, entity):
        NamespaceExtension.__init__(self, name, view)
        d = self._d
        # Start with the actions defined on the entity.
        for q_name in entity._q_names:
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
                if not isclassmethod(func):
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
