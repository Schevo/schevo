"""Fieldspec-related code.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.constant import UNASSIGNED
from schevo.label import label_from_name
from schevo.lib.odict import odict


class FieldMap(odict):
    """Field Mapping based on Ordered Dictionary."""

    __slots__ = ['_keys']

    def update_values(self, other):
        """Update field values based on field values in other FieldMap."""
        for name, field in other.iteritems():
            if name in self:
                f = self[name]
                if f.fget is None and not f.readonly:
                    # Only assign to non-readonly fields.
                    f.assign(field.get())

    def value_map(self):
        d = odict()
        for name, field in self.items():
            # Do not use field.get() here because we want the value to
            # be stored in the database, not the value that is exposed
            # to users.
            value = field._value
            d[name] = value
        return d


class FieldSpecMap(odict):
    """Field spec mapping based on Ordered Dictionary."""

    __slots__ = ['_keys']

    def field_map(self, instance=None, values={}):
        """Return a FieldMap based on field specifications."""
        pairs = [(name, FieldClass(instance, name,
                                   values.get(name, UNASSIGNED)))
                 for name, FieldClass in self.iteritems()]
        return FieldMap(pairs)
    

def field_spec_from_class(cls, dct):
    orig_spec = FieldSpecMap()
    if cls._field_spec:
        # Pass-through if it already has a field spec.  XXX: This
        # should actually use the original field spec and
        # append/modify it based on the class's spec.
        orig_spec = cls._field_spec.copy()
    spec = []
    for name, field_def in dct.items():
        if isinstance(field_def, FieldDefinition):
            field_def.name = name
            FieldClass = field_def.FieldClass
            if not FieldClass.label:
                # A label was not provided; determine one from the
                # field name.
                FieldClass.label = label_from_name(name)
            spec.append((field_def.counter, name, FieldClass))
            delattr(cls, name)
    spec.sort()
    spec = [s[1:] for s in spec]
    orig_spec.update(FieldSpecMap(spec))
    return orig_spec


class FieldDefinition(object):
    """A definition of a field attached to something.

    The order of FieldDefinition instance creation is kept for the
    purposes of creating ordered dictionaries of fields, etc.
    """

    __do_not_optimize__ = True

    BaseFieldClass = None
    _counter = 0

    def __init__(self, *args, **kw):
        self.name = None
        BaseFieldClass = self.BaseFieldClass
        class _Field(BaseFieldClass):
            pass
        _Field.BaseFieldClass = BaseFieldClass
        _Field._init_kw(kw)
        _Field._init_args(args)
        _Field._init_final()
        _Field.__name__ = BaseFieldClass.__name__
        self.FieldClass = _Field
        self.counter = FieldDefinition._counter
        FieldDefinition._counter += 1

    def __call__(self, fn):
        """For use as a decorator."""
        self.FieldClass.fget = (fn, )
        return self

    def field(self, instance=None, attribute=None, value=UNASSIGNED):
        FieldClass = self.FieldClass
        f = self.FieldClass(instance, attribute)
        f._value = value
        return f


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
