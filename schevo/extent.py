"""Extent class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo import base
from schevo.entity import Entity
from schevo.error import EntityDoesNotExist
from schevo.error import FindoneFoundMoreThanOne
from schevo.introspect import isextentmethod, isselectionmethod
from schevo.namespace import NamespaceExtension
from schevo.query import ResultsIterator, ResultsList


class Extent(base.Extent):
    """An extent of entity instances."""

    def __init__(self, db, name, id, EntityClass):
        # Decorate the EntityClass.
        EntityClass._db = db
        EntityClass._extent = self
        # Decorate the extent.
        self.__doc__ = EntityClass.__doc__
        self.hidden = EntityClass._hidden
        # Public API.
        self.db = db
        self.default_key = EntityClass._default_key
        self.EntityClass = EntityClass
        self.field_spec = EntityClass._field_spec
        self.id = id
        self.index_spec = EntityClass._index_spec
        self.initial = EntityClass._initial
        self.key_spec = EntityClass._key_spec
        self.name = name
        self.f = ExtentFieldClasses('f', self, EntityClass)
        self.q = ExtentQueries('q', self, EntityClass)
        self.t = ExtentTransactions('t', self, EntityClass)
        self.x = ExtentExtenders('x', self, EntityClass)
        # Private variables.
        self._by = db._by_entity_oids
        self._enforce = db._enforce_index
        self._find = db._find_entity_oids
        self._label = EntityClass._label
        self._plural = EntityClass._plural
        self._relax = db._relax_index
        # Attach extent to each field class.
        for field_name, field_class in self.field_spec.iteritems():
            field_class._extent = self

    def __cmp__(self, other):
        if other.__class__ is self.__class__:
            return cmp(self.name, other.name)
        else:
            return cmp(hash(self), hash(other))

    def __contains__(self, entity):
        if isinstance(entity, Entity):
            if entity._extent is not self:
                return False
            oid = entity._oid
        else:
            oid = entity
        return self.db._extent_contains_oid(self.name, oid)

    def __getitem__(self, oid):
        if not self.db._extent_contains_oid(self.name, oid):
            raise EntityDoesNotExist(self.name, oid=oid)
        return self.EntityClass(oid)

    def __iter__(self):
        """Return an iterator of entities in order by OID."""
        Entity = self.EntityClass
        oids = self._find(self.name, None)
        for oid in oids:
            try:
                entity = Entity(oid)
            except EntityDoesNotExist:
                pass
            else:
                yield entity

    def __len__(self):
        return self.db._extent_len(self.name)

    def __nonzero__(self):
        return True

    def __repr__(self):
        return '<Extent %r in %r>' % (self.name, self.db)

    def _scrub_criteria(self, criteria, equality_criteria):
        # Convert equality_criteria to criteria.
        if len(equality_criteria) > 0:
            criteria = list(criteria) # tuple to list so we can append
            for key, value in equality_criteria.iteritems():
                criteria.append(self.f[key] == value)
        # Multiple criteria are AND-ed together.
        if len(criteria) > 1:
            criterion = criteria[0]
            for c in criteria[1:]:
                criterion &= c
        elif len(criteria) == 1:
            criterion = criteria[0]
        else:
            criterion = None
        return criterion

    def as_datalist(self):
        """Return sorted list of entity value tuples in a form
        suitable for initial or sample data in a schema."""
        return sorted([entity.s.as_data() for entity in self])

    def as_unittest_code(self):
        """Return formatted string of entity value tuples in a form
        suitable for initial or sample data in a schema."""
        code = 'E.%s._sample_unittest = [' % self.name
        code += '\n    '
        body = [str(data) for data in self.as_datalist()]
        code += ',\n    '.join(body)
        code += ',\n    ]'
        return code

    def by(self, *index_spec):
        """Return an iterator of entities sorted by index_spec."""
        Entity = self.EntityClass
        oids = self._by(self.name, *index_spec)
        def generator():
            for oid in oids:
                try:
                    entity = Entity(oid)
                except EntityDoesNotExist:
                    pass
                else:
                    yield entity
        return ResultsIterator(generator())

    def by_oids(self, *index_spec):
        """Return a list of OIDs sorted by index_spec."""
        return self._by(self.name, *index_spec)

    def count(self, *criteria, **equality_criteria):
        """Return count of entities matching given field value(s)."""
        criterion = self._scrub_criteria(criteria, equality_criteria)
        # Find count.
        return len(self._find(self.name, criterion))

    def enforce_index(self, *index_spec):
        """Validate and begin enforcing constraints on the specified
        index if it was relaxed within the currently-executing
        transaction."""
        self._enforce(self.name, *index_spec)

    def find(self, *criteria, **equality_criteria):
        """Return list of entities matching given field value(s)."""
        criterion = self._scrub_criteria(criteria, equality_criteria)
        # Get OIDs from database and return entity instances.
        Entity = self.EntityClass
        return ResultsList(
            Entity(oid) for oid in self._find(self.name, criterion))

    def find_oids(self, *criteria, **equality_criteria):
        """Return list of OIDs matching given field value(s)."""
        criterion = self._scrub_criteria(criteria, equality_criteria)
        # XXX: Needs unit test.
        return self._find(self.name, criterion)

    def findone(self, *criteria, **equality_criteria):
        """Return single entity matching given field value(s)."""
        criterion = self._scrub_criteria(criteria, equality_criteria)
        # Find all OIDs.
        results = self._find(self.name, criterion)
        # Check length and return value or raise error.
        count = len(results)
        if count == 1:
            return self.EntityClass(results[0])
        elif count == 0:
            return None
        else:
            raise FindoneFoundMoreThanOne(self.name, criteria)

    @property
    def next_oid(self):
        return self.db._extent_next_oid(self.name)

    @property
    def relationships(self):
        return self.EntityClass._relationships

    def relax_index(self, *index_spec):
        """Relax constraints on the specified index until a matching
        enforce_index is called, or the currently-executing
        transaction finishes, whichever occurs first."""
        self._relax(self.name, *index_spec)

    def relax_all_indices(self):
        """Relax all indices using `relax_index`."""
        for index_spec in self.key_spec:
            self.relax_index(*index_spec)


class ExtentExtenders(NamespaceExtension):
    """Methods that extend the functionality of an extent."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, instance, EntityClass):
        NamespaceExtension.__init__(self, name, instance)
        # Expose methods through this namespace.
        for name in dir(EntityClass):
            # Extender methods always have x_ prefix.
            if name.startswith('x_'):
                method = getattr(EntityClass, name)
                # Methods that apply to an extent are extentmethods.
                if isextentmethod(method):
                    # Drop the 'x_' prefix.
                    name = name[2:]
                    self._set(name, method)


class ExtentFieldClasses(object):

    __slots__ = ['_n', '_i', '_extent']

    def __init__(self, name, instance, extent):
        self._n = name
        self._i = instance
        self._extent = extent

    def __getattr__(self, name):
        FieldClass = self._extent._field_spec[name]
        return FieldClass

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __iter__(self):
        return iter(self._extent._field_spec)

    def __repr__(self):
        return '<%r namespace on %r>' % (self._n, self._i)

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(iter(self))


class ExtentQueries(NamespaceExtension):
    """Queries that apply to an extent."""

    __slots__ = NamespaceExtension.__slots__ + ['_E']

    def __init__(self, name, instance, EntityClass):
        NamespaceExtension.__init__(self, name, instance)
        self._E = EntityClass
        # Expose query methods through this namespace.
        for key in dir(EntityClass):
            # Query methods always have q_ prefix.
            if key.startswith('q_'):
                method = getattr(EntityClass, key)
                # Query methods that apply to an extent are
                # extentmethods of an Entity class.
                if isextentmethod(method):
                    # Drop the 'q_' prefix.
                    name = key[2:]
                    self._set(name, method)

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if k not in self._E._hidden_queries)


class ExtentTransactions(NamespaceExtension):
    """Transactions that apply to an extent."""

    __slots__ = NamespaceExtension.__slots__ + ['_E']

    def __init__(self, name, instance, EntityClass):
        NamespaceExtension.__init__(self, name, instance)
        self._E = EntityClass
        # Expose transaction methods through this namespace.
        for key in dir(EntityClass):
            # Transaction methods always have t_ prefix.
            if key.startswith('t_'):
                method = getattr(EntityClass, key)
                # Transaction methods that apply to an extent are
                # extentmethods of an Entity class.
                if isextentmethod(method):
                    # Drop the 't_' prefix.
                    name = key[2:]
                    self._set(name, method)

    def __iter__(self):
        return (k for k in self._d.iterkeys()
                if (k not in self._E._hidden_actions
                    and 't_' + k not in self._E._t_selectionmethod_names
                    )
                )


optimize.bind_all(sys.modules[__name__])  # Last line of module.
