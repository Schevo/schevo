"""View classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo import base
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
        '_f', '_m', '_q', '_s', '_t', '_v', '_x']

    # Namespaces.
    f = namespaceproperty('f', cls=viewns.ViewClassFields,
                          instance=schevo.namespace.Fields)
    m = namespaceproperty('m', instance=viewns.ViewOneToMany)
    q = namespaceproperty('q', cls=viewns.ViewClassQueries,
                          instance=viewns.ViewQueries)
    s = namespaceproperty('s', instance=viewns.ViewSys)
    t = namespaceproperty('t', cls=viewns.ViewClassTransactions,
                          instance=viewns.ViewTransactions)
    v = namespaceproperty('v', cls=viewns.ViewClassViews,
                          instance=viewns.ViewViews)
    x = namespaceproperty('x', cls=viewns.ViewClassExtenders,
                          instance=viewns.ViewExtenders)

    # Deprecated namespaces.
    sys = namespaceproperty('s', instance=viewns.ViewSys, deprecated=True)

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
        s = getattr(entity, 's', None)
        if s is not None:
            f_map.update_values(s.field_map(not_fget))
        self._setup(entity, *args, **kw)
        # All fields should be readonly by default.
        for field in f_map.itervalues():
            field.readonly = True

    def _setup(self, entity, *args, **kw):
        """Override this in subclasses to customize a view."""
        pass

    def __getattr__(self, name):
        try:
            return self._field_map[name].get_immutable()
        except KeyError:
            msg = 'Field %r does not exist on %r.' % (name, self)
            raise AttributeError(msg)

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
