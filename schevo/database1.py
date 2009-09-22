"""Schevo database, format 1."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo.base import Entity
from schevo.change import CREATE, UPDATE, DELETE
from schevo.constant import UNASSIGNED
from schevo import database2
from schevo.database2 import _index_add, _index_remove
from schevo import error
from schevo.field import Entity as EntityField
from schevo.placeholder import Placeholder
from schevo.trace import log


class Database(database2.Database):
    """Schevo database, format 1, using schevo.store as an object store.

    Based on the format 2 database class, with overrides to modify behavior
    to store information using format 1 instead.

    Also restricts the use of may_store_entities field types other than Entity
    fields themselves.

    See doc/SchevoInternalDatabaseStructures.txt for detailed information on
    data structures.
    """

    def _create_entity(self, extent_name, fields, related_entities,
                       oid=None, rev=None):
        """Create a new entity in an extent; return the oid.

        - `extent_name`: Name of the extent to create a new entity in.

        - `fields`: Dictionary of field_name:field_value mappings, where
          each field_value is the value to be stored in the database, as
          returned by a field instance's `_dump` method.

        - `related_entities`: Dictionary of field_name:related_entity_set
          mappings, where each related_entity_set is the set of entities
          stored in the field's structure, as returned by a field
          instance's `_entities_in_value` method.

        - `oid`: (optional) Specific OID to create the entity as; used
          for importing data, e.g. from an XML document.

        - `rev`: (optional) Specific revision to create the entity as; see
          `oid`.
        """
        extent_map = self._extent_map(extent_name)
        entities = extent_map['entities']
        old_next_oid = extent_map['next_oid']
        field_name_id = extent_map['field_name_id']
        entity_field_ids = extent_map['entity_field_ids']
        extent_name_id = self._extent_name_id
        extent_maps_by_id = self._extent_maps_by_id
        indices_added = []
        ia_append = indices_added.append
        links_created = []
        lc_append = links_created.append
        BTree = self._BTree
        PDict = self._PDict
        try:
            if oid is None:
                oid = extent_map['next_oid']
                extent_map['next_oid'] += 1
            if rev is None:
                rev = 0
            if oid in entities:
                raise error.EntityExists(extent_name, oid)
            # Create dict with field-id:field-value items.
            fields_by_id = PDict()
            new_links = []
            nl_append = new_links.append
            for name, value in fields.iteritems():
                field_id = field_name_id[name]
                # Handle entity reference fields.
                if field_id in entity_field_ids:
                    if isinstance(value, Placeholder):
                        # Dereference entity.
                        other_extent_id = value.extent_id
                        other_oid = value.oid
                        value = (other_extent_id, other_oid)
                        nl_append((field_id, other_extent_id, other_oid))
                    elif len(related_entities.get(name, [])) > 1:
                        msg = (
                            'Field values with multiple entities are not '
                            'supported by format 1 Schevo databases.'
                            )
                        raise error.UnsupportedFieldType(reason)
                fields_by_id[field_id] = value
            # Make sure fields that weren't specified are set to
            # UNASSIGNED.
            setdefault = fields_by_id.setdefault
            for field_id in field_name_id.itervalues():
                setdefault(field_id, UNASSIGNED)
            # Update index mappings.
            indices = extent_map['indices']
            for index_spec in indices.iterkeys():
                field_values = tuple(fields_by_id[field_id]
                                     for field_id in index_spec)
                # Find out if the index has been relaxed.
                relaxed_specs = self._relaxed[extent_name]
                if index_spec in relaxed_specs:
                    txns, relaxed = relaxed_specs[index_spec]
                else:
                    relaxed = None
                _index_add(extent_map, index_spec, relaxed, oid, field_values,
                           BTree)
                ia_append((extent_map, index_spec, oid, field_values))
            # Update links from this entity to another entity.
            referrer_extent_id = extent_name_id[extent_name]
            for referrer_field_id, other_extent_id, other_oid in new_links:
                other_extent_map = extent_maps_by_id[other_extent_id]
                try:
                    other_entity_map = other_extent_map['entities'][other_oid]
                except KeyError:
                    field_id_name = extent_map['field_id_name']
                    field_name = field_id_name[referrer_field_id]
                    other_extent_map = extent_maps_by_id[other_extent_id]
                    other_extent_name = other_extent_map['name']
                    raise error.EntityDoesNotExist(
                        other_extent_name, field_name=field_name)
                # Add a link to the other entity.
                links = other_entity_map['links']
                link_key = (referrer_extent_id, referrer_field_id)
                if link_key not in links:  # XXX Should already be there.
                    links[link_key] = BTree()
                links[link_key][oid] = None
                other_entity_map['link_count'] += 1
                lc_append((other_entity_map, links, link_key, oid))
            # Create the actual entity.
            entity_map = entities[oid] = PDict()
            entity_map['rev'] = rev
            entity_map['fields'] = fields_by_id
            # XXX flesh out links based on who is capable of linking
            # to this one.
            entity_map['link_count'] = 0
            entity_map['links'] = PDict()
            extent_map['len'] += 1
            # Allow inversion of this operation.
            self._append_inversion(self._delete_entity, extent_name, oid)
            # Keep track of changes.
            append_change = self._append_change
            append_change(CREATE, extent_name, oid)
            return oid
        except:
            # Revert changes made during create attempt.
            for _e, _i, _o, _f in indices_added:
                _index_remove(_e, _i, _o, _f)
            for other_entity_map, links, link_key, oid in links_created:
                del links[link_key][oid]
                other_entity_map['link_count'] -= 1
            extent_map['next_oid'] = old_next_oid
            raise

    def _delete_entity(self, extent_name, oid):
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        extent_id = extent_map['id']
        extent_name_id = self._extent_name_id
        extent_maps_by_id = self._extent_maps_by_id
        entity_field_ids = extent_map['entity_field_ids']
        field_name_id = extent_map['field_name_id']
        link_count = entity_map['link_count']
        links = entity_map['links']
        # Disallow deletion if other entities refer to this one,
        # unless all references are merely from ourself or an entity
        # that will be deleted.
        deletes = set()
        executing = self._executing
        if executing:
            tx = executing[-1]
            deletes.update([(extent_name_id[del_entity_cls.__name__], del_oid)
                            for del_entity_cls, del_oid in tx._deletes])
            deletes.update([(extent_name_id[del_entity_cls.__name__], del_oid)
                            for del_entity_cls, del_oid in tx._known_deletes])
        for (other_extent_id, other_field_id), others in links.iteritems():
            for other_oid in others:
                if (other_extent_id, other_oid) in deletes:
                    continue
                # Give up as soon as we find one outside reference.
                if (other_extent_id, other_oid) != (extent_id, oid):
                    entity = self._entity(extent_name, oid)
                    referring_entity = self._entity(other_extent_id, other_oid)
                    other_field_name = extent_maps_by_id[other_extent_id][
                        'field_id_name'][other_field_id]
                    raise error.DeleteRestricted(
                        entity=entity,
                        referring_entity=referring_entity,
                        referring_field_name=other_field_name
                        )
        # Get old values for use in a potential inversion.
        old_fields = self._entity_fields(extent_name, oid)
        old_related_entities = self._entity_related_entities(extent_name, oid)
        old_rev = entity_map['rev']
        # Remove index mappings.
        indices = extent_map['indices']
        fields_by_id = entity_map['fields']
        for index_spec in indices.iterkeys():
            field_values = tuple(fields_by_id.get(f_id, UNASSIGNED)
                                 for f_id in index_spec)
            _index_remove(extent_map, index_spec, oid, field_values)
        # Delete links from this entity to other entities.
        referrer_extent_id = extent_name_id[extent_name]
        for referrer_field_id in entity_field_ids:
            other_value = fields_by_id.get(referrer_field_id, UNASSIGNED)
            if isinstance(other_value, tuple):
                # Remove the link to the other entity.
                other_extent_id, other_oid = other_value
                link_key = (referrer_extent_id, referrer_field_id)
                other_extent_map = extent_maps_by_id[other_extent_id]
                if other_oid in other_extent_map['entities']:
                    other_entity_map = other_extent_map['entities'][other_oid]
                    links = other_entity_map['links']
                    other_links = links[link_key]
                    del other_links[oid]
                    other_entity_map['link_count'] -= 1
        del extent_map['entities'][oid]
        extent_map['len'] -= 1
        # Allow inversion of this operation.
        self._append_inversion(
            self._create_entity, extent_name, old_fields, old_related_entities,
            oid, old_rev)
        # Keep track of changes.
        append_change = self._append_change
        append_change(DELETE, extent_name, oid)

    def _delete_extent(self, extent_name):
        """Remove a named extent."""
        # XXX: Need to check for links to any entity in this extent,
        # and fail to remove it if so.
        #
        # Iterate through all entities in the extent to delete, and
        # remove bidirectional link information from any entities they
        # point to.
        extent_map = self._extent_map(extent_name)
        extent_id = extent_map['id']
        entity_field_ids = extent_map['entity_field_ids']
        for oid, entity_map in extent_map['entities'].iteritems():
            fields = entity_map['fields']
            for field_id in entity_field_ids:
                stored_value = fields.get(field_id, UNASSIGNED)
                if isinstance(stored_value, tuple):
                    rel_extent_id, rel_oid = stored_value
                    rel_extent_map = self._extent_maps_by_id.get(
                        rel_extent_id, None)
                    if rel_extent_map is not None:
                        rel_entity_map = rel_extent_map['entities'][rel_oid]
                        rel_links = rel_entity_map['links']
                        key = (extent_id, field_id)
                        if key in rel_links:
                            link_count = len(rel_links[key])
                            del rel_links[key]
                            rel_entity_map['link_count'] -= link_count
        # Delete the extent.
        del self._extent_name_id[extent_name]
        del self._extent_maps_by_id[extent_id]
        del self._extent_maps_by_name[extent_name]

    def _entity_field(self, extent_name, oid, name):
        """Return the value of a field in an entity in named extent
        with given OID."""
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_name_id = extent_map['field_name_id']
        entity_field_ids = extent_map['entity_field_ids']
        field_id = field_name_id[name]
        value = entity_map['fields'][field_id]
        if field_id in entity_field_ids and isinstance(value, tuple):
            value = Placeholder.new(*value)
        return value

    def _entity_fields(self, extent_name, oid):
        """Return a dictionary of field values for an entity in
        `extent` with given OID."""
        entity_classes = self._entity_classes
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_id_name = extent_map['field_id_name']
        entity_field_ids = extent_map['entity_field_ids']
        fields = {}
        for field_id, value in entity_map['fields'].iteritems():
            if field_id in entity_field_ids and isinstance(value, tuple):
                value = Placeholder.new(*value)
            # During database evolution, it may turn out that fields
            # get removed.  For time efficiency reasons, Schevo does
            # not iterate through all entities to remove existing
            # data.  Therefore, when getting entity fields from the
            # database here, ignore fields that exist in the entity
            # but no longer exist in the extent.
            field_name = field_id_name.get(field_id, None)
            if field_name:
                fields[field_name] = value
        return fields

    def _entity_related_entities(self, extent_name, oid):
        """Return a dictionary of related entity sets for an entity in
        `extent` with given OID."""
        entity_classes = self._entity_classes
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_id_name = extent_map['field_id_name']
        entity_field_ids = extent_map['entity_field_ids']
        fields = entity_map['fields']
        related_entities = {}
        for field_id in entity_field_ids:
            # During database evolution, it may turn out that fields
            # get removed.  For time efficiency reasons, Schevo does
            # not iterate through all entities to remove existing
            # data.  Therefore, when getting entity fields from the
            # database here, ignore fields that exist in the entity
            # but no longer exist in the extent.
            field_name = field_id_name.get(field_id, None)
            if field_name:
                value = fields.get(field_id, None)
                if isinstance(value, tuple):
                    value = Placeholder.new(*value)
                    related_entities[field_name] = frozenset([value])
                else:
                    related_entities[field_name] = frozenset()
        return related_entities

    def _find_entity_oids_single_extent_field_equality(
        self, extent_name, criteria
        ):
        extent_map = self._extent_map(extent_name)
        entity_maps = extent_map['entities']
        EntityClass = self._entity_classes[extent_name]
        extent_name_id = self._extent_name_id
        indices = extent_map['indices']
        normalized_index_map = extent_map['normalized_index_map']
        entity_field_ids = extent_map['entity_field_ids']
        field_name_id = extent_map['field_name_id']
        # Convert from field_name:value to field_id:value.
        field_id_value = {}
        field_spec = EntityClass._field_spec
        for field_class, value in criteria.iteritems():
            field_name = field_class.name
            try:
                field_id = field_name_id[field_name]
            except KeyError:
                raise error.FieldDoesNotExist(extent_name, field_name)
            # Dereference if it's an entity field and not UNASSIGNED.
            if field_id in entity_field_ids and isinstance(value, Entity):
                # Dereference entity.
                other_extent_id = extent_name_id[value._extent.name]
                other_oid = value._oid
                value = (other_extent_id, other_oid)
            else:
                # Create a field to convert the value.
                FieldClass = field_spec[field_name]
                field = FieldClass(None, None)
                value = field.convert(value)
            field_id_value[field_id] = value
        # First, see if the fields given can be found in an index. If
        # so, use the index to return matches.
        #
        # XXX: Should be updated to use partial search via an index,
        # and brute-force on the subset found via that index.
        field_ids = tuple(sorted(field_id_value))
        assert log(3, 'field_ids', field_ids)
        len_field_ids = len(field_ids)
        index_spec = None
        if field_ids in normalized_index_map:
            for spec in normalized_index_map[field_ids]:
                if len(spec) == len_field_ids:
                    index_spec = spec
                    break
        results = []
        if index_spec is not None:
            # We found an index to use.
            assert log(2, 'Use index spec:', index_spec)
            unique, branch = indices[index_spec]
            match = True
            for field_id in index_spec:
                field_value = field_id_value[field_id]
                if field_value not in branch:
                    # No matches found.
                    match = False
                    break
                branch = branch[field_value]
            if match:
                # Now we're at a leaf that matches all of the
                # criteria, so return the OIDs in that leaf.
                results = list(branch.keys())
        else:
            # Fields aren't indexed, so use brute force.
            assert log(2, 'Use brute force.')
            append = results.append
            for oid, entity_map in entity_maps.iteritems():
                fields = entity_map['fields']
                match = True
                for field_id, value in field_id_value.iteritems():
                    if fields.get(field_id, UNASSIGNED) != value:
                        match = False
                        break
                if match:
                    append(oid)
        assert log(2, 'Result count', len(results))
        return results

    def _update_entity(self, extent_name, oid, fields, related_entities,
                       rev=None):
        """Update an existing entity in an extent.

        - `extent_name`: Name of the extent to create a new entity in.

        - `oid`: OID of the entity to update.

        - `fields`: Dictionary of field_name:field_value mappings to change,
          where each field_value is the value to be stored in the database, as
          returned by a field instance's `_dump` method.

        - `related_entities`: Dictionary of field_name:related_entity_set
          mappings, where each related_entity_set is the set of entities
          stored in the field's structure, as returned by a field instance's
          `_entities_in_value` method.

        - `rev`: (optional) Specific revision to update the entity to.
        """
        # XXX: Could be optimized to update mappings only when
        # necessary.
        entity_classes = self._entity_classes
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_name_id = extent_map['field_name_id']
        entity_field_ids = extent_map['entity_field_ids']
        extent_name_id = self._extent_name_id
        extent_maps_by_id = self._extent_maps_by_id
        indices_added = []
        indices_removed = []
        new_links = []
        links_created = []
        links_deleted = []
        ia_append = indices_added.append
        ir_append = indices_removed.append
        nl_append = new_links.append
        lc_append = links_created.append
        ld_append = links_deleted.append
        BTree = self._BTree
        try:
            # Get old values for use in a potential inversion.
            old_fields = self._entity_fields(extent_name, oid)
            old_related_entities = self._entity_related_entities(
                extent_name, oid)
            old_rev = entity_map['rev']
            # Dereference entities.
            for name, value in fields.items():
                field_id = field_name_id[name]
                if field_id in entity_field_ids:
                    if isinstance(value, Placeholder):
                        # Dereference entity.
                        other_extent_id = value.extent_id
                        other_oid = value.oid
                        value = (other_extent_id, other_oid)
                        nl_append((field_id, other_extent_id, other_oid))
                    elif len(related_entities.get(name, [])) > 1:
                        msg = (
                            'Field values with multiple entities are not '
                            'supported by format 1 Schevo databases.'
                            )
                        raise UnsupportedFieldType(reason)
                fields[name] = value
            # Get fields, and set UNASSIGNED for any fields that are
            # new since the last time the entity was stored.
            fields_by_id = entity_map['fields']
            all_field_ids = set(extent_map['field_id_name'].iterkeys())
            new_fields = all_field_ids - set(fields_by_id.iterkeys())
            fields_by_id.update(dict(
                (field_id, UNASSIGNED) for field_id in new_fields))
            # Remove existing index mappings.
            indices = extent_map['indices']
            for index_spec in indices.iterkeys():
                field_values = tuple(fields_by_id[field_id]
                                     for field_id in index_spec)
                # Find out if the index has been relaxed.
                relaxed_specs = self._relaxed[extent_name]
                if index_spec in relaxed_specs:
                    txns, relaxed = relaxed_specs[index_spec]
                else:
                    relaxed = None
                _index_remove(extent_map, index_spec, oid, field_values)
                ir_append((extent_map, index_spec, relaxed, oid, field_values))
            # Delete links from this entity to other entities.
            referrer_extent_id = extent_name_id[extent_name]
            for referrer_field_id in entity_field_ids:
                other_value = fields_by_id[referrer_field_id]
                if isinstance(other_value, tuple):
                    # Remove the link to the other entity.
                    other_extent_id, other_oid = other_value
                    link_key = (referrer_extent_id, referrer_field_id)
                    other_extent_map = extent_maps_by_id[other_extent_id]
                    other_entity_map = other_extent_map['entities'][other_oid]
                    links = other_entity_map['links']
                    other_links = links[link_key]
                    del other_links[oid]
                    other_entity_map['link_count'] -= 1
                    ld_append((other_entity_map, links, link_key, oid))
            # Create ephemeral fields for creating new index mappings.
            new_fields = dict(fields_by_id)
            for name, value in fields.iteritems():
                new_fields[field_name_id[name]] = value
            # Create new index mappings.
            for index_spec in indices.iterkeys():
                field_values = tuple(new_fields[field_id]
                                     for field_id in index_spec)
                # Find out if the index has been relaxed.
                relaxed_specs = self._relaxed[extent_name]
                if index_spec in relaxed_specs:
                    txns, relaxed = relaxed_specs[index_spec]
                else:
                    relaxed = None
                _index_add(extent_map, index_spec, relaxed, oid, field_values,
                           BTree)
                ia_append((extent_map, index_spec, oid, field_values))
            # Update links from this entity to another entity.
            referrer_extent_id = extent_name_id[extent_name]
            for referrer_field_id, other_extent_id, other_oid in new_links:
                other_extent_map = extent_maps_by_id[other_extent_id]
                try:
                    other_entity_map = other_extent_map['entities'][other_oid]
                except KeyError:
                    field_id_name = extent_map['field_id_name']
                    field_name = field_id_name[referrer_field_id]
                    other_extent_map = extent_maps_by_id[other_extent_id]
                    other_extent_name = other_extent_map['name']
                    raise error.EntityDoesNotExist(
                        other_extent_name, field_name=field_name)
                # Add a link to the other entity.
                links = other_entity_map['links']
                link_key = (referrer_extent_id, referrer_field_id)
                if link_key not in links:  # XXX Should already be there.
                    links[link_key] = BTree()
                links[link_key][oid] = None
                other_entity_map['link_count'] += 1
                lc_append((other_entity_map, links, link_key, oid))
            # Update actual fields.
            for name, value in fields.iteritems():
                fields_by_id[field_name_id[name]] = value
            if rev is None:
                entity_map['rev'] += 1
            else:
                entity_map['rev'] = rev
            # Allow inversion of this operation.
            self._append_inversion(
                self._update_entity, extent_name, oid, old_fields,
                old_related_entities, old_rev)
            # Keep track of changes.
            append_change = self._append_change
            append_change(UPDATE, extent_name, oid)
        except:
            # Revert changes made during update attempt.
            for _e, _i, _o, _f in indices_added:
                _index_remove(_e, _i, _o, _f)
            for _e, _i, _r, _o, _f in indices_removed:
                _index_add(_e, _i, _r, _o, _f, BTree)
            for other_entity_map, links, link_key, oid in links_created:
                del links[link_key][oid]
                other_entity_map['link_count'] -= 1
            for other_entity_map, links, link_key, oid in links_deleted:
                links[link_key][oid] = None
                other_entity_map['link_count'] += 1
            raise

    def _create_schevo_structures(self):
        """Create or update Schevo structures in the database."""
        root = self._root
        PDict = self._PDict
        if 'SCHEVO' not in root:
            schevo = root['SCHEVO'] = PDict()
            schevo['format'] = 1
            schevo['version'] = 0
            schevo['extent_name_id'] = PDict()
            schevo['extents'] = PDict()
            schevo['schema_source'] = None

    def _schema_format_compatibility_check(self, schema):
        """Return None if the given schema is compatible with this database
        engine's format, or raise an error when the first incompatibility
        is found.

        - `schema`: The schema to check.
        """
        # Check for fields that may_store_entities but are not Entity fields.
        E = schema.E
        for e_name in E:
            EntityClass = E[e_name]
            for f_name, f_class in EntityClass._field_spec.iteritems():
                if (f_class.may_store_entities
                    and not issubclass(f_class, EntityField)
                    ):
                    reason = (
                        'Field %r in Entity class %r may store entities '
                        'but is a %r field and not an Entity field; this '
                        'is unsupported in format 1 databases.'
                        ) % (f_name, e_name, f_class.__name__)
                    raise error.UnsupportedFieldType(reason)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
