"""Entity class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from string import digits, ascii_letters
import inspect

from schevo import base
from schevo.constant import UNASSIGNED
from schevo.error import (
    EntityDoesNotExist, ExtentDoesNotExist, FieldDoesNotExist, KeyIndexOverlap)
from schevo.fieldspec import field_spec_from_class
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import (
    LabelMixin, label_from_name, plural_from_name, relabel, with_label)
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo import query
from schevo import transaction
from schevo import view


# extentmethod provides support for decorating methods of entity
# classes as belonging to the extent, not the entity.
def extentmethod(fn):
    def outer_fn(cls, *args, **kw):
        return fn(cls._extent, *args, **kw)
    if hasattr(fn, '_label'):
        _plural = getattr(fn, '_plural', None)
        decorator = with_label(fn._label, _plural)
        outer_fn = decorator(outer_fn)
    outer_fn = classmethod(outer_fn)
    return outer_fn


class EntityMeta(type):
    """Convert field definitions to a field specification ordered
    dictionary."""

    def __new__(cls, class_name, bases, class_dict):
        # Only do something if creating an Entity subclass.
        if class_name != 'Entity':
            class_dict['__slots__'] = bases[0].__slots__
        return type.__new__(cls, class_name, bases, class_dict)

    def __init__(cls, class_name, bases, class_dict):
        # Only do something if creating a subclass of Entity.
        type.__init__(cls, class_name, bases, class_dict)
        if class_name == 'Entity':
            return
        # If the class specifies an actual name, use that instead.
        if '_actual_name' in class_dict:
            class_name = cls._actual_name
            cls.__name__ = class_name
        # Create the field spec.
        field_spec = cls._field_spec = field_spec_from_class(
            cls, class_dict, slots=True)
        field_spec.reorder_all()
        # Setup fields, keeping track of calculated (fget) fields.
        cls.setup_fields()
        # Get slotless specs for queries, transactions and views.
        spec = field_spec_from_class(cls, class_dict)
        q_spec = spec.copy()
        t_spec = spec.copy()
        v_spec = spec.copy()
        # Transactions and the default query don't normally need fget
        # fields, so hide them by default in those contexts.
        for field_name in cls._fget_fields:
            q_spec[field_name].hidden = True
            t_spec[field_name].hidden = True
        # Generic Update (for use by cascading delete).  Assigned in
        # this metaclass to prevent subclasses from overriding.
        class _GenericUpdate(transaction.Update):
            _call_change_handlers_on_init = False
            _EntityClass = cls
            _extent_name = class_name
            _fget_fields = cls._fget_fields
            _field_spec = t_spec.copy()
        cls._GenericUpdate = _GenericUpdate
        if not class_name.startswith('_'):
            # Setup standard transaction classes (Create, Delete, Update).
            cls.setup_transactions(class_name, class_dict, t_spec)
            # Setup view classes.
            cls.setup_views(class_name, bases, class_dict, v_spec)
        # Normalize hidden information.
        cls._hidden_actions = set(cls._hidden_actions)
        cls._hidden_queries = set(cls._hidden_queries)
        cls._hidden_views = set(cls._hidden_views)
        # Setup key spec.
        cls.setup_key_spec()
        # Setup index spec.
        cls.setup_index_spec()
        # Keep them from clashing.
        cls.validate_key_and_index_specs()
        if not class_name.startswith('_'):
            # Assign labels if class name is "public".
            cls.assign_labels(class_name, class_dict)
        # Remember queries for the EntityQueries namespace.
        cls._q_names = cls.get_method_names('q_')
        # Remember transactions for the EntityTransactions namespace.
        cls._t_names = cls.get_method_names('t_')
        # Remember views for the EntityViews namespace.
        cls._v_names = cls.get_method_names('v_')
        # Remember x_methods for the EntityExtenders namespace.
        cls._x_names = cls.get_method_names('x_')
        # Add this class to the schema.
        cls.update_schema(class_name)

    def assign_labels(cls, class_name, class_dict):
        # Assign labels for the class/extent.
        if '_label' not in class_dict and not hasattr(cls, '_label'):
            cls._label = label_from_name(class_name)
        if '_plural' not in class_dict and not hasattr(cls, '_plural'):
            cls._plural = plural_from_name(class_name)
        # Assign labels for query, transaction, and view methods.
        for key in class_dict:
            if key[:2] in ('q_', 't_', 'v_'):
                m_name = key
                func = getattr(cls, m_name)
                # Drop the prefix.
                method_name = m_name[2:]
                # Assign a label if none exists.
                new_label = None
                if getattr(func, '_label', None) is None:
                    # Make a label after dropping prefix.
                    new_label = label_from_name(method_name)
                if func.im_self == cls:
                    # Classmethod.
                    if new_label is not None:
                        func.im_func._label = new_label
                else:
                    # Instancemethod.
                    if new_label is not None:
                        class_dict[m_name]._label = new_label

    def get_method_names(cls, prefix):
        """Return list of method names that start with prefix."""
        names = []
        for name in dir(cls):
            if name.startswith(prefix):
                func = getattr(cls, name)
                if func.im_self is None:
                    names.append(name)
        return names

    def setup_fields(cls):
        fget_fields = []
        for field_name, FieldClass in cls._field_spec.iteritems():
            fget = FieldClass.fget
            if fget is not None:
                fget_fields.append(field_name)
                def get_field_value(self, fget=fget[0]):
                    return fget(self)
            else:
                field = FieldClass(instance=None)
                def get_field_value(self, field_name=field_name, field=field):
                    """Get the field value from the database."""
                    db = self._db
                    extent_name = self._extent.name
                    oid = self._oid
                    try:
                        value = db._entity_field(extent_name, oid, field_name)
                    except EntityDoesNotExist:
                        raise
                    except KeyError:  # XXX This needs to be more specific.
                        value = UNASSIGNED
                    field._value = value
                    field._restore(db)
                    return field.get_immutable()
            setattr(cls, field_name, property(fget=get_field_value))
        cls._fget_fields = tuple(fget_fields)

    def setup_index_spec(cls):
        # Create the index spec.
        index_set = set(cls._index_spec)
        for s in cls._index_spec_additions:
            # Get just the names from field definitions.
            # Note that field_def could be a string.
            names = tuple(getattr(field_def, 'name', field_def)
                          for field_def in s)
            index_set.add(names)
        cls._index_spec = tuple(index_set)
        cls._index_spec_additions = ()

    def setup_key_spec(cls):
        # Create the key spec.
        key_set = set(cls._key_spec)
        for s in cls._key_spec_additions:
            # Get just the names from field definitions.
            # Note that field_def could be a string.
            names = tuple(getattr(field_def, 'name', field_def)
                          for field_def in s)
            key_set.add(names)
            # The first key becomes the default key.
            if cls._default_key is None:
                cls._default_key = names
        cls._key_spec = tuple(key_set)
        cls._key_spec_additions = ()

    def setup_transactions(cls, class_name, class_dict, t_spec):
        """Create standard transaction classes."""
        # Fields in a transaction class defined in the schema appear
        # below the fields that come from the entity field spec.
        for name in dir(cls):
            OldClass = getattr(cls, name)
            if not isinstance(OldClass, type):
                continue
            if not issubclass(OldClass, (transaction.Create,
                                         transaction.Delete,
                                         transaction.Update)):
                continue
            NewClass = type(name, (OldClass,), {})
            NewClass._EntityClass = cls
            NewClass._extent_name = class_name
            NewClass._fget_fields = cls._fget_fields
            field_spec = NewClass._field_spec = t_spec.copy()
            field_spec.update(OldClass._field_spec, reorder=True)
            field_spec.reorder_all()
            # Perform any class-level initialization.
            if hasattr(NewClass, '_init_class'):
                NewClass._init_class()
            setattr(cls, name, NewClass)

    def setup_views(cls, class_name, bases, class_dict, v_spec):
        # Create subclasses of any View class defined in a base class
        # and not already locally subclassed.
        for parent in reversed(bases):
            for name, attr in parent.__dict__.iteritems():
                if (name not in class_dict and
                    inspect.isclass(attr) and issubclass(attr, base.View)):
                    ViewClass = type(name, (attr,), {})
                    ViewClass._label = attr._label
                    setattr(cls, name, ViewClass)
        # Set properties on all View classes.
        for name, attr in cls.__dict__.iteritems():
            if inspect.isclass(attr) and issubclass(attr, base.View):
                ViewClass = attr
                ViewClass._EntityClass = cls
                ViewClass._extent_name = class_name
                ViewClass._hidden_actions = set(cls._hidden_actions)
                ViewClass._hidden_queries = set(cls._hidden_queries)
                # Acquire field specs from the host entity class.
                base_spec = ViewClass._field_spec
                ViewClass._fget_fields = cls._fget_fields
                ViewClass._field_spec = v_spec.copy()
                ViewClass._field_spec.update(base_spec, reorder=True)
                ViewClass._field_spec.reorder_all()
                if hasattr(ViewClass, '_init_class'):
                    ViewClass._init_class()

    def update_schema(cls, class_name):
        # Only if this global schema definition variable exists, and
        # this class applies to the current evolution context.
        if (schevo.namespace.SCHEMADEF is not None
            and (schevo.namespace.EVOLVING or not cls._evolve_only)):
            # Add this class to the entity classes namespace.
            schevo.namespace.SCHEMADEF.E._set(class_name, cls)
            # Keep track of relationship metadata, except when it is a
            # private entity class.  (Private base classes are not
            # turned into extents.)
            if not class_name.startswith('_'):
                relationships = schevo.namespace.SCHEMADEF.relationships
                for field_name, FieldClass in cls._field_spec.iteritems():
                    if (hasattr(FieldClass, 'allow') and
                        field_name not in cls._fget_fields):
                        for entity_name in FieldClass.allow:
                            spec = relationships.setdefault(entity_name, [])
                            spec.append((class_name, field_name))

    def validate_key_and_index_specs(cls):
        """Raise a `KeyIndexOverlap` if there are any shared key/index specs."""
        key_set = set(cls._key_spec)
        index_set = set(cls._index_spec)
        duplicates = key_set.intersection(index_set)
        if len(duplicates):
            raise KeyIndexOverlap(cls.__name__, duplicates)


class Entity(base.Entity, LabelMixin):

    __metaclass__ = EntityMeta

    __slots__ = LabelMixin.__slots__ + ['_oid', 'sys',
                                        'f', 'm', 'q', 't', 'v', 'x']

    # The actual class/extent name to use for this Entity type.
    _actual_name = None

    # The database instance associated with this Entity type.
    _db = None

    # The first _key() specification defined.
    _default_key = None

    # True if the class definition should only be valid during schema
    # evolution.
    _evolve_only = False

    # The extent associated with this Entity type.
    _extent = None

    # Field specification for this type of Entity.
    _field_spec = FieldSpecMap()

    # True if typically hidden from a top-level view of the database
    # in a UI.
    _hidden = False

    # Sets of hidden transaction, query, and view methods.
    #
    # XXX: _hidden_* defaults in schevo.schema.hide function are used
    # XXX: if _hide is called during Entity subclass creation.
    _hidden_actions = set(['create_if_necessary', 'generic_update'])
    _hidden_queries = set([])
    _hidden_views = set()

    # Index specifications for the related extent.
    _index_spec = ()
    _index_spec_additions = ()          # Used during subclassing.

    # Initial entity instances to create in a new database.
    _initial = []

    # The priority in which these initial values should be created.  A
    # higher priority indicates earlier execution.
    _initial_priority = 0

    # Key specifications for the related extent.
    _key_spec = ()
    _key_spec_additions = ()            # Used during subclassing.

    # Relationships between this Entity type and other Entity types.
    _relationships = []

    # Sample entity instances to optionally create in a new database.
    _sample = []

    # Name of the class in the previous schema version, or None if not
    # being renamed.
    _was = None

    # Names of query, transaction, view, and extender methods
    # applicable to entity instances.
    _q_names = []
    _t_names = []
    _v_names = []
    _x_names = []

    def __init__(self, oid):
        self._oid = oid

    def __cmp__(self, other):
        if other is UNASSIGNED:
            return 1
        if other.__class__ is self.__class__:
            if self._default_key:
                key = self._default_key
                return cmp([getattr(self, fieldname) for fieldname in key],
                           [getattr(other, fieldname) for fieldname in key])
            else:
                return cmp(self._oid, other._oid)
        else:
            return cmp(hash(self), hash(other))

    def __eq__(self, other):
        try:
            return (self._extent is other._extent and self._oid == other._oid)
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __getattr__(self, name):
        if name == 'sys':
            self.sys = attr = EntitySys(self)
        elif name == 'f':
            self.f = attr = EntityFields(self)
        elif name == 'm':
            self.m = attr = EntityOneToMany(self)
        elif name == 'q':
            self.q = attr = EntityQueries(self)
        elif name == 't':
            self.t = attr = EntityTransactions(self)
        elif name == 'v':
            self.v = attr = EntityViews(self)
        elif name == 'x':
            self.x = attr = EntityExtenders(self)
        else:
            msg = 'Field %r does not exist on %r.' % (name, self._extent.name)
            raise AttributeError(msg)
        return attr

    def __hash__(self):
        return hash((self._extent, self._oid))

    def __repr__(self):
        oid = self._oid
        extent = self._extent
        if oid not in extent:
            return '<%s entity oid:%i rev:DELETED>' % (extent.name, oid)
        else:
            rev = self._rev
            return '<%s entity oid:%i rev:%i>' % (extent.name, oid, rev)

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        key = self._default_key
        if key:
            return u' :: '.join([unicode(getattr(self.f, name))
                                 for name in key])
        else:
            return repr(self)

    @extentmethod
    @with_label(u'Exact Matches')
    def q_exact(extent, **kw):
        """Return a simple parameterized query for finding instances
        using the extent's ``find`` method."""
        return query.Exact(extent, **kw)

    @extentmethod
    @with_label(u'By Example')
    def q_by_example(extent, **kw):
        """Return an extensible query for finding instances, built
        upon Match and Intersection queries."""
        q = query.ByExample(extent, **kw)
        return q

    @classmethod
    @with_label(u'Create')
    def t_create(cls, *args, **kw):
        """Return a Create transaction."""
        tx = cls._Create(*args, **kw)
        return tx

    @classmethod
    @with_label(u'Create If Necessary')
    def t_create_if_necessary(cls, *args, **kw):
        """Return a Create transaction that creates if necessary."""
        tx = cls._Create(*args, **kw)
        tx._style = transaction._Create_If_Necessary
        return tx

    @with_label(u'Clone')
    def t_clone(self):
        """Return a Clone transaction."""
        # First create a Create transaction based on this entity's
        # fields.
        tx = self._Create(self)
        # Relabel the transaction.
        relabel(tx, 'Clone')
        return tx

    @with_label(u'Delete')
    def t_delete(self):
        """Return a Delete transaction."""
        tx = self._Delete(self)
        return tx

    @with_label(u'Generic Update')
    def t_generic_update(self, **kw):
        """Return a Generic Update transaction."""
        tx = self._GenericUpdate(self, **kw)
        return tx

    @with_label(u'Update')
    def t_update(self, **kw):
        """Return an Update transaction."""
        tx = self._Update(self, **kw)
        return tx

    @with_label(u'View')
    def v_default(self):
        """Return the Default view."""
        return self._DefaultView(self)

    @property
    def _rev(self):
        """Return the revision number of the entity."""
        return self._db._entity_rev(self._extent.name, self._oid)

    class _Create(transaction.Create):
        pass

    class _Delete(transaction.Delete):
        pass

    class _Update(transaction.Update):
        pass

    class _DefaultView(view.View):
        _label = u'View'


class EntityExtenders(NamespaceExtension):
    """A namespace of entity-level methods."""

    __slots__ = NamespaceExtension.__slots__

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        for x_name in entity._x_names:
            func = getattr(entity, x_name)
            name = x_name[2:]
            d[name] = func


class EntityFields(object):

    __slots__ = ['_entity']

    def __init__(self, entity):
        self._entity = entity

    def __getattr__(self, name):
        e = self._entity
        FieldClass = e._field_spec[name]
        field = FieldClass(e, getattr(e, name))
        return field

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __iter__(self):
        return iter(self._entity._field_spec)

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(iter(self))


class EntityOneToMany(NamespaceExtension):
    """A namespace of entity-level methods."""

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        e = entity
        db = e._db
        extent_name = e._extent.name
        oid = e._oid
        last_extent_name = ''
        for other_extent_name, other_field_name in e._extent.relationships:
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


class EntityQueries(NamespaceExtension):
    """A namespace of entity-level queries."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for q_name in entity._q_names:
            func = getattr(entity, q_name)
            name = q_name[2:]
            d[name] = func

    def __contains__(self, name):
        return name in self._d and name not in self._e._hidden_queries

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._e._hidden_queries)


class EntitySys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_entity']

    def __init__(self, entity):
        """Create a sys namespace for the `entity`."""
        NamespaceExtension.__init__(self)
        self._entity = entity

    def as_data(self):
        """Return tuple of entity values in a form suitable for
        initial or sample data in a schema."""
        def resolve(entity, fieldname):
            field = entity.f[fieldname]
            value = getattr(entity, fieldname)
            if isinstance(value, Entity):
                entity = value
                values = []
                for fieldname in entity.sys.extent.default_key:
                    value = resolve(entity, fieldname)
                    values.append(value)
                if len(field.allow) > 1:
                    values = (entity.sys.extent.name, tuple(values))
                return tuple(values)
            else:
                return value
        values = []
        create = self._entity.t_create()
        e = self._entity
        for f_name in e.f:
            if (f_name not in create.f
                or create.f[f_name].hidden or create.f[f_name].readonly):
                # Don't include a field that doesn't exist in the
                # create transaction, or is hidden or readonly.
                continue
            f = e.f[f_name]
            if f.fget is not None or f.hidden:
                pass
            else:
                value = resolve(e, f_name)
                values.append(value)
        return tuple(values)

    def count(self, other_extent_name=None, other_field_name=None):
        """Return count of all links, or specific links if
        `other_extent_name` and `other_field_name` are supplied."""
        e = self._entity
        return e._db._entity_links(e._extent.name, e._oid, other_extent_name,
                                   other_field_name, return_count=True)

    @property
    def db(self):
        """Return the database to which this entity belongs."""
        return self._entity._db

    @property
    def exists(self):
        """Return True if the entity exists; False if it was deleted."""
        entity = self._entity
        oid = entity._oid
        extent = entity._extent
        return oid in extent

    @property
    def extent(self):
        """Return the extent to which this entity belongs."""
        return self._entity._extent

    @property
    def extent_name(self):
        """Return the name of the extent to which this entity belongs."""
        return self._entity._extent.name

    def field_map(self, *filters):
        """Return field_map for the entity, filtered by optional
        callable objects specified in `filters`."""
        e = self._entity
        db = e._db
        stored_values = e._db._entity_fields(e._extent.name, e._oid)
        entity_field_map = e._field_spec.field_map(e, stored_values)
        # Remove fields that should not be included.
        new_fields = entity_field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        entity_field_map = FieldMap(
            (field.name, field) for field in new_fields)
        for field in entity_field_map.itervalues():
            if field.fget is not None:
                # Update fields that have fget callables.
                value = field.fget[0](e)
            else:
                # Allow fields to restore themselves from a stored
                # value.
                field._restore(db)
        return entity_field_map

    def links(self, other_extent_name=None, other_field_name=None):
        """Return dictionary of (extent_name, field_name): entity_list
        pairs, or list of linking entities if `other_extent_name` and
        `other_field_name` are supplied."""
        e = self._entity
        return e._db._entity_links(e._extent.name, e._oid,
                                   other_extent_name, other_field_name)

    def links_filter(self, other_extent_name, other_field_name):
        """Return a callable that returns the current list of linking
        entities whenever called."""
        db = self._entity._db
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
        return self._entity._oid

    @property
    def rev(self):
        """Return the revision number of the entity."""
        return self._entity._rev


class EntityTransactions(NamespaceExtension):
    """A namespace of entity-level transactions."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for t_name in entity._t_names:
            func = getattr(entity, t_name)
            name = t_name[2:]
            d[name] = func

    def __contains__(self, name):
        return name in self._d and name not in self._e._hidden_actions

    def __iter__(self):
        entity = self._e
        hidden = entity._hidden_actions.copy()
        hidden_t_methods = getattr(entity, '_hidden_t_methods', None)
        if hidden_t_methods is not None:
            hidden.update(hidden_t_methods() or [])
        return (k for k in self._d.iterkeys() if k not in hidden)


class EntityViews(NamespaceExtension):
    """A namespace of entity-level views."""

    __slots__ = NamespaceExtension.__slots__ + ['_e']

    def __init__(self, entity):
        NamespaceExtension.__init__(self)
        d = self._d
        self._e = entity
        for v_name in entity._v_names:
            func = getattr(entity, v_name)
            name = v_name[2:]
            d[name] = func

    def __contains__(self, name):
        return name in self._d and name not in self._e._hidden_views

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._e._hidden_views)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2007 Orbtech, L.L.C. and contributors
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
