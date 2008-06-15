"""Fieldspec-related code.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from warnings import warn

from schevo.constant import UNASSIGNED
from schevo.label import label_from_name
from schevo.lib.odict import odict


class FieldMap(odict):
    """Field Mapping based on Ordered Dictionary."""

    __slots__ = ['_keys']

    def dump_map(self):
        """Return a dictionary of field_name:dumped_value pairs."""
        d = odict()
        for name, field in self.items():
            d[name] = field._dump()
        return d

    def related_entity_map(self):
        """Return a dictionary of field_name:related_entity_set pairs."""
        d = odict()
        for name, field in self.items():
            if field.may_store_entities:
                d[name] = field._entities_in_value()
        return d

    def update_values(self, other):
        """Update field values based on field values in other FieldMap."""
        for name, field in other.iteritems():
            if name in self:
                f = self[name]
                if f.fget is None and not f.readonly:
                    # Only assign to non-readonly fields.
                    f.set(field.get())

    def value_map(self):
        """Return a dictionary of field_name:field_value pairs."""
        d = odict()
        for name, field in self.items():
            # Do not use field.get() here because we want the value to
            # be stored in the database, not the value that is exposed
            # to users.
            #
            # XXX: Is this comment and implementation accurate
            # anymore, now that we use dump_map for that purpose?
            d[name] = field._value
        return d


class FieldSpecMap(odict):
    """Field spec mapping based on Ordered Dictionary."""

    __slots__ = ['_keys']

    def __call__(self, *filters):
        """Return FieldSpecMap instance based on self, filtered by optional
        callable objects specified in `filters`."""
        new_fields = self.iteritems()
        for filt in filters:
            new_fields = [
                (key, field) for key, field in new_fields
                if filt(field)
                ]
        return FieldSpecMap(new_fields)

    def field_map(self, instance=None, values={}):
        """Return a FieldMap based on field specifications."""
        pairs = [(name, FieldClass(instance=instance,
                                   value=values.get(name, UNASSIGNED)))
                 for name, FieldClass in self.iteritems()]
        return FieldMap(pairs)


def field_spec_from_class(cls, class_dict, slots=False):
    field_spec = FieldSpecMap()
    if cls._field_spec:
        # Make new subclasses of any inherited fields.
        for name, BaseFieldClass in cls._field_spec.iteritems():
            field_spec[name] = new_field_class(BaseFieldClass, slots)
    specs = []
    for name, field_def in class_dict.items():
        if isinstance(field_def, FieldDefinition):
            field_def.name = name
            BaseFieldClass = field_def.FieldClass
            NewClass = new_field_class(BaseFieldClass, slots)
            NewClass._name = name
            if not NewClass.label:
                NewClass.label = label_from_name(name)
            specs.append((field_def.counter, name, NewClass))
            if isinstance(getattr(cls, name, None), FieldDefinition):
                delattr(cls, name)
    specs.sort()
    specs = [s[1:] for s in specs]
    field_spec.update(FieldSpecMap(specs))
    return field_spec

def new_field_class(BaseFieldClass, slots):
    """Return a new field class subclassed from BaseFieldClass."""
    if slots:
        class NewClass(BaseFieldClass):
            # The field metaclass will assign __slots__.
            pass
    else:
        class NoSlotsField(BaseFieldClass):
            # The field metaclass will not assign __slots__ in order
            # to give flexibility to other users of this field, like
            # transactions and queries.
            pass
        NewClass = NoSlotsField
    NewClass.readonly = BaseFieldClass.readonly
    NewClass.__name__ = BaseFieldClass.__name__
    return NewClass


class FieldDefinition(object):
    """A definition of a field attached to something.

    The order of FieldDefinition instance creation is kept for the
    purposes of creating ordered dictionaries of fields, etc.
    """

    __do_not_optimize__ = True

    # The field class that this field definition class is based on.
    BaseFieldClass = None

    # "Global", class-level counter used for sorting after a series of
    # fields are defined.
    _counter = 0

    # Whether or not the name of this field definition class is
    # deprecated.  If it is deprecated, the user is given a DeprecationWarning
    # about the use of this name.
    _deprecated_name = False

    # If this class's name is deprecated, the preferred class name.
    _preferred_name = None

    def __init__(self, *args, **kw):
        self.name = None  # Set by field_spec_from_class().
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
        # Warn about name deprecation if this class's name is deprecated.
        if self._deprecated_name:
            msg = (
                '%r is a deprecated field definition name. '
                'Please replace with %r in your schemata.'
                % (self.__class__.__name__, self._preferred_name)
                )
            if not hasattr(sys, 'frozen'):
                warn(msg, DeprecationWarning, 2)
        # Warn about class deprecation if this class is deprecated.
        if _Field._deprecated_class:
            msg = (
                "%r is a deprecated field type.  "
                'See %s for more information.'
                % (self.__class__.__name__, _Field._deprecated_class_see_also)
                )
            if not hasattr(sys, 'frozen'):
                warn(msg, DeprecationWarning, 2)

    def __call__(self, fn):
        """For use as a decorator."""
        self.FieldClass.fget = (fn, )
        return self

    def field(self, name, instance=None, value=None):
        class NoSlotsField(self.FieldClass):
            # No __slots__ defined in order to give
            # flexibility to other users of this field, like
            # transactions and queries.
            pass
        NoSlotsField.__name__ = self.FieldClass.__name__
        NewClass = NoSlotsField
        NewClass._name = name
        if not NewClass.label:
            # Assign a label to the field based on the name.
            NewClass.label = label_from_name(name)
        f = NewClass(instance, value)
        return f


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
