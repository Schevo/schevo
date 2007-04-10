"""Entity Placeholder class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.constant import UNASSIGNED


class Placeholder(object):
    """Placeholder for an Entity via its extent ID and OID."""

    __slots__ = ['extent_id', 'oid']

    def __init__(self, entity):
        """Create a Placeholder instance based on `entity`."""
        self.extent_id = entity._db._extent_name_id[entity._extent.name]
        self.oid = entity._oid

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
        return '<Placeholder extent_id:%r, oid:%r>' % (
            self.extent_id, self.oid)

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
        extent = db.extent(db._extent_id_name[self.extent_id])
        oid = self.oid
        if oid in extent:
            return extent[oid]
        else:
            return UNASSIGNED


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
