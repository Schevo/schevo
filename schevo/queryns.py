"""Query namespace classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import operator
import sys
from schevo.lib import optimize

from schevo import base
from schevo.constant import UNASSIGNED
import schevo.error
from schevo import field
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label, plural
from schevo.lib.odict import odict
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo.trace import log


class ParamChangeHandlers(NamespaceExtension):
    """A namespace of field change handlers."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, query):
        NamespaceExtension.__init__(self, name, query)
        d = self._d
        # Note: could be optimized via using a metaclass with
        # ParamQuery.
        for name in dir(query):
            if name.startswith('h_'):
                func = getattr(query, name)
                name = name[2:]
                d[name] = func


class ParamSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    def field_map(self, *filters):
        # Remove fields that should not be included.
        new_fields = self._i._field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        return FieldMap((field.name, field) for field in new_fields)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
