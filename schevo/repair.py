"""Schevo database repair functions.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import schevo.database


def repairs_needed(db, db_filename):
    """Return a list of repair types that should be performed in order to
    repair the given database."""
    needed = []
    for repair_type in [
        EntityFieldIdsRepair,
        ]:
        repair = repair_type(db, db_filename)
        if repair.is_needed:
            needed.append(repair)
    return needed


class EntityFieldIdsRepair(object):

    description = 'Remove entity_field_ids extraneous field IDs. (No data loss)'

    def __init__(self, db, db_filename):
        self.db = db
        self.db_filename = db_filename
        self._determine_if_needed()

    def perform(self):
        # Database starts out closed.
        db_filename = self.db_filename
        db = schevo.database.open(db_filename)
        try:
            try:
                items = self._extents_extraneous.items()
                for (extent_name, extraneous_field_ids) in items:
                    extent_map = db._extent_map(extent_name)
                    # For all formats, remove extraneouse field IDs from
                    # entity_field_ids.
                    entity_field_ids = set(extent_map['entity_field_ids'])
                    entity_field_ids -= extraneous_field_ids
                    extent_map['entity_field_ids'] = tuple(entity_field_ids)
                    # For format 2, also iterate over each entity in the
                    # extent and remove extraneous related_entities sets.
                    if db.format == 2:
                        for entity_map in extent_map['entities'].itervalues():
                            related_entities = entity_map['related_entities']
                            for field_id in extraneous_field_ids:
                                if field_id in related_entities:
                                    del related_entities[field_id]
                db._commit()
            except:
                db._rollback()
                raise
        finally:
            db.close()

    def _determine_if_needed(self):
        db = self.db
        self.is_needed = False
        extents_extraneous = self._extents_extraneous = {
            # extent_name: set([extraneous, field, ids]),
            }
        for extent in db.extents():
            extent_map = db._extent_map(extent.name)
            field_id_name = extent_map['field_id_name']
            entity_field_ids = extent_map['entity_field_ids']
            for entity_field_id in entity_field_ids:
                field_name = field_id_name[entity_field_id]
                FieldClass = extent.f[field_name]
                if FieldClass.fget is not None:
                    # Calculated field found in entity_field_ids,
                    # database needs repair.
                    self.is_needed = True
                    extraneous_field_ids = extents_extraneous.setdefault(
                        extent.name, set())
                    extraneous_field_ids.add(entity_field_id)


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
