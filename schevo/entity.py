"""Entity class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from string import digits, ascii_letters

from schevo import base
from schevo.constant import UNASSIGNED
from schevo.error import (
    EntityDoesNotExist, ExtentDoesNotExist, FieldDoesNotExist)
from schevo.fieldspec import field_spec_from_class
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import (
    LabelMixin, label_from_name, plural_from_name, with_label)
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
        # Only do something if creating an Entity subclass.
        type.__init__(cls, class_name, bases, class_dict)
        if class_name == 'Entity':
            return
        # If the class has an actual name, use that instead.
        if '_actual_name' in class_dict:
            class_name = cls._actual_name
            cls.__name__ = class_name
        # Create the field spec odict.
        cls._field_spec = field_spec_from_class(cls, class_dict, slots=True)
        spec = field_spec_from_class(cls, class_dict)
        q_spec = spec.copy()
        tx_spec = spec.copy()
        v_spec = spec.copy()
        # Keep track of fields that have fget methods.
        fget_fields = []
        for field_name, FieldClass in spec.iteritems():
            fget = FieldClass.fget
            if fget is not None:
                fget_fields.append(field_name)
                def get_field_value(self, fget=fget[0]):
                    return fget(self)
                # Transactions and the default query don't need
                # calculated fields.
                del q_spec[field_name]
                del tx_spec[field_name]
            else:
                field = FieldClass(instance=None)
                def get_field_value(self, field_name=field_name, field=field):
                    """Get the field value from the database."""
                    db = self._db
                    extent_name = self._extent.name
                    oid = self._oid
                    try:
                        value = db._entity_field(extent_name, oid, field_name)
                    except schevo.error.EntityDoesNotExist:
                        raise
                    except KeyError:  # XXX This needs to be more specific.
                        value = UNASSIGNED
                    field._value = value
                    return field.get()
            setattr(cls, field_name, property(fget=get_field_value))
        cls._fget_fields = tuple(fget_fields)
        #
        # Create standard transaction classes.  Transaction fields
        # included in a transaction class defined in the schema appear
        # below the fields that come from the entity field spec.
        #
        # Create
        if not hasattr(cls, '_Create'):
            class _Create(transaction.Create):
                pass
            _Create._field_spec = tx_spec.copy()
        else:
            # Always create a transaction subclass, in case the entity class
            # inherits from something other than E.Entity
            class _Create(cls._Create):
                pass
            subclass_spec = cls._Create._field_spec
            _Create._field_spec = tx_spec.copy()
            _Create._field_spec.update(subclass_spec, reorder=True)
            if hasattr(_Create, '_init_class'):
                _Create._init_class()
        _Create._fget_fields = cls._fget_fields
        cls._Create = _Create
        # Delete
        if not hasattr(cls, '_Delete'):
            class _Delete(transaction.Delete):
                pass
            _Delete._field_spec = tx_spec.copy()
        else:
            # Always create a transaction subclass, in case the entity class
            # inherits from something other than E.Entity
            class _Delete(cls._Delete):
                pass
            subclass_spec = cls._Delete._field_spec
            _Delete._field_spec = tx_spec.copy()
            _Delete._field_spec.update(subclass_spec, reorder=True)
            if hasattr(_Delete, '_init_class'):
                _Delete._init_class()
        _Delete._fget_fields = cls._fget_fields
        cls._Delete = _Delete
        # Generic Update (for use by cascading delete)
        class _GenericUpdate(transaction.Update):
            pass
        _GenericUpdate._field_spec = tx_spec.copy()
        _GenericUpdate._fget_fields = cls._fget_fields
        cls._GenericUpdate = _GenericUpdate
        # Update
        if not hasattr(cls, '_Update'):
            class _Update(transaction.Update):
                pass
            _Update._field_spec = tx_spec.copy()
        else:
            # Always create a transaction subclass, in case the entity class
            # inherits from something other than E.Entity
            class _Update(cls._Update):
                pass
            subclass_spec = cls._Update._field_spec
            _Update._field_spec = tx_spec.copy()
            _Update._field_spec.update(subclass_spec, reorder=True)
            if hasattr(_Update, '_init_class'):
                _Update._init_class()
        _Update._fget_fields = cls._fget_fields
        cls._Update = _Update
        #
        # Create standard view classes.  View fields included in a
        # view class defined in the schema appear below the fields
        # that come from the entity field spec.
        #
        # Default
        if not hasattr(cls, '_DefaultView'):
            class _DefaultView(view.View):
                _label = u'View'
            _DefaultView._field_spec = v_spec.copy()
        else:
            # Always create a view subclass, in case the entity class
            # inherits from something other than E.Entity
            class _DefaultView(cls._DefaultView):
                pass
            subclass_spec = cls._DefaultView._field_spec
            _DefaultView._field_spec = v_spec.copy()
            _DefaultView._field_spec.update(subclass_spec, reorder=True)
            if hasattr(_DefaultView, '_init_class'):
                _DefaultView._init_class()
        _DefaultView._fget_fields = cls._fget_fields
        _DefaultView._hidden_actions = set(cls._hidden_actions)
        _DefaultView._hidden_queries = set(cls._hidden_queries)
        cls._DefaultView = _DefaultView
        # Set the entity class and extent name on all of them.
        cls._Create._extent_name = class_name
        cls._DefaultView._extent_name = class_name
        cls._Delete._extent_name = class_name
        cls._GenericUpdate._extent_name = class_name
        cls._Update._extent_name = class_name
        cls._Create._EntityClass = cls
        cls._DefaultView._EntityClass = cls
        cls._Delete._EntityClass = cls
        cls._GenericUpdate._EntityClass = cls
        cls._Update._EntityClass = cls
        # Create the hide spec.
        cls._hidden_actions = set(cls._hidden_actions)
        cls._hidden_queries = set(cls._hidden_queries)
        cls._hidden_views = set(cls._hidden_views)
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
        # Remember queries for the EntityQueries namespace.
        q_names = []
        for attr in dir(cls):
            if attr.startswith('q_'):
                q_name = attr
                func = getattr(cls, q_name)
                if func.im_self is None:
                    q_names.append(q_name)
        cls._q_names = q_names
        # Remember transactions for the EntityTransactions namespace.
        t_names = []
        for attr in dir(cls):
            if attr.startswith('t_'):
                t_name = attr
                func = getattr(cls, t_name)
                if func.im_self is None:
                    t_names.append(t_name)
        cls._t_names = t_names
        # Remember views for the EntityViews namespace.
        v_names = []
        for attr in dir(cls):
            if attr.startswith('v_'):
                v_name = attr
                func = getattr(cls, v_name)
                if func.im_self is None:
                    v_names.append(v_name)
        cls._v_names = v_names
        # Remember x_methods for the EntityExtenders namespace.
        x_names = []
        for attr in dir(cls):
            if attr.startswith('x_'):
                x_name = attr
                func = getattr(cls, x_name)
                if func.im_self is None:
                    x_names.append(x_name)
        cls._x_names = x_names
        # Only if this global schema definition variable exists, and
        # this class applies to the current evolution context.
        if (schevo.namespace.SCHEMADEF is not None
            and (schevo.namespace.EVOLVING
                 or not cls._evolve_only)
            ):
            # Add this subclass to the entity classes namespace.
            schevo.namespace.SCHEMADEF.E._set(class_name, cls)
            # Keep track of relationship metadata.
            relationships = schevo.namespace.SCHEMADEF.relationships
            for field_name, FieldClass in cls._field_spec.iteritems():
                if (hasattr(FieldClass, 'allow') and
                    field_name not in cls._fget_fields):
                    for entity_name in FieldClass.allow:
                        spec = relationships.setdefault(entity_name, [])
                        spec.append((class_name, field_name))


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
    _hidden_actions = set(['create_if_necessary', 'create_or_update',
                           'generic_update'])
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
        if 'name' in self._field_spec:
            return unicode(self.name)
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

    @classmethod
    @with_label(u'Create Or Update')
    def t_create_or_update(cls, **kw):
        """Return a Create transaction that creates or updates."""
        tx = cls._Create(**kw)
        tx._style = transaction._Create_Or_Update
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
            if f_name not in create.f:
                # Don't include a field that doesn't exist in the
                # create transaction.
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
        stored_values = e._db._entity_fields(e._extent.name, e._oid)
        entity_field_map = e._field_spec.field_map(e, stored_values)
        # Remove fields that should not be included.
        new_fields = entity_field_map.itervalues()
        for filt in filters:
            new_fields = (field for field in new_fields if filt(field))
        entity_field_map = FieldMap(
            (field.name, field) for field in new_fields)
        # Update fields that have fget callables.
        for field in entity_field_map.itervalues():
            if field.fget is not None:
                value = field.fget[0](e)
            else:
                value = field._value
            field._value = field.convert(value)
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
            raise ExtentDoesNotExist('%r does not exist.' % other_extent_name)
        if other_field_name not in extent.field_spec:
            raise FieldDoesNotExist('%r does not exist in %r' % (
                other_field_name, other_extent_name))
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
        return (k for k in self._d.iterkeys()
                if k not in self._e._hidden_actions)


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


class EntityRef(object):
    """Reference to an Entity via its extent name and OID."""

    def __init__(self, extent_name, oid):
        """Create an EntityRef instance.

        - `extent_name`: The name of the extent.
        - `oid`: The OID of the entity.
        """
        self.extent_name = extent_name
        self.oid = oid


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2006 Orbtech, L.L.C. and contributors
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
