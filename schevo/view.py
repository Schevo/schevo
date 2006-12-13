"""View classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.constant import UNASSIGNED
from schevo import field
from schevo.field import not_fget
from schevo.fieldspec import (
    FieldDefinition, FieldMap, FieldSpecMap, field_spec_from_class)
from schevo.label import label, label_from_name
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension


class View(base.View):
    """Views mimic the behavior of entities, while providing
    alternative information about them."""

    __metaclass__ = schema_metaclass('V')

    __slots__ = ['_entity', '_extent', '_field_map', '_oid',
                 'f', 'm', 'q', 'sys', 't', 'v', 'x']

    _field_spec = FieldSpecMap()

    _hidden_actions = set()
    _hidden_queries = set()

    def __init__(self, entity):
        self._entity = entity
        self._extent = entity._extent
        self._oid = entity._oid
        f_map = self._field_map = self._field_spec.field_map(instance=self)
        f_map.update_values(entity.sys.field_map(not_fget))
        self._setup(entity)
        # All fields should be readonly by default.
        for field in f_map.itervalues():
            field.readonly = True

    def _setup(self, entity):
        """Override this in subclasses to customize a view."""
        pass

    def __getattr__(self, name):
        if name == 'sys':
            self.sys = attr = ViewSys(self)
        elif name == 'f':
            self.f = attr = schevo.namespace.Fields(self)
        elif name == 'm' and self._entity is not None:
            self.m = attr = self._entity.m
        elif name == 'q' and self._entity is not None:
            self.q = attr = self._entity.q
        elif name == 't' and self._entity is not None:
            self.t = attr = ViewTransactions(self._entity, self)
        elif name == 'v' and self._entity is not None:
            self.v = attr = self._entity.v
        elif name == 'x':
            self.x = attr = ViewExtenders(self)
        elif name in self._field_map:
            attr = self._field_map[name].get()
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

    def __init__(self, view):
        NamespaceExtension.__init__(self)
        d = self._d
        cls = view.__class__
        x_names = []
        for attr in dir(cls):
            if attr.startswith('x_'):
                x_name = attr
                func = getattr(cls, x_name)
                if func.im_self is None:
                    x_names.append(x_name)
        for x_name in x_names:
            name = x_name[2:]
            func = getattr(view, x_name)
            d[name] = func


class ViewSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_view']

    def __init__(self, view):
        NamespaceExtension.__init__(self)
        self._view = view

    @property
    def entity(self):
        return self._view._entity

    def field_map(self, *filters):
        """Return field_map for the view, filtered by optional
        callable objects specified in `filters`."""
        # Remove fields that should not be included.
        new_fields = self._view._field_map.itervalues()
        for filt in filters:
            new_fields = (field for field in new_fields if filt(field))
        return FieldMap((field.name, field) for field in new_fields)

    @property
    def count(self):
        return self._view._entity.sys.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._view._entity.sys.exists

    @property
    def count(self):
        return self._view._entity.sys.count

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        return self._view._entity.sys.exists

    @property
    def extent(self):
        return self._view._entity.sys.extent

    @property
    def extent_name(self):
        return self.extent.name

    @property
    def links(self):
        return self._view._entity.sys.links

    @property
    def oid(self):
        return self._view._entity.sys.oid

    @property
    def rev(self):
        return self._view._entity.sys.rev


class ViewTransactions(NamespaceExtension):
    """A namespace of view-level transactions."""

    __slots__ = NamespaceExtension.__slots__ + ['_v']

    def __init__(self, entity, view):
        NamespaceExtension.__init__(self)
        d = self._d
        self._v = view
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
                if func.im_self is None:
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

    def __contains__(self, name):
        return name in self._d and name not in self._v._hidden_actions

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._v._hidden_actions)


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
