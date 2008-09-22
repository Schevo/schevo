"""View classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.decorator import isclassmethod, isselectionmethod
from schevo.field import not_fget
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label_from_name, LabelMixin
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension, namespaceproperty
from schevo import viewns


class View(base.View):
    """Views mimic the behavior of entities, while providing
    alternative information about them."""

    __metaclass__ = schema_metaclass('V')

    __slots__ = LabelMixin.__slots__ + [
        '_entity', '_extent', '_field_map', '_oid', '_rev',
        '_f', '_m', '_q', '_sys', '_t', '_v', '_x']

    # Namespaces.
    sys = namespaceproperty('sys', instance=viewns.ViewSys)
    f = namespaceproperty('f', cls=viewns.ViewClassFields,
                          instance=schevo.namespace.Fields)
    m = namespaceproperty('m', instance=viewns.ViewOneToMany)
    q = namespaceproperty('q', cls=viewns.ViewClassQueries,
                          instance=viewns.ViewQueries)
    t = namespaceproperty('t', cls=viewns.ViewClassTransactions,
                          instance=viewns.ViewTransactions)
    v = namespaceproperty('v', cls=viewns.ViewClassViews,
                          instance=viewns.ViewViews)
    x = namespaceproperty('x', cls=viewns.ViewClassExtenders,
                          instance=viewns.ViewExtenders)

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
        if name in self._field_map:
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
