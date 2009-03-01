"""Entity Placeholder class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo.constant import UNASSIGNED


class Placeholder(object):
    """Placeholder for an Entity via its extent ID and OID."""

    __slots__ = ['extent_id', 'oid', 'entity', 'db_sync_count']

    def __init__(self, entity):
        """Create a Placeholder instance based on `entity`."""
        self.extent_id = entity._extent.id
        self.oid = entity._oid
        self.entity = entity
        self.db_sync_count = -1

    def __getstate__(self):
        # Only store the extent and OID of the entity, not the entity
        # itself.
        return (self.extent_id, self.oid)

    def __setstate__(self, state):
        self.extent_id, self.oid = state
        # Entity instance not available from pickled version.
        self.entity = None

    def __cmp__(self, other):
        if other is UNASSIGNED:
            return 1
        if isinstance(other, Placeholder):
            return cmp((self.extent_id, self.oid),
                       (other.extent_id, other.oid))
        elif isinstance(other, tuple) and len(other) == 2:
            return cmp((self.extent_id, self.oid), other)
        else:
            return cmp(hash(self), hash(other))

    def __eq__(self, other):
        if isinstance(other, Placeholder):
            return (self.extent_id, self.oid) == (other.extent_id, other.oid)
        else:
            return False

    def __hash__(self):
        return hash((self.extent_id, self.oid))

    def __ne__(self, other):
        # Equivalent to "not (self == other)" but unfolded to prevent
        # extraneous method call.
        if isinstance(other, Placeholder):
            return (self.extent_id, self.oid) != (other.extent_id, other.oid)
        else:
            return True

    def __repr__(self):
        if self.entity is None:
            return '<Placeholder extent_id:%r, oid:%r>' % (
                self.extent_id, self.oid)
        else:
            # If entity is known, show its representation.
            return '<PH: %r>' % self.entity

    def restore(self, db):
        """Return the actual entity that this placeholder refers to, if it
        exists; returns UNASSIGNED if the entity no longer exists.

        EntityDoesNotExist errors are not propagated because in some cases,
        such as in complex cascade delete scenarios, several related
        entities must be deleted in one transaction.

        Such a transaction appears as an atomic operation to the executor of
        the transaction, but behind the scenes, an entity B may still refer to
        another already-deleted entity A until entity B is deleted. The delete
        transaction used to delete entity B must be initialized with the
        values of that entity.  Since entity A is already deleted, entity B
        must have some other value other than a reference to entity A.
        Therefore, UNASSIGNED is used instead.
        """
        if self.entity is not None and self.db_sync_count == db._sync_count:
            # Use the attached entity if it's there; only foolishness
            # would result in it being the wrong one.
            return self.entity
        extent = db.extent(self.extent_id)
        oid = self.oid
        if oid in extent:
            entity = self.entity = extent[oid]
            self.db_sync_count = db._sync_count
            return entity
        else:
            return UNASSIGNED

    @staticmethod
    def new(extent_id, oid, entity=None):
        p = object.__new__(Placeholder)
        p.extent_id = extent_id
        p.oid = oid
        p.entity = entity
        return p


optimize.bind_all(sys.modules[__name__])  # Last line of module.
