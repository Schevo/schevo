"""Schevo database, format 2."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import operator
import os
import random

try:
    import louie
except ImportError:
    # Dummy module.
    class louie(object):
        @staticmethod
        def send(*args, **kw):
            pass


from schevo import base
from schevo import change
from schevo.change import CREATE, UPDATE, DELETE
from schevo.constant import UNASSIGNED
from schevo.counter import schema_counter
from schevo import error
from schevo.entity import Entity
from schevo.expression import Expression
from schevo.extent import Extent
from schevo.field import Entity as EntityField
from schevo.field import not_fget
from schevo.lib import module
from schevo.mt.dummy import dummy_lock
from schevo.namespace import NamespaceExtension
from schevo.placeholder import Placeholder
import schevo.schema
from schevo.signal import TransactionExecuted
from schevo.trace import log
from schevo.transaction import (
    CallableWrapper, Combination, Initialize, Populate, Transaction)


class Database(base.Database):
    """Schevo database, format 2.

    See doc/SchevoInternalDatabaseStructures.txt for detailed information on
    data structures.
    """

    # By default, don't dispatch signals.  Set to True to dispatch
    # TransactionExecuted signals.
    dispatch = False

    # See dummy_lock documentation.
    read_lock = dummy_lock
    write_lock = dummy_lock

    def __init__(self, backend):
        """Create a database.

        - `backend`: The storage backend instance to use.
        """
        self._sync_count = 0
        self.backend = backend
        # Aliases to classes in the backend.
        self._BTree = backend.BTree
        self._PDict = backend.PDict
        self._PList = backend.PList
        self._conflict_exceptions = getattr(backend, 'conflict_exceptions', ())
        self._root = backend.get_root()
        # Shortcuts to coarse-grained commit and rollback.
        self._commit = backend.commit
        self._rollback = backend.rollback
        # Keep track of schema modules remembered.
        self._remembered = []
        # Initialization.
        self._create_schevo_structures()
        self._commit()
        # Index to extent instances assigned by _sync.
        self._extents = {}
        # Index to entity classes assigned by _sync.
        self._entity_classes = {}
        # Vars used in transaction processing.
        self._bulk_mode = False
        self._executing = []
        # Shortcuts.
        schevo = self._root['SCHEVO']
        self._extent_name_id = schevo['extent_name_id']
        self._extent_maps_by_id = schevo['extents']
        self._update_extent_maps_by_name()
        # Plugin support.
        self._plugins = []

    def __repr__(self):
        return '<Database %r :: V %r>' % (self.label, self.version)

    @property
    def _extent_id_name(self):
        return dict((v, k) for k, v in self._extent_name_id.items())

    def close(self):
        """Close the database."""
        assert log(1, 'Stopping plugins.')
        p = self._plugins
        while p:
            assert log(2, 'Stopping', p)
            p.pop().close()
        assert log(1, 'Closing storage.')
        self.backend.close()
        remembered = self._remembered
        while remembered:
            module.forget(remembered.pop())

    def execute(self, *transactions, **kw):
        """Execute transaction(s)."""
        if self._executing:
            # Pass-through outer transactions.
            return self._execute(*transactions, **kw)
        else:
            # Try outer transactions up to 10 times if conflicts occur.
            remaining_attempts = 10
            while remaining_attempts > 0:
                try:
                    return self._execute(*transactions, **kw)
                except self._conflict_exceptions:
                    remaining_attempts -= 1
                    for tx in transactions:
                        tx._executing = False
            raise error.BackendConflictError()

    def _execute(self, *transactions, **kw):
        strict = kw.get('strict', True)
        executing = self._executing
        if len(transactions) == 0:
            raise RuntimeError('Must supply at least one transaction.')
        if len(transactions) > 1:
            if not executing:
                raise RuntimeError(
                    'Must supply only one top-level transaction.')
            else:
                # Multiple transactions are treated as a single
                # transaction containing subtransactions.
                tx = Combination(transactions)
        else:
            tx = transactions[0]
        if tx._executed:
            raise error.TransactionAlreadyExecuted(tx)
            raise error.TransactionAlreadyExecuted('%r already executed.' % tx)
        if not executing:
            # Bulk mode can only be set on an outermost transaction
            # and effects all inner transactions.
            self._bulk_mode = kw.get('bulk_mode', False)
            # Outermost transaction must be executed strict.
            strict = True
        # Bulk mode minimizes transaction metadata.
        bulk_mode = self._bulk_mode
        executing.append(tx)
        assert log(1, 'Begin executing [%i]' % len(executing), tx)
        try:
            retval = tx._execute(self)
            assert log(2, 'Result was', repr(retval))
            # Enforce any indices relaxed by the transaction.
            for extent_name, index_spec in frozenset(tx._relaxed):
                assert log(2, 'Enforcing index', extent_name, index_spec)
                self._enforce_index_field_ids(extent_name, *index_spec)
            # If the transaction must be executed with strict
            # validation, perform that validation now.
            if strict:
                c = tx._changes_requiring_validation
                assert log(
                    2, 'Validating', len(c), 'changes requiring validation')
                self._validate_changes(c)
        except Exception, e:
            assert log(1, e, 'was raised; undoing side-effects.')
            if bulk_mode:
                assert log(2, 'Bulk Mode transaction; storage rollback.')
                self._rollback()
            elif len(executing) == 1:
                assert log(2, 'Outer transaction; storage rollback.')
                self._rollback()
            else:
                assert log(2, 'Inner transaction; inverting.')
                inversions = tx._inversions
                while len(inversions):
                    method, args, kw = inversions.pop()
                    # Make sure the inverse operation doesn't append
                    # an inversion itself.
                    self._executing = None
                    # Perform the inversion.
                    method(*args, **kw)
                    # Restore state.
                    self._executing = executing
            # Get rid of the current transaction on the stack since
            # we're done undoing it.
            executing.pop()
            # Allow exception to bubble up.
            raise
        assert log(1, ' Done executing [%i]' % len(executing), tx)
        tx._executed = True
        # Post-transaction
        if bulk_mode and len(executing) > 1:
            assert log(2, 'Bulk Mode inner transaction.')
            e2 = executing[-2]
            e1 = executing[-1]
            if not strict:
                e2._changes_requiring_validation.extend(
                    e1._changes_requiring_validation)
        elif bulk_mode:
            assert log(2, 'Bulk Mode outer transaction; storage commit.')
            # Done executing the outermost transaction.  Use
            # Durus-based commit.
            self._commit()
        elif len(executing) > 1:
            assert log(2, 'Inner transaction; record inversions and changes.')
            # Append the inversions from this transaction to the next
            # outer transaction.
            e2 = executing[-2]
            e1 = executing[-1]
            e2._inversions.extend(e1._inversions)
            # Also append the changes made from this transaction.
            e2._changes_requiring_notification.extend(
                e1._changes_requiring_notification)
            if not strict:
                e2._changes_requiring_validation.extend(
                    e1._changes_requiring_validation)
        else:
            assert log(2, 'Outer transaction; storage commit.')
            # Done executing the outermost transaction.  Use
            # Durus-based commit.
            self._commit()
            # Send a signal if told to do so.
            if self.dispatch:
                assert log(2, 'Dispatching TransactionExecuted signal.')
                louie.send(TransactionExecuted, sender=self, transaction=tx)
        executing.pop()
        return retval

    def extent(self, extent_name):
        """Return the named extent instance."""
        return self._extents[extent_name]

    def extent_names(self):
        """Return a sorted list of extent names."""
        return sorted(self._extent_maps_by_name.keys())

    def extents(self):
        """Return a list of extent instances sorted by name."""
        extent = self.extent
        return [extent(name) for name in self.extent_names()]

    def pack(self):
        """Pack the database."""
        if os.environ.get('SCHEVO_NOPACK', '').strip() != '1':
            self.backend.pack()

    def populate(self, sample_name=''):
        """Populate the database with sample data."""
        tx = Populate(sample_name)
        self.execute(tx)

    @property
    def format(self):
        return self._root['SCHEVO']['format']

    @property
    def schema_source(self):
        return self._root['SCHEVO']['schema_source']

    @property
    def version(self):
        return self._root['SCHEVO']['version']

    def _get_label(self):
        SCHEVO = self._root['SCHEVO']
        if 'label' not in SCHEVO:
            # Older database, no label stored in it.
            return u'Schevo Database'
        else:
            return SCHEVO['label']

    def _set_label(self, new_label):
        if self._executing:
            raise error.DatabaseExecutingTransaction(
                'Cannot change database label while executing a transaction.')
        self._root['SCHEVO']['label'] = unicode(new_label)
        self._commit()

    label = property(_get_label, _set_label)
    _label = property(_get_label, _set_label)

    def _append_change(self, typ, extent_name, oid):
        executing = self._executing
        if executing:
            info = (typ, extent_name, oid)
            tx = executing[-1]
            tx._changes_requiring_validation.append(info)
            if not self._bulk_mode:
                tx._changes_requiring_notification.append(info)

    def _append_inversion(self, method, *args, **kw):
        """Append an inversion to a transaction if one is being
        executed."""
        if self._bulk_mode:
            return
        executing = self._executing
        if executing:
            executing[-1]._inversions.append((method, args, kw))

    def _by_entity_oids(self, extent_name, *index_spec):
        """Return a list of OIDs from an extent sorted by index_spec."""
        extent_map = self._extent_map(extent_name)
        indices = extent_map['indices']
        index_map = extent_map['index_map']
        # Separate index_spec into two tuples, one containing field
        # names and one containing 'ascending' bools.
        field_names = []
        ascending = []
        for field_name in index_spec:
            if field_name.startswith('-'):
                field_names.append(field_name[1:])
                ascending.append(False)
            else:
                field_names.append(field_name)
                ascending.append(True)
        index_spec = _field_ids(extent_map, field_names)
        if index_spec not in indices:
            # Specific index not found; look for an index where
            # index_spec matches the beginning of that index's spec.
            if index_spec not in index_map:
                # None found.
                raise error.IndexDoesNotExist(
                    extent_name,
                    _field_names(extent_map, index_spec),
                    )
            # Use the first index found.
            index_spec = index_map[index_spec][0]
        oids = []
        unique, branch = indices[index_spec]
        _walk_index(branch, ascending, oids)
        return oids

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
            # Create fields_by_id dict with field-id:field-value items.
            fields_by_id = PDict()
            for name, value in fields.iteritems():
                field_id = field_name_id[name]
                fields_by_id[field_id] = value
            # Create related_entities_by_id dict with
            # field-id:related-entities items.
            new_links = []
            nl_append = new_links.append
            related_entities_by_id = PDict()
            for name, related_entity_set in related_entities.iteritems():
                field_id = field_name_id[name]
                related_entities_by_id[field_id] = related_entity_set
                for placeholder in related_entity_set:
                    other_extent_id = placeholder.extent_id
                    other_oid = placeholder.oid
                    nl_append((field_id, other_extent_id, other_oid))
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
            entity_map['fields'] = fields_by_id
            # XXX flesh out links based on who is capable of linking
            # to this one.
            entity_map['link_count'] = 0
            entity_map['links'] = PDict()
            entity_map['related_entities'] = related_entities_by_id
            entity_map['rev'] = rev
            # Update the extent.
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
        all_field_ids = set(extent_map['field_id_name'].iterkeys())
        extent_id = extent_map['id']
        extent_name_id = self._extent_name_id
        extent_maps_by_id = self._extent_maps_by_id
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
        related_entities = entity_map['related_entities']
        referrer_extent_id = extent_name_id[extent_name]
        for referrer_field_id, related_set in related_entities.iteritems():
            # If a field once existed, but no longer does, there will
            # still be a related entity set for it in related_entities.
            # Only process the fields that still exist.
            if referrer_field_id in all_field_ids:
                for other_value in related_set:
                    # Remove the link to the other entity.
                    other_extent_id = other_value.extent_id
                    other_oid = other_value.oid
                    link_key = (referrer_extent_id, referrer_field_id)
                    other_extent_map = extent_maps_by_id[other_extent_id]
                    if other_oid in other_extent_map['entities']:
                        other_entity_map = other_extent_map[
                            'entities'][other_oid]
                        links = other_entity_map['links']
                        other_links = links[link_key]
                        # The following check is due to scenarios like this:
                        # Entity A and entity B are both being deleted in a
                        # cascade delete scenario.  Entity B refers to entity A.
                        # Entity A has already been deleted.  Entity B is now
                        # being deleted. We must now ignore any information
                        # about entity A that is attached to entity B.
                        if oid in other_links:
                            del other_links[oid]
                        other_entity_map['link_count'] -= 1
        del extent_map['entities'][oid]
        extent_map['len'] -= 1
        # Allow inversion of this operation.
        self._append_inversion(
            self._create_entity, extent_name, old_fields,
            old_related_entities, oid, old_rev)
        # Keep track of changes.
        append_change = self._append_change
        append_change(DELETE, extent_name, oid)

    def _enforce_index(self, extent_name, *index_spec):
        """Call _enforce_index after converting index_spec from field
        names to field IDs."""
        extent_map = self._extent_map(extent_name)
        index_spec = _field_ids(extent_map, index_spec)
        return self._enforce_index_field_ids(extent_name, *index_spec)

    def _enforce_index_field_ids(self, extent_name, *index_spec):
        """Validate and begin enforcing constraints on the specified
        index if it was relaxed within the currently-executing
        transaction."""
        executing = self._executing
        if not executing:
            # No-op if called outside a transaction.
            return
        # Find the index to re-enforce.
        extent_map = self._extent_map(extent_name)
        indices = extent_map['indices']
        if index_spec not in indices:
            raise error.IndexDoesNotExist(
                extent_name,
                _field_names(extent_map, index_spec),
                )
        # Find out if it has been relaxed.
        current_txn = executing[-1]
        relaxed = self._relaxed[extent_name]
        txns, added = relaxed.get(index_spec, ([], []))
        if not txns:
            # Was never relaxed; no-op.
            return
        if current_txn in txns:
            current_txn._relaxed.remove((extent_name, index_spec))
            txns.remove(current_txn)
        # If no more transactions have relaxed this index, enforce it.
        if not txns:
            BTree = self._BTree
            for _extent_map, _index_spec, _oid, _field_values in added:
                _index_validate(_extent_map, _index_spec, _oid, _field_values,
                                BTree)

    def _entity(self, extent_name, oid):
        """Return the entity instance."""
        EntityClass = self._entity_classes[extent_name]
        return EntityClass(oid)

    def _entity_field(self, extent_name, oid, name):
        """Return the value of a field in an entity in named extent
        with given OID."""
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_name_id = extent_map['field_name_id']
        field_id = field_name_id[name]
        value = entity_map['fields'][field_id]
        return value

    def _entity_field_rev(self, extent_name, oid, name):
        """Return a tuple of (value, rev) of a field in an entity in
        named extent with given OID."""
        value = self._entity_field(extent_name, oid, name)
        rev = self._entity_rev(extent_name, oid)
        return value, rev

    def _entity_fields(self, extent_name, oid):
        """Return a dictionary of field values for an entity in
        `extent` with given OID."""
        entity_classes = self._entity_classes
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_id_name = extent_map['field_id_name']
        fields = {}
        for field_id, value in entity_map['fields'].iteritems():
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

    def _entity_links(self, extent_name, oid, other_extent_name=None,
                     other_field_name=None, return_count=False):
        """Return dictionary of (extent_name, field_name): entity_list
        pairs, or list of linking entities if `other_extent_name` and
        `other_field_name` are supplied; return link count instead if
        `return_count` is True."""
        assert log(1, '_entity_links', extent_name, oid, other_extent_name,
                   other_field_name, return_count)
        entity_classes = self._entity_classes
        entity_map = self._entity_map(extent_name, oid)
        entity_links = entity_map['links']
        extent_maps_by_id = self._extent_maps_by_id
        if other_extent_name is not None and other_field_name is not None:
            # Both extent name and field name were provided.
            other_extent_map = self._extent_map(other_extent_name)
            other_extent_id = other_extent_map['id']
            try:
                other_field_id = other_extent_map['field_name_id'][
                    other_field_name]
            except KeyError:
                raise error.FieldDoesNotExist(
                    other_extent_name, other_field_name)
            key = (other_extent_id, other_field_id)
            # Default to a dict since it has the same API as a BTree
            # for our use but is faster and will stay empty anyway.
            btree = entity_links.get(key, {})
            if return_count:
                count = len(btree)
                assert log(2, 'returning len(btree)', count)
                return count
            else:
                EntityClass = entity_classes[other_extent_name]
                others = [EntityClass(oid) for oid in btree]
                return others
        # Shortcut if we only care about the count, with no specificity.
        link_count = entity_map['link_count']
        if return_count and other_extent_name is None:
            assert log(2, 'returning link_count', link_count)
            return link_count
        # Build links tree.
        specific_extent_name = other_extent_name
        if return_count:
            links = 0
        else:
            links = {}
        if link_count == 0:
            # No links; no need to traverse.
            assert log(2, 'no links - returning', links)
            return links
        for key, btree in entity_links.iteritems():
            other_extent_id, other_field_id = key
            other_extent_map = extent_maps_by_id[other_extent_id]
            other_extent_name = other_extent_map['name']
            if (specific_extent_name
                and specific_extent_name != other_extent_name
                ):
                assert log(2, 'Skipping', other_extent_name)
                continue
            if return_count:
                links += len(btree)
            else:
                other_field_name = other_extent_map['field_id_name'][
                    other_field_id]
                if specific_extent_name:
                    link_key = other_field_name
                else:
                    link_key = (other_extent_name, other_field_name)
                EntityClass = entity_classes[other_extent_name]
                others = [EntityClass(oid) for oid in btree]
                if others:
                    links[link_key] = others
        if return_count:
            assert log(2, 'returning links', links)
        return links

    def _entity_related_entities(self, extent_name, oid):
        """Return a dictionary of related entity sets for an entity in
        `extent` with given OID."""
        entity_classes = self._entity_classes
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_id_name = extent_map['field_id_name']
        related_entities = {}
        for field_id, related in entity_map['related_entities'].iteritems():
            # During database evolution, it may turn out that fields
            # get removed.  For time efficiency reasons, Schevo does
            # not iterate through all entities to remove existing
            # data.  Therefore, when getting entity fields from the
            # database here, ignore fields that exist in the entity
            # but no longer exist in the extent.
            field_name = field_id_name.get(field_id, None)
            if field_name:
                related_entities[field_name] = related
        return related_entities

    def _entity_rev(self, extent_name, oid):
        """Return the revision of an entity in `extent` with given
        OID."""
        entity_map = self._entity_map(extent_name, oid)
        return entity_map['rev']

    def _extent_contains_oid(self, extent_name, oid):
        extent_map = self._extent_map(extent_name)
        return oid in extent_map['entities']

    def _extent_len(self, extent_name):
        """Return the number of entities in the named extent."""
        extent_map = self._extent_map(extent_name)
        return extent_map['len']

    def _extent_next_oid(self, extent_name):
        """Return the next OID to be assigned in the named extent."""
        extent_map = self._extent_map(extent_name)
        return extent_map['next_oid']

    def _find_entity_oids(self, extent_name, criterion):
        """Return sequence of entity OIDs matching given field value(s)."""
        assert log(1, extent_name, criterion)
        extent_map = self._extent_map(extent_name)
        entity_maps = extent_map['entities']
        # No criterion: return all entities.
        if criterion is None:
            assert log(2, 'Return all oids.')
            return list(entity_maps.keys())
        # Equality intersection: use optimized lookup.
        try:
            criteria = criterion.single_extent_field_equality_criteria()
        except ValueError:
            pass
        else:
            extent_names = frozenset(key._extent for key in criteria)
            if len(extent_names) > 1:
                raise ValueError('Must use fields from same extent.')
            return self._find_entity_oids_field_equality(
                extent_name, criteria)
        # More complex lookup.
        return self._find_entity_oids_general_criterion(extent_name, criterion)

    def _find_entity_oids_general_criterion(self, extent_name, criterion):
        if (isinstance(criterion.left, Expression)
            and isinstance(criterion.right, Expression)
            ):
            left_oids = self._find_entity_oids_general_criterion(
                extent_name, criterion.left)
            right_oids = self._find_entity_oids_general_criterion(
                extent_name, criterion.right)
            return criterion.op(left_oids, right_oids)
        elif (isinstance(criterion.left, type)
              and issubclass(criterion.left, base.Field)
              ):
            return self._find_entity_oids_field_criterion(
                extent_name, criterion)
        else:
            raise ValueError('Cannot evaluate criterion', criterion)

    def _find_entity_oids_field_criterion(self, extent_name, criterion):
        extent_map = self._extent_map(extent_name)
        entity_maps = extent_map['entities']
        FieldClass, value, op = criterion.left, criterion.right, criterion.op
        # Make sure extent name matches.
        if FieldClass._extent.name != extent_name:
            raise ValueError(
                'Criterion extent does not match query extent.', criterion)
        # Optimize for equality and inequality.
        if op == operator.eq:
            return set(self._find_entity_oids_field_equality(
                extent_name, {FieldClass: value}))
        if op == operator.ne:
            all = entity_maps.keys()
            matching = self._find_entity_oids_field_equality(
                extent_name, {FieldClass: value})
            return set(all) - set(matching)
        # Create a writable field to convert the value and get its
        # _dump'd representation.
        field_id = extent_map['field_name_id'][FieldClass.name]
        EntityClass = self._entity_classes[extent_name]
        FieldClass = EntityClass._field_spec[FieldClass.name]
        class TemporaryField(FieldClass):
            readonly = False
        field = TemporaryField(None)
        field.set(value)
        value = field._dump()
        # Additional operators.
        # XXX: Brute force for now.
        if op in (operator.lt, operator.le, operator.gt, operator.ge):
            results = []
            append = results.append
            for oid, entity_map in entity_maps.iteritems():
                if op(entity_map['fields'].get(field_id, UNASSIGNED), value):
                    append(oid)
            return set(results)

    def _find_entity_oids_field_equality(self, extent_name, criteria):
        extent_map = self._extent_map(extent_name)
        entity_maps = extent_map['entities']
        EntityClass = self._entity_classes[extent_name]
        extent_name_id = self._extent_name_id
        indices = extent_map['indices']
        normalized_index_map = extent_map['normalized_index_map']
        field_id_name = extent_map['field_id_name']
        field_name_id = extent_map['field_name_id']
        # Convert from field_name:value to field_id:value.
        field_id_value = {}
        field_name_value = {}
        for field_class, value in criteria.iteritems():
            field_name = field_class.name
            try:
                field_id = field_name_id[field_name]
            except KeyError:
                raise error.FieldDoesNotExist(extent_name, field_name)
            # Create a writable field to convert the value and get its
            # _dump'd representation.
            class TemporaryField(field_class):
                readonly = False
            field = TemporaryField(None)
            field.set(value)
            value = field._dump()
            field_id_value[field_id] = value
            field_name_value[field_name] = value
        # Get results, using indexes and shortcuts where possible.
        results = []
        field_ids = tuple(sorted(field_id_value))
        assert log(3, 'field_ids', field_ids)
        len_field_ids = len(field_ids)
        # First, see if we can take advantage of entity links.
        if len_field_ids == 1:
            field_id = field_ids[0]
            field_name = field_id_name[field_id]
            value = field_name_value[field_name]
            if isinstance(value, Entity):
                # We can take advantage of entity links.
                entity_map = self._entity_map(value._extent.name, value._oid)
                entity_links = entity_map['links']
                extent_id = extent_map['id']
                key = (extent_id, field_id)
                linkmap = entity_links.get(key, {})
                results = linkmap.keys()
                return results
        # Next, see if the fields given can be found in an index. If
        # so, use the index to return matches.
        index_spec = None
        if field_ids in normalized_index_map:
            for spec in normalized_index_map[field_ids]:
                if len(spec) == len_field_ids:
                    index_spec = spec
                    break
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

    def _relax_index(self, extent_name, *index_spec):
        """Relax constraints on the specified index until a matching
        enforce_index is called, or the currently-executing
        transaction finishes, whichever occurs first."""
        executing = self._executing
        if not executing:
            raise RuntimeError('Indexes can only be relaxed inside '
                               'transaction execution.')
        # ID-ify the index_spec.
        extent_map = self._extent_map(extent_name)
        index_spec = _field_ids(extent_map, index_spec)
        # Find the index to relax.
        indices = extent_map['indices']
        if index_spec not in indices:
            raise error.IndexDoesNotExist(
                extent_name,
                _field_names(extent_map, index_spec),
                )
        # Keep track of the relaxation.
        current_txn = executing[-1]
        relaxed = self._relaxed[extent_name]
        txns, added = relaxed.setdefault(index_spec, ([], []))
        txns.append(current_txn)
        current_txn._relaxed.add((extent_name, index_spec))

    def _set_extent_next_oid(self, extent_name, next_oid):
        extent_map = self._extent_map(extent_name)
        extent_map['next_oid'] = next_oid

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
            updating_related = len(related_entities) > 0
            if updating_related:
                old_related_entities = self._entity_related_entities(
                    extent_name, oid)
            else:
                old_related_entities = {}
            old_rev = entity_map['rev']
            # Manage entity references.
            if updating_related:
                for name, related_entity_set in related_entities.iteritems():
                    field_id = field_name_id[name]
                    for placeholder in related_entity_set:
                        other_extent_id = placeholder.extent_id
                        other_oid = placeholder.oid
                        nl_append((field_id, other_extent_id, other_oid))
            # Get fields, and set UNASSIGNED for any fields that are
            # new since the last time the entity was stored.
            fields_by_id = entity_map['fields']
            all_field_ids = set(extent_map['field_id_name'])
            new_field_ids = all_field_ids - set(fields_by_id)
            fields_by_id.update(dict(
                (field_id, UNASSIGNED) for field_id in new_field_ids))
            # Create ephemeral fields for creating new mappings.
            new_fields_by_id = dict(fields_by_id)
            for name, value in fields.iteritems():
                new_fields_by_id[field_name_id[name]] = value
            if updating_related:
                new_related_entities_by_id = dict(
                    (field_name_id[name], related_entities[name])
                    for name in related_entities
                    )
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
            if updating_related:
                # Delete links from this entity to other entities.
                related_entities_by_id = entity_map['related_entities']
                referrer_extent_id = extent_name_id[extent_name]
                new_field_ids = frozenset(new_fields_by_id)
                for (referrer_field_id,
                     related_set) in related_entities_by_id.iteritems():
                    # If a field once existed, but no longer does, there will
                    # still be a related entity set for it in related_entities.
                    # Only process the fields that still exist.
                    if referrer_field_id in all_field_ids:
                        # Remove only the links that no longer exist.
                        new_related_entities = new_related_entities_by_id.get(
                            referrer_field_id, set())
                        for other_value in related_set - new_related_entities:
                            # Remove the link to the other entity.
                            other_extent_id = other_value.extent_id
                            other_oid = other_value.oid
                            link_key = (referrer_extent_id, referrer_field_id)
                            other_extent_map = extent_maps_by_id[
                                other_extent_id]
                            other_entity_map = other_extent_map['entities'][
                                other_oid]
                            links = other_entity_map['links']
                            other_links = links[link_key]
                            del other_links[oid]
                            other_entity_map['link_count'] -= 1
                            ld_append((other_entity_map, links, link_key, oid))
            # Create new index mappings.
            for index_spec in indices.iterkeys():
                field_values = tuple(new_fields_by_id[field_id]
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
            if updating_related:
                # Update links from this entity to another entity.
                referrer_extent_id = extent_name_id[extent_name]
                for referrer_field_id, other_extent_id, other_oid in new_links:
                    other_extent_map = extent_maps_by_id[other_extent_id]
                    try:
                        other_entity_map = other_extent_map['entities'][
                            other_oid]
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
                        mapping = links[link_key] = BTree()
                    else:
                        mapping = links[link_key]
                    if oid not in mapping:
                        # Only add the link if it's not already there.
                        links[link_key][oid] = None
                        other_entity_map['link_count'] += 1
                        lc_append((other_entity_map, links, link_key, oid))
            # Update actual fields and related entities.
            for name, value in fields.iteritems():
                fields_by_id[field_name_id[name]] = value
            if updating_related:
                for name, value in related_entities.iteritems():
                    related_entities_by_id[field_name_id[name]] = value
            # Update revision.
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

    def _create_extent(self, extent_name, field_names, entity_field_names,
                      key_spec=None, index_spec=None):
        """Create a new extent with a given name."""
        BTree = self._BTree
        PList = self._PList
        PDict = self._PDict
        if extent_name in self._extent_maps_by_name:
            raise error.ExtentExists(extent_name)
        if key_spec is None:
            key_spec = []
        if index_spec is None:
            index_spec = []
        extent_map = PDict()
        extent_id = self._unique_extent_id()
        indices = extent_map['indices'] = PDict()
        extent_map['index_map'] = PDict()
        normalized_index_map = extent_map[
            'normalized_index_map'] = PDict()
        extent_map['entities'] = BTree()
        field_id_name = extent_map['field_id_name'] = PDict()
        field_name_id = extent_map['field_name_id'] = PDict()
        extent_map['id'] = extent_id
        extent_map['len'] = 0
        extent_map['name'] = extent_name
        extent_map['next_oid'] = 1
        self._extent_name_id[extent_name] = extent_id
        self._extent_maps_by_id[extent_id] = extent_map
        self._extent_maps_by_name[extent_name] = extent_map
        # Give each field name a unique ID.
        for name in field_names:
            field_id = self._unique_field_id(extent_name)
            field_id_name[field_id] = name
            field_name_id[name] = field_id
        # Convert field names to field IDs in key spec and create
        # index structures.
        for field_names in key_spec:
            i_spec = _field_ids(extent_map, field_names)
            _create_index(extent_map, i_spec, True, BTree, PList)
        # Convert field names to field IDs in index spec and create
        # index structures.
        for field_names in index_spec:
            i_spec = _field_ids(extent_map, field_names)
            # Although we tell it unique=False, it may find a subset
            # key, which will cause this superset to be unique=True.
            _create_index(extent_map, i_spec, False, BTree, PList)
        # Convert field names to field IDs for entity field names.
        extent_map['entity_field_ids'] = _field_ids(
            extent_map, entity_field_names)

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
        for oid, entity_map in extent_map['entities'].iteritems():
            related_entities = entity_map['related_entities'].iteritems()
            for field_id, related_entity_set in related_entities:
                for related_entity in related_entity_set:
                    rel_extent_id = related_entity.extent_id
                    rel_oid = related_entity.oid
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

    def _create_schevo_structures(self):
        """Create or update Schevo structures in the database."""
        root = self._root
        PDict = self._PDict
        if 'SCHEVO' not in root:
            schevo = root['SCHEVO'] = PDict()
            schevo['format'] = 2
            schevo['version'] = 0
            schevo['extent_name_id'] = PDict()
            schevo['extents'] = PDict()
            schevo['schema_source'] = None

    def _entity_map(self, extent_name, oid):
        """Return an entity PDict corresponding to named
        `extent` and OID."""
        extent_map = self._extent_map(extent_name)
        try:
            entity_map = extent_map['entities'][oid]
        except KeyError:
            raise error.EntityDoesNotExist(extent_name, oid=oid)
        return entity_map

    def _entity_extent_map(self, extent_name, oid):
        """Return an (entity PDict, extent PDict)
        tuple corresponding to named `extent` and OID."""
        extent_map = self._extent_map(extent_name)
        try:
            entity_map = extent_map['entities'][oid]
        except KeyError:
            raise error.EntityDoesNotExist(extent_name, oid=oid)
        return entity_map, extent_map

    def _evolve(self, schema_source, version):
        """Evolve the database to a new schema definition.

        - `schema_source`: String containing the source code for the
          schema to be evolved to.

        - `version`: Integer with the version number of the new schema
          source.  Must be the current database version, plus 1.
        """
        current_version = self.version
        expected_version = current_version + 1
        if version != self.version + 1:
            raise error.DatabaseVersionMismatch(
                current_version, expected_version, version)
        def call(module, name):
            fn = getattr(module, name, None)
            if callable(fn):
                tx = CallableWrapper(fn)
                # Trick the database into not performing a
                # storage-level commit.
                self._executing = [Transaction()]
                try:
                    self.execute(tx)
                finally:
                    self._executing = []
        # Load the new schema.
        schema_name = schema_counter.next_schema_name()
        schema_module = self._import_from_source(schema_source, schema_name)
        try:
            # Execute `before_evolve` function if defined.
            call(schema_module, 'before_evolve')
            # Perform first pass of evolution.
            self._sync(schema_source, initialize=False, commit=False,
                       evolving=True)
            # Execute `during_evolve` function if defined.
            call(self._schema_module, 'during_evolve')
            # Perform standard schema synchronization.
            self._sync(schema_source, initialize=False, commit=False,
                       evolving=False)
            # Execute `after_evolve` function if defined.
            call(self._schema_module, 'after_evolve')
        except:
            self._rollback()
            # Re-raise exception.
            raise
        else:
            self._root['SCHEVO']['version'] = version
            self._commit()

    def _extent_map(self, extent_name):
        """Return an extent PDict corresponding to `extent_name`."""
        try:
            return self._extent_maps_by_name[extent_name]
        except KeyError:
            raise error.ExtentDoesNotExist(extent_name)

    def _import_from_source(self, source, module_name):
        """Import a schema module from a string containing source code."""
        # Now that prerequisites are loaded, load this schema.
        schema_module = module.from_string(source, module_name)
        # Remember the schema module.
        module.remember(schema_module)
        self._remembered.append(schema_module)
        # Expose this database to the schema module.
        schema_module.db = self
        # Return the schema module.
        return schema_module

    def _initialize(self):
        """Populate the database with initial data."""
        tx = Initialize()
        self.execute(tx)

    def _on_open(self):
        """Allow schema to run code after the database is opened."""
        if hasattr(self, '_schema_module'):
            # An empty database created without a schema source will
            # not have a schema module.
            fn = getattr(self._schema_module, 'on_open', None)
            if callable(fn):
                fn(self)

    def _remove_stale_links(self, extent_id, field_id, FieldClass):
        # Remove links from this field to other entities that are held
        # in the structures for those other entities.
        allow = FieldClass.allow
        for other_name in allow:
            other_extent_map = self._extent_map(other_name)
            other_entities = other_extent_map['entities']
            for other_entity in other_entities.itervalues():
                other_link_count = other_entity['link_count']
                other_links = other_entity['links']
                referrer_key = (extent_id, field_id)
                if referrer_key in other_links:
                    referrers = other_links[referrer_key]
                    other_link_count -= len(referrers)
                    del other_links[referrer_key]
                other_entity['link_count'] = other_link_count

    def _schema_format_compatibility_check(self, schema):
        """Return None if the given schema is compatible with this
        database engine's format, or raise an error when the first
        incompatibility is found.

        - `schema`: The schema to check.
        """
        pass

    def _sync(self, schema_source=None, schema_version=None,
              initialize=True, commit=True, evolving=False):
        """Synchronize the database with a schema definition.

        - `schema_source`: String containing the source code for a
          schema.  If `None`, the schema source contained in the
          database itself will be used.

        - `schema_version`: If set, the schema version to use for a
          newly-created database.  If set to something other than None
          for an existing database, raises a ValueError.

        - `initialize`: True if a new database should be populated
          with initial values defined in the schema.

        - `commit`: True if a successful synchronization should commit
          to the storage backend.  False if the caller of `_sync` will
          handle this task.

        - `evolving`: True if the synchronization is occuring during a
          database evolution.
        """
        self._sync_count += 1
        sync_schema_changes = True
        locked = False
        try:
            SCHEVO = self._root['SCHEVO']
            # Import old schema.
            old_schema_source = SCHEVO['schema_source']
            if old_schema_source is not None:
                old_schema_module = None
                schevo.schema.start(self, evolving)
                locked = True
                schema_name = schema_counter.next_schema_name()
                try:
                    old_schema_module = self._import_from_source(
                        old_schema_source, schema_name)
                finally:
                    old_schema = schevo.schema.finish(self, old_schema_module)
                    locked = False
                self._old_schema = old_schema
                self._old_schema_module = old_schema_module
            else:
                old_schema = self._old_schema = None
                old_schema_module = self._old_schema_module = None
            # Import current schema.
            if schema_source is None:
                schema_source = old_schema_source
                if schema_source is None:
                    # No schema source was specified and this is a new
                    # database, so _sync becomes a no-op.
                    return
                else:
                    # No schema source was specified and this is an
                    # existing database with a defined schema.
                    sync_schema_changes = False
            if schema_source == old_schema_source:
                # If the same source, it'll be the same schema.
                schema = old_schema
                schema_module = old_schema_module
            else:
                schema_module = None
                schevo.schema.start(self, evolving)
                locked = True
                schema_name = schema_counter.next_schema_name()
                try:
                    schema_module = self._import_from_source(
                        schema_source, schema_name)
                finally:
                    schema = schevo.schema.finish(self, schema_module)
                    locked = False
            self._schema_format_compatibility_check(schema)
            self.schema = schema
            self._schema_module = schema_module
            # Expose database-level namespaces and make the database
            # the object that the namespace is associated with, for
            # more effective use with repr().
            self.q = schema.q
            self.q._i = self
            self.t = schema.t
            self.t._i = self
            self.Q = schema.Q
            self.Q._i = self
            # Create an extenders namespace.
            self.x = DatabaseExtenders('x', self, self._schema_module)
            # If the schema has changed then sync with it.
            if sync_schema_changes:
                # Update schema source stored in database.
                SCHEVO['schema_source'] = schema_source
                self._sync_extents(schema, evolving)
            # Create extent instances.
            E = schema.E
            extents = self._extents = {}
            relaxed = self._relaxed = {}
            entity_classes = self._entity_classes = {}
            extent_name_id = self._extent_name_id
            for e_name in self.extent_names():
                e_id = extent_name_id[e_name]
                EntityClass = E[e_name]
                extent = Extent(self, e_name, e_id, EntityClass)
                extents[e_id] = extents[e_name] = extent
                relaxed[e_name] = {}
                entity_classes[e_id] = entity_classes[e_name] = EntityClass
                # Decorate this Database instance to support the
                # following syntax within schema code, for example:
                # tx = db.Foo.t.create()
                setattr(self, e_name, extent)
            # Initialize a new database.
            if SCHEVO['version'] == 0:
                if schema_version is None:
                    schema_version = 1
                SCHEVO['version'] = schema_version
                # Populate with initial data, unless overridden such as
                # when importing from an XML file.
                if initialize:
                    self._initialize()
            elif schema_version is not None:
                # Do not allow schema_version to differ from existing
                # version if opening an existing database.
                if SCHEVO['version'] != schema_version:
                    raise ValueError(
                        'Existing database; schema_version must be set to '
                        'None or to the current version of the database.')
        except:
            if locked:
                schevo.schema.import_lock.release()
            if commit:
                self._rollback()
            raise
        else:
            if commit:
                self._commit()
            self._on_open()

    def _sync_extents(self, schema, evolving):
        """Synchronize the extents based on the schema."""
        E = schema.E
        old_schema = self._old_schema
        # Rename extents in the database whose entity class definition
        # has a `_was` attribute.
        in_schema = set(iter(E))
        if evolving:
            for extent_name in in_schema:
                EntityClass = E[extent_name]
                was_named = EntityClass._was
                if was_named is not None:
                    # Change the name of the existing extent in the
                    # database.
                    extent_name_id = self._extent_name_id
                    extent_map = self._extent_map(was_named)
                    extent_id = extent_map['id']
                    extent_map['name'] = extent_name
                    del extent_name_id[was_named]
                    extent_name_id[extent_name] = extent_id
            self._update_extent_maps_by_name()
        # Create extents that are in schema but not in db.
        in_db = set(self.extent_names())
        to_create = in_schema - in_db
        for extent_name in to_create:
            if extent_name.startswith('_'):
                # Do not bother with hidden classes.
                continue
            EntityClass = E[extent_name]
            field_spec = EntityClass._field_spec
            field_names = field_spec.keys()
            entity_field_names = []
            for name in field_names:
                FieldClass = field_spec[name]
                if FieldClass.may_store_entities and not FieldClass.fget:
                    entity_field_names.append(name)
            key_spec = EntityClass._key_spec
            index_spec = EntityClass._index_spec
            self._create_extent(
                extent_name, field_names, entity_field_names,
                key_spec, index_spec)
        # Remove extents that are in the db but not in the schema.
        in_db = set(self.extent_names())
        to_remove = in_db - in_schema
        for extent_name in to_remove:
            if extent_name.startswith('_'):
                # Do not bother with hidden classes.
                continue
            # Check for links made from entities in this extent to
            # other entities, where the other entities maintain those
            # link structures.
            if old_schema:
                extent_map = self._extent_map(extent_name)
                field_name_id = extent_map['field_name_id']
                extent_id = extent_map['id']
                # The old extent name will not exist in the old schema
                # if it was an evolve_only class definition, and we
                # are not in the process of evolving.
                if extent_name in old_schema.E:
                    for old_field_name, FieldClass in (
                        old_schema.E[extent_name]._field_spec.iteritems()
                        ):
                        old_field_id = field_name_id[old_field_name]
                        if issubclass(FieldClass, EntityField):
                            self._remove_stale_links(
                                extent_id, old_field_id, FieldClass)
            # Delete the extent.  XXX: Need to skip system extents?
            self._delete_extent(extent_name)
        # Update entity_field_ids, field_id_name, and field_name_id
        # for all extents.
        for extent_name in self.extent_names():
            EntityClass = E[extent_name]
            field_spec = EntityClass._field_spec
            extent_map = self._extent_map(extent_name)
            extent_id = extent_map['id']
            entity_field_ids = set(extent_map['entity_field_ids'])
            field_id_name = extent_map['field_id_name']
            field_name_id = extent_map['field_name_id']
            # Rename fields with 'was' attribute.
            existing_field_names = set(field_name_id.keys())
            new_field_names = set(field_spec.keys())
            if evolving:
                for field_name in new_field_names:
                    FieldClass = field_spec[field_name]
                    was_named = FieldClass.was
                    if was_named is not None:
                        if was_named not in existing_field_names:
                            raise error.FieldDoesNotExist(
                                extent_name, was_named, field_name)
                        # Rename the field.
                        field_id = field_name_id[was_named]
                        del field_name_id[was_named]
                        field_name_id[field_name] = field_id
                        field_id_name[field_id] = field_name
                        # Remove from the set of existing field names.
                        existing_field_names.remove(was_named)
            # Remove fields that no longer exist.
            old_field_names = existing_field_names - new_field_names
            for old_field_name in old_field_names:
                old_field_id = field_name_id[old_field_name]
                if old_schema:
                    # Get the field spec for the field being deleted.
                    # It may not exist in the old schema, if it was only
                    # there in an _evolve_only class definition.
                    if extent_name in old_schema.E:
                        FieldClass = old_schema.E[extent_name]._field_spec.get(
                            old_field_name, None)
                        if (FieldClass is not None and
                            issubclass(FieldClass, EntityField)):
                            self._remove_stale_links(
                                extent_id, old_field_id, FieldClass)
                if old_field_id in entity_field_ids:
                    entity_field_ids.remove(old_field_id)
                del field_name_id[old_field_name]
                del field_id_name[old_field_id]
            # Create fields IDs for new fields.
            existing_field_names = set(field_name_id.keys())
            fields_to_create = new_field_names - existing_field_names
            for field_name in fields_to_create:
                field_id = self._unique_field_id(extent_name)
                field_name_id[field_name] = field_id
                field_id_name[field_id] = field_name
                # Check for entity field.
                FieldClass = field_spec[field_name]
                if (FieldClass.may_store_entities and not FieldClass.fget):
                    entity_field_ids.add(field_id)
            extent_map['entity_field_ids'] = tuple(entity_field_ids)
        # Update index specs for all extents.
        for extent_name in self.extent_names():
            # Skip system extents.
            EntityClass = E[extent_name]
            key_spec = EntityClass._key_spec
            index_spec = EntityClass._index_spec
            self._update_extent_key_spec(extent_name, key_spec, index_spec)

    def _unique_extent_id(self):
        """Return an unused random extent ID."""
        extent_name_id = self._extent_name_id
        while True:
            extent_id = random.randint(0, 2**31)
            if extent_id not in extent_name_id:
                return extent_id

    def _unique_field_id(self, extent_name):
        """Return an unused random field ID."""
        field_id_name = self._extent_map(extent_name)['field_id_name']
        while True:
            field_id = random.randint(0, 2**31)
            if field_id not in field_id_name:
                return field_id

    def _update_extent_maps_by_name(self):
        extent_maps_by_name = self._extent_maps_by_name = {}
        for extent in self._extent_maps_by_id.itervalues():
            extent_maps_by_name[extent['name']] = extent

    def _update_extent_key_spec(self, extent_name, key_spec, index_spec):
        """Update an existing extent to match given key spec."""
        extent_map = self._extent_map(extent_name)
        entities = extent_map['entities']
        indices = extent_map['indices']
        key_spec_ids = [_field_ids(extent_map, field_names)
                        for field_names in key_spec]
        index_spec_ids = [_field_ids(extent_map, field_names)
                          for field_names in index_spec]
        BTree = self._BTree
        PList = self._PList
        # Convert key indices that have been changed to non-unique
        # incides.
        for i_spec in index_spec_ids:
            if i_spec not in key_spec and i_spec in indices:
                unique, branch = indices[i_spec]
                indices[i_spec] = (False, branch)
        # Create new key indices for those that don't exist.
        for i_spec in key_spec_ids:
            if i_spec not in indices:
                # Create a new unique index and populate it.
                _create_index(
                    extent_map, i_spec, True, BTree, PList)
                for oid in entities:
                    fields_by_id = entities[oid]['fields']
                    field_values = tuple(fields_by_id.get(field_id, UNASSIGNED)
                                         for field_id in i_spec)
                    _index_add(extent_map, i_spec, None, oid, field_values,
                               BTree)
        # Create new non-unique indices for those that don't exist.
        for i_spec in index_spec_ids:
            if i_spec not in indices:
                # Create a new non-unique index and populate it.
                _create_index(extent_map, i_spec, False, BTree, PList)
                for oid in entities:
                    fields_by_id = entities[oid]['fields']
                    field_values = tuple(fields_by_id.get(field_id, UNASSIGNED)
                                         for field_id in i_spec)
                    _index_add(extent_map, i_spec, None, oid, field_values,
                               BTree)
        # Remove key indices that no longer exist.
        to_remove = set(indices) - set(key_spec_ids + index_spec_ids)
        for i_spec in to_remove:
            _delete_index(extent_map, i_spec)
        # Check non-unique indices to see if any are supersets of
        # unique indices.  If any found, change them to 'unique' and
        # validate them.
        #
        # XXX: Needs testing.
        for i_spec, (unique, branch) in list(indices.items()):
            # Look for unique index supersets of this index, and make
            # it unique if any exist.
            if not unique:
                spec_set = set(index_spec)
                for i_spec in indices:
                    compare_set = set(i_spec)
                    if compare_set.issuperset(spec_set):
                        unique = True
                        break
                if unique:
                    # Should be unique but isn't; alter and validate.
                    indices[i_spec] = (unique, branch)
                    for oid in entities:
                        fields_by_id = entities[oid]['fields']
                        field_values = tuple(fields_by_id[field_id]
                                             for field_id in i_spec)
                        _index_validate(extent_map, i_spec, oid, field_values,
                                        BTree)

    def _validate_changes(self, changes):
        # Here we are applying rules defined by the entity itself, not
        # the transaction, since transactions may relax certain rules.
        entity_classes = self._entity_classes
        changes = change.normalize(changes)
        for typ, extent_name, oid in changes:
            if typ in (CREATE, UPDATE):
                EntityClass = entity_classes[extent_name]
                entity = EntityClass(oid)
                field_map = entity.s.field_map(not_fget)
                for field in field_map.itervalues():
                    field.validate(field._value)

    def _reset_all(self):
        """Clear all entities, indices, etc. in the database.

        FOR USE WITH SINGLE-SCHEMA UNIT TESTS.

        NOT INDENDED FOR GENERAL USE.
        """
        BTree = self._BTree
        for extent_name in self.extent_names():
            extent_map = self._extent_map(extent_name)
            extent_map['entities'] = BTree()
            extent_map['len'] = 0
            extent_map['next_oid'] = 1
            indices = extent_map['indices']
            for index_spec, (unique, index_tree) in list(indices.items()):
                indices[index_spec] = (unique, BTree())
        self._commit()
        self.dispatch = Database.dispatch
        self.label = Database.label
        self._initialize()
        self._on_open()


def _create_index(extent_map, index_spec, unique, BTree, PList):
    """Create a new index in the extent with the given spec and
    uniqueness flag."""
    assert log(1, extent_map['name'])
    assert log(1, 'index_spec', index_spec)
    indices = extent_map['indices']
    index_map = extent_map['index_map']
    normalized_index_map = extent_map['normalized_index_map']
    # Look for unique index subsets of this index, and make it unique
    # if any exist.
    if not unique:
        spec_set = set(index_spec)
        for i_spec in indices:
            compare_set = set(i_spec)
            if compare_set.issubset(spec_set):
                unique = True
                break
    # Continue with index creation.
    assert log(2, 'unique', unique)
    assert log(
        2, 'normalized_index_map.keys()', list(normalized_index_map.keys()))
    partial_specs = _partial_index_specs(index_spec)
    assert log(3, 'partial_specs', partial_specs)
    normalized_specs = _normalized_index_specs(partial_specs)
    assert log(3, 'normalized_specs', normalized_specs)
    index_root = BTree()
    indices[index_spec] = (unique, index_root)
    for partial_spec in partial_specs:
        L = index_map.setdefault(partial_spec, PList())
        L.append(index_spec)
    for normalized_spec in normalized_specs:
        L = normalized_index_map.setdefault(normalized_spec, PList())
        L.append(index_spec)
    assert log(
        2, 'normalized_index_map.keys()', list(normalized_index_map.keys()))


def _delete_index(extent_map, index_spec):
    indices = extent_map['indices']
    index_map = extent_map['index_map']
    normalized_index_map = extent_map['normalized_index_map']
    partial_specs = _partial_index_specs(index_spec)
    normalized_specs = _normalized_index_specs(partial_specs)
    del indices[index_spec]
    for partial_spec in partial_specs:
        L = index_map[partial_spec]
        L.remove(index_spec)
        if not L:
            del index_map[partial_spec]
    for normalized_spec in normalized_specs:
        if normalized_spec in normalized_index_map:
            L = normalized_index_map[normalized_spec]
            L.remove(index_spec)
            if not L:
                del normalized_index_map[normalized_spec]


def _field_ids(extent_map, field_names):
    """Convert a (field-name, ...) tuple to a (field-id, ...)
    tuple for the given extent map."""
    field_name_id = extent_map['field_name_id']
    return tuple(field_name_id[name] for name in field_names)


def _field_names(extent_map, field_ids):
    """Convert a (field-id, ...) tuple to a (field-name, ...) tuple
    for the given extent map."""
    field_id_name = extent_map['field_id_name']
    return tuple(field_id_name[id] for id in field_ids)


def _index_add(extent_map, index_spec, relaxed, oid, field_values, BTree):
    """Add an entry to the specified index, of entity oid having the
    given values in order of the index spec."""
    indices = extent_map['indices']
    unique, branch = indices[index_spec]
    # Traverse branches to find a leaf.
    for field_id, field_value in zip(index_spec, field_values):
        if field_value in branch:
            branch = branch[field_value]
        else:
            new_branch = BTree()
            branch[field_value] = new_branch
            branch = new_branch
    # Raise error if unique index and not an empty leaf.
    if unique and len(branch) and relaxed is None:
        _index_clean(extent_map, index_spec, field_values)
        raise error.KeyCollision(
            extent_map['name'],
            _field_names(extent_map, index_spec),
            field_values,
            )
    # Inject the OID into the leaf.
    branch[oid] = True
    # Keep track of the addition if relaxed.
    if relaxed is not None:
        relaxed.append((extent_map, index_spec, oid, field_values))


def _index_clean(extent_map, index_spec, field_values):
    """Remove stale branches from the specified index."""
    indices = extent_map['indices']
    unique, branch = indices[index_spec]
    _index_clean_branch(branch, field_values)


def _index_clean_branch(branch, field_values):
    """Recursively clean a branch of stale child branches."""
    branch_value = field_values[0]
    child_values = field_values[1:]
    if branch_value in branch:
        if child_values:
            # Clean children first.
            _index_clean_branch(branch[branch_value], child_values)
        # Clean ourself if empty.
        if not len(branch[branch_value]):
            del branch[branch_value]


def _index_remove(extent_map, index_spec, oid, field_values):
    """Remove an entry from the specified index, of entity oid having
    the given values in order of the index spec."""
    indices = extent_map['indices']
    unique, branch = indices[index_spec]
    # Traverse branches to find a leaf.
    for field_id, field_value in zip(index_spec, field_values):
        if field_value not in branch:
            # Was never indexed for some reason, so stop traversing.
            break
        branch = branch[field_value]
    if oid in branch:
        del branch[oid]
    _index_clean(extent_map, index_spec, field_values)


def _index_validate(extent_map, index_spec, oid, field_values, BTree):
    """Validate the index entry for uniqueness."""
    indices = extent_map['indices']
    unique, branch = indices[index_spec]
    # Traverse branches to find a leaf.
    for field_id, field_value in zip(index_spec, field_values):
        if field_value in branch:
            branch = branch[field_value]
        else:
            new_branch = BTree()
            branch[field_value] = new_branch
            branch = new_branch
    # Raise error if unique index and not an empty leaf.
    if unique and len(branch) > 1:
        _index_clean(extent_map, index_spec, field_values)
        raise error.KeyCollision(
            extent_map['name'],
            _field_names(extent_map, index_spec),
            field_values,
            )


def _normalized_index_specs(index_specs):
    """Return normalized index specs based on index_specs."""
    return [tuple(sorted(spec)) for spec in index_specs]


def _partial_index_specs(index_spec):
    """Return a list of partial index specs based on index_spec."""
    return [tuple(index_spec[:x+1]) for x in xrange(len(index_spec))]


def _walk_index(branch, ascending_seq, result_list):
    """Recursively walk a branch of an index, appending OIDs found to
    result_list.

    - `branch`: The branch to start at.
    - `ascending_seq`: The sequence of ascending flags corresponding
      to the current branch.
    - `result_list`: List to append OIDs to.
    """
    if len(ascending_seq):
        # We are at a branch.
        ascending, inner_ascending = ascending_seq[0], ascending_seq[1:]
        if ascending:
            for key, inner_branch in branch.iteritems():
                _walk_index(inner_branch, inner_ascending, result_list)
        else:
            # XXX: SchevoZodb backend requires us to use
            # `reversed(branch.keys())` rather than
            # `reversed(branch)`.
            keys = reversed(branch.keys())
            for key in keys:
                inner_branch = branch[key]
                _walk_index(inner_branch, inner_ascending, result_list)
    else:
        # We are at a leaf.
        result_list.extend(branch.iterkeys())


class DatabaseExtenders(NamespaceExtension):
    """Methods that extend the functionality of a database."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, name, instance, schema_module):
        NamespaceExtension.__init__(self, name, instance)
        # Expose functions through this namespace.
        for name in dir(schema_module):
            # Extender functions always have x_ prefix.
            if name.startswith('x_'):
                function = getattr(schema_module, name)
                # Drop the 'x_' prefix.
                name = name[2:]
                self._set(name, function)


def convert_from_format1(backend):
    """Convert a database from format 1 to format 2.

    - `backend`: Open backend connection to the database to convert.
      Assumes that the database has already been verified to be a format 1
      database.
    """
    root = backend.get_root()
    schevo = root['SCHEVO']
    extent_name_id = schevo['extent_name_id']
    extents = schevo['extents']
    # For each extent in the database...
    for extent_name, extent_id in extent_name_id.iteritems():
        extent = extents[extent_id]
        entity_field_ids = frozenset(extent['entity_field_ids'])
        # For each entity in the extent...
        for entity_oid, entity in extent['entities'].iteritems():
            fields = entity['fields']
            related_entities = entity['related_entities'] = backend.PDict()
            # For each entity field in the entity...
            for field_id in entity_field_ids:
                related_entity_set = set()
                # If the value is an entity reference, turn it into a
                # Placeholder.  Store the value, and also add it to the
                # set of related entities.
                value = fields.get(field_id, UNASSIGNED)
                if isinstance(value, tuple):
                    p = Placeholder.new(*value)
                    fields[field_id] = p
                    related_entity_set.add(p)
                related_entities[field_id] = frozenset(related_entity_set)
        # For each index...
        indices = extent['indices']
        for index_spec, (unique, index_tree) in indices.iteritems():
            # Convert all (extent_id, oid) tuples to Placeholder instances in
            # extent indices.
            _convert_index_from_format1(
                entity_field_ids, index_spec, index_tree)
    # Bump format from 1 to 2.
    schevo['format'] = 2


def _convert_index_from_format1(entity_field_ids, index_spec, index_tree):
    current_field_id, next_index_spec = index_spec[0], index_spec[1:]
    is_entity_field = current_field_id in entity_field_ids
    for key, child_tree in index_tree.items():
        if is_entity_field and isinstance(key, tuple):
            # Convert entity tuple to Placeholder.
            p = Placeholder.new(*key)
            # Replace old key with new key.
            del index_tree[key]
            index_tree[p] = child_tree
        # Recurse into child structures if not at a leaf.
        if len(next_index_spec) > 0:
            _convert_index_from_format1(
                entity_field_ids, next_index_spec, child_tree)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
