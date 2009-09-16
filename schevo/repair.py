"""Schevo database repair functions."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import schevo.database


def repairs_needed(db, url):
    """Return a list of repair types that should be performed in order to
    repair the given database."""
    needed = []
    for repair_type in [
        EntityFieldIdsRepair,
        OrphanLinkStructuresRepair,
        ]:
        repair = repair_type(db, url)
        if repair.is_needed:
            needed.append(repair)
    return needed


class EntityFieldIdsRepair(object):

    description = 'Remove entity_field_ids extraneous field IDs. (No data loss)'
    is_needed_certainty = True

    def __init__(self, db, url):
        self.db = db
        self.url = url
        self._determine_if_needed()

    def perform(self):
        # Database starts out closed.
        url = self.url
        db = schevo.database.open(url)
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


class OrphanLinkStructuresRepair(object):

    description = 'Remove orphan link structures. (No data loss)'
    is_needed = True
    is_needed_certainty = False

    def __init__(self, db, url):
        self.db = db
        self.url = url

    def perform(self):
        # Database starts out closed.
        url = self.url
        db = schevo.database.open(url)
        try:
            try:
                extent_id_name = db._extent_id_name
                extent_maps_by_id = db._extent_maps_by_id
                for extent_id, extent_map in extent_maps_by_id.iteritems():
                    extent_name = extent_map['name']
                    for oid, entity_map in extent_map['entities'].iteritems():
                        links = entity_map['links']
                        for key in links.keys():
                            other_extent_id, other_field_id = key
                            if other_extent_id not in extent_id_name:
                                link_count = len(links[key])
                                del links[key]
                                entity_map['link_count'] -= link_count
                        entity = db.extent(extent_name)[oid]
                        len_links = sum(
                            len(v) for v in entity.s.links().itervalues())
                        assert len_links == entity.s.count()
                db._commit()
            except:
                db._rollback()
                raise
        finally:
            db.close()


optimize.bind_all(sys.modules[__name__])  # Last line of module.
