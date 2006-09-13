"""Schevo database.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import os
import pkg_resources
import random

import louie

from schevo import base
from schevo import change
from schevo.change import CREATE, UPDATE, DELETE
from schevo.constant import UNASSIGNED
from schevo import error
from schevo.entity import Entity
from schevo.extent import Extent
from schevo.field import Entity as EntityField
from schevo.field import not_fget
from schevo import icon
from schevo.lib import module
from schevo.namespace import NamespaceExtension
import schevo.schema
from schevo.signal import TransactionExecuted
from schevo.store.btree import BTree
from schevo.store.connection import Connection
from schevo.store.file_storage import FileStorage
from schevo.store.persistent_dict import PersistentDict as PDict
from schevo.store.persistent_list import PersistentList as PList
from schevo.trace import log
from schevo.transaction import Combination, Initialize, Populate


def inject(filename, schema_source, version):
    fs = FileStorage(filename)
    conn = Connection(fs)
    root = conn.get_root()
    schevo = root['SCHEVO']
    schevo['schema_source'] = schema_source
    schevo['version'] = version
    conn.commit()
    fs.close()


def open(filename=None, schema_source=None, initialize=True, label='',
         fp=None):
    """Return an open database."""
    if fp is not None:
        fs = FileStorage(fp=fp)
    else:
        fs = FileStorage(filename)
    conn = Connection(fs)
    db = Database(conn)
    if label:
        db.label = label
    db._sync(schema_source, initialize)
    # Install icon support.
    icon.install(db)
    db._on_open()
    return db


class dummy_lock(object):
    """Dummy class for read_lock and write_lock objects in a database,
    so that code can be written to be multi-thread-ready but still be
    run in cases where the schevo.mt plugin is not installed."""
    
    def release(self):
        pass


class schema_counter(object):
    """Schema counter singleton.

    This is a class instead of a global, because globals won't work
    because of the binding done by optimize.bind_all.
    """
    
    _current = 0

    @classmethod
    def next(cls):
        c = cls._current
        cls._current += 1
        return c

    @classmethod
    def next_schema_name(cls):
        return 'schevo-db-schema-%i' % cls.next()    


class Database(base.Database):
    """Schevo database, using Durus as an object store.

    See doc/reference/database.txt for detailed information on data
    structures, or visit http://docs.schevo.org/trunk/reference/database.html
    """

    label = 'Schevo Database'

    # By default, don't dispatch signals.  Set to True to dispatch
    # TransactionExecuted signals.
    dispatch = False

    # See dummy_lock documentation.
    read_lock = dummy_lock
    write_lock = dummy_lock

    def __init__(self, connection):
        """Create a database.

        - `connection`: The Durus connection to use.
        """
        self.connection = connection
        self._root = connection.get_root()
        # Shortcuts to coarse-grained commit and rollback.
        self._commit = connection.commit
        self._rollback = connection.abort
        # Keep track of schema modules remembered.
        self._remembered = []
        # Initialization.
        self._create_schevo_structures()
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
        extent_maps_by_name = self._extent_maps_by_name = {}
        for extent in self._extent_maps_by_id.itervalues():
            extent_maps_by_name[extent['name']] = extent
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
        self.connection.storage.close()
        del self.connection
        remembered = self._remembered
        while remembered:
            module.forget(remembered.pop())

    def execute(self, *transactions, **kw):
        """Execute transaction(s)."""
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
            for extent_name, index_spec in tx._relaxed:
                assert log(2, 'Enforcing index', extent_name, index_spec)
                self._enforce_index(extent_name, index_spec)
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
        self.connection.pack()

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
                    'Index %r not found in extent %r.'
                    % (_field_names(extent_map, index_spec), extent_name))
            # Use the first index found.
            index_spec = index_map[index_spec][0]
        oids = []
        unique, branch = indices[index_spec]
        _walk_index(branch, ascending, oids)
        return oids
    
    def _create_entity(self, extent_name, fields, oid=None, rev=None):
        """Create a new entity in an extent; return the oid."""
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
        try:
            if oid is None:
                oid = extent_map['next_oid']
                extent_map['next_oid'] += 1
            if rev is None:
                rev = 0
            if oid in entities:
                raise error.EntityExists(
                    'OID %r already exists in %r' % (oid, extent_name))
            # Create dict with field-id:field-value items.
            fields_by_id = PDict()
            new_links = []
            nl_append = new_links.append
            for name, value in fields.iteritems():
                field_id = field_name_id[name]
                # Handle entity reference fields.
                if (field_id in entity_field_ids
                    and isinstance(value, Entity)):
                    # Dereference entity.
                    other_extent_id = extent_name_id[value._extent.name]
                    other_oid = value._oid
                    value = (other_extent_id, other_oid)
                    nl_append((field_id, other_extent_id, other_oid))
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
                _index_add(extent_map, index_spec, relaxed, oid, field_values)
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
                    raise error.EntityDoesNotExist(
                        'Entity referenced in %r does not exist.'
                        % field_name)
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
        # unless all references are merely from ourself.
        for (other_extent_id, other_field_id), others in links.items():
            for other_oid in others:
                # Give up as soon as we find one outside reference.
                if (other_extent_id, other_oid) != (extent_id, oid):
                    msg = 'Cannot delete; other entities depend on this one.'
                    raise error.DeleteRestricted(msg)
        # Get old values for use in a potential inversion.
        old_fields = self._entity_fields(extent_name, oid)
        old_rev = entity_map['rev']
        # Remove index mappings.
        indices = extent_map['indices']
        fields_by_id = entity_map['fields']
        for index_spec in indices.iterkeys():
            field_values = tuple(fields_by_id[f_id] for f_id in index_spec)
            _index_remove(extent_map, index_spec, oid, field_values)
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
        del extent_map['entities'][oid]
        extent_map['len'] -= 1
        # Allow inversion of this operation.
        self._append_inversion(self._create_entity, extent_name, old_fields,
                               oid, old_rev)
        # Keep track of changes.
        append_change = self._append_change
        append_change(DELETE, extent_name, oid)

    def _enforce_index(self, extent_name, *index_spec):
        """Validate and begin enforcing constraints on the specified
        index if it was relaxed within the currently-executing
        transaction."""
        executing = self._executing
        if not executing:
            # No-op if called outside a transaction.
            return
        # ID-ify the index_spec.
        extent_map = self._extent_map(extent_name)
        index_spec = _field_ids(extent_map, index_spec)
        # Find the index to re-enforce.
        indices = extent_map['indices']
        if index_spec not in indices:
            raise error.IndexDoesNotExist(
                'Index %r not found in extent %r.'
                % (_field_names(extent_map, index_spec), extent_name))
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
            for _extent_map, _index_spec, _oid, _field_values in added:
                _index_validate(_extent_map, _index_spec, _oid, _field_values)

    def _entity(self, extent_name, oid):
        """Return the entity instance."""
        EntityClass = self._entity_classes[extent_name]
        return EntityClass(oid)

    def _entity_field(self, extent_name, oid, name):
        """Return the value of a field in an entity in named extent
        with given OID."""
        entity_map, extent_map = self._entity_extent_map(extent_name, oid)
        field_name_id = extent_map['field_name_id']
        entity_field_ids = extent_map['entity_field_ids']
        field_id = field_name_id[name]
        value = entity_map['fields'][field_id]
        if field_id in entity_field_ids and isinstance(value, tuple):
            extent_id, oid = value
            EntityClass = self._entity_classes[extent_id]
            value = EntityClass(oid)
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
        entity_field_ids = extent_map['entity_field_ids']
        fields = {}
        for field_id, value in entity_map['fields'].iteritems():
            if field_id in entity_field_ids and isinstance(value, tuple):
                extent_id, oid = value
                EntityClass = entity_classes[extent_id]
                value = EntityClass(oid)
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
                    'Field %r does not exist in extent %r' % (
                    other_field_name, other_extent_name))
            key = (other_extent_id, other_field_id)
            # Default to a dict since it has the same API as a BTree
            # for our use but is faster and will stay empty anyway.
            btree = entity_links.get(key, {})
            if return_count:
                count = len(btree.keys()) # XXX Optimization opportunity.
                assert log(2, 'returning len(btree.keys())', count)
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
                links += len(btree.keys()) # XXX: Optimization opportunity.
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

    def _find_entity_oids(self, extent_name, **criteria):
        """Return list of entity OIDs matching given field value(s)."""
        assert log(1, extent_name, criteria)
        extent_map = self._extent_map(extent_name)
        entity_maps = extent_map['entities']
        EntityClass = self._entity_classes[extent_name]
        if not criteria:
            # Return all of them.
            assert log(2, 'Return all oids.')
            return entity_maps.keys()
        extent_name_id = self._extent_name_id
        indices = extent_map['indices']
        assert log(3, 'indices.keys()', indices.keys())
        normalized_index_map = extent_map['normalized_index_map']
        assert log(3, 'normalized_index_map.keys()',
                   normalized_index_map.keys())
        entity_field_ids = extent_map['entity_field_ids']
        field_name_id = extent_map['field_name_id']
        # Convert from field_name:value to field_id:value.
        field_id_value = {}
        field_spec = EntityClass._field_spec
        for field_name, value in criteria.iteritems():
            try:
                field_id = field_name_id[field_name]
            except KeyError:
                raise error.FieldDoesNotExist(
                    'Field %r does not exist for %r' % (
                    field_name, extent_name))
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
                    assert log(3, field_value, 'not found in', branch.keys())
                    match = False
                    break
                branch = branch[field_value]
            if match:
                # Now we're at a leaf that matches all of the
                # criteria, so return the OIDs in that leaf.
                results = branch.keys()
        else:
            # Fields aren't indexed, so use brute force.
            assert log(2, 'Use brute force.')
            append = results.append
            for oid, entity_map in entity_maps.iteritems():
                fields = entity_map['fields']
                match = True
                for field_id, value in field_id_value.iteritems():
                    if fields[field_id] != value:
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
                'Index %r not found in extent %r.'
                % (_field_names(extent_map, index_spec), extent_name))
        # Keep track of the relaxation.
        current_txn = executing[-1]
        relaxed = self._relaxed[extent_name]
        txns, added = relaxed.setdefault(index_spec, ([], []))
        txns.append(current_txn)
        current_txn._relaxed.add((extent_name, index_spec))

    def _set_extent_next_oid(self, extent_name, next_oid):
        extent_map = self._extent_map(extent_name)
        extent_map['next_oid'] = next_oid

    def _update_entity(self, extent_name, oid, fields, rev=None):
        """Update an existing entity in an extent."""
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
        try:
            # Get old values for use in a potential inversion.
            old_fields = self._entity_fields(extent_name, oid)
            old_rev = entity_map['rev']
            # Dereference entities.
            for name, value in fields.items():
                field_id = field_name_id[name]
                if (field_id in entity_field_ids and
                    isinstance(value, Entity)
                    ):
                    # Dereference entity.
                    other_extent_id = extent_name_id[value._extent.name]
                    other_oid = value._oid
                    value = (other_extent_id, other_oid)
                    nl_append((field_id, other_extent_id, other_oid))
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
                _index_add(extent_map, index_spec, relaxed, oid, field_values)
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
                    raise error.EntityDoesNotExist(
                        'Entity referenced in %r does not exist.'
                        % field_name)
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
            self._append_inversion(self._update_entity, extent_name, oid,
                                   old_fields, old_rev)
            # Keep track of changes.
            append_change = self._append_change
            append_change(UPDATE, extent_name, oid)
        except:
            # Revert changes made during update attempt.
            for _e, _i, _o, _f in indices_added:
                _index_remove(_e, _i, _o, _f)
            for _e, _i, _r, _o, _f in indices_removed:
                _index_add(_e, _i, _r, _o, _f)
            for other_entity_map, links, link_key, oid in links_created:
                del links[link_key][oid]
                other_entity_map['link_count'] -= 1
            for other_entity_map, links, link_key, oid in links_deleted:
                links[link_key][oid] = None
                other_entity_map['link_count'] += 1
            raise

    def _create_extent(self, extent_name, field_names, entity_field_names,
                      key_spec=None, index_spec=None, commit=True):
        """Create a new extent with a given name."""
        if extent_name in self._extent_maps_by_name:
            raise error.ExtentExists('%r already exists.' % extent_name)
        if key_spec is None:
            key_spec = []
        if index_spec is None:
            index_spec = []
        extent_map = PDict()
        extent_id = self._unique_extent_id()
        indices = extent_map['indices'] = PDict()
        extent_map['index_map'] = PDict()
        normalized_index_map = extent_map['normalized_index_map'] = PDict()
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
            _create_index(extent_map, i_spec, True)
        # Convert field names to field IDs in index spec and create
        # index structures.
        for field_names in index_spec:
            i_spec = _field_ids(extent_map, field_names)
            # Although we tell it unique=False, it may find a subset
            # key, which will cause this superset to be unique=True.
            _create_index(extent_map, i_spec, False)
        # Convert field names to field IDs for entity field names.
        extent_map['entity_field_ids'] = _field_ids(
            extent_map, entity_field_names)
        if commit:
            self._commit()

    def _delete_extent(self, extent_name):
        """Remove a named extent."""
        # XXX: Need to check for links to any entity in this extent,
        # and fail to remove it if so.
        extent_map = self._extent_map(extent_name)
        extent_id = extent_map['id']
        del self._extent_name_id[extent_name]
        del self._extent_maps_by_id[extent_id]
        del self._extent_maps_by_name[extent_name]
        self._commit()

    def _create_schevo_structures(self):
        """Create or update Schevo structures in the database."""
        root = self._root
        if 'SCHEVO' not in root.keys():
            schevo = root['SCHEVO'] = PDict()
            schevo['version'] = 0
            schevo['extent_name_id'] = PDict()
            schevo['extents'] = PDict()
            schevo['schema_source'] = None
            self._commit()
        if 'format' not in root['SCHEVO']:
            root['SCHEVO']['format'] = 1

    def _entity_map(self, extent_name, oid):
        """Return an entity PDict corresponding to named
        `extent` and OID."""
        extent_map = self._extent_map(extent_name)
        try:
            entity_map = extent_map['entities'][oid]
        except KeyError:
            raise error.EntityDoesNotExist(
                'OID %r does not exist in %r' % (oid, extent_name))
        return entity_map

    def _entity_extent_map(self, extent_name, oid):
        """Return an (entity PDict, extent PDict)
        tuple corresponding to named `extent` and OID."""
        extent_map = self._extent_map(extent_name)
        try:
            entity_map = extent_map['entities'][oid]
        except KeyError:
            raise error.EntityDoesNotExist(
                'OID %r does not exist in %r' % (oid, extent_name))
        return entity_map, extent_map

    def _extent_map(self, extent_name):
        """Return an extent PDict corresponding to `extent_name`."""
        try:
            return self._extent_maps_by_name[extent_name]
        except KeyError:
            raise error.ExtentDoesNotExist('%r does not exist.' % extent_name)

    def _import_from_source(self, source, module_name=''):
        """Import a schema module from a string containing source code."""
        # Look through source lines and find imports.
        for line in source.splitlines():
            if line.startswith('_import('):
                # XXX: This algorithm could be much more elegant.
                #
                # Split by comma.
                # "_import('Requirement', 'name', 2, ...)" ->
                # ["_import('Requirement'",
                #  " 'name'",
                #  " 2",
                #  " ...)",
                #  ]
                parts = line.strip().split(',')
                if parts and parts[0].startswith('_import('):
                    part0parts = parts[0].split("'")
                    requirement = part0parts[1]
                    part1parts = parts[1].split("'")
                    name = part1parts[1]
                    part2parts = parts[2].split(')')
                    version = int(part2parts[0])
                    self._import_named_schema(requirement, name, version)
        # Now that prerequisites are loaded, load this schema.
        schema_module = module.from_string(source, module_name)
        # Remember the schema module.
        module.remember(schema_module)
        self._remembered.append(schema_module)
        # Expose this database to the schema module.
        schema_module.db = self
        # Return the schema module.
        return schema_module

    def _import_named_schema(self, requirement, name, version):
        """Import a schema module from a named exported schema."""
        # Read the module source.
        dist = pkg_resources.get_distribution(requirement)
        entry_point = dist.get_entry_info('schevo.schema_export', name)
        if entry_point:
            pkg_name = entry_point.module_name
            __import__(pkg_name)
            pkg = sys.modules[pkg_name]
            pkg_dirname = os.path.dirname(pkg.__file__)
            # Import from source.
            schema_filename = os.path.join(
                pkg_dirname, 'schema_%03i.py' % version)
            source = file(schema_filename, 'rU').read()
            schema_name = schema_counter.next_schema_name()
            schema_module = self._import_from_source(source, schema_name)
            self._imported_schemata[
                (requirement, name, version)] = schema_module
            return schema_module
        else:
            # XXX: raise exception?
            return None

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
        # Remove links from this field to other
        # entities that are held in the structures for
        # those other entities.
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
                    other_link_count -= len(referrers.keys())
                    del other_links[referrer_key]
                other_entity['link_count'] = other_link_count

    def _sync(self, schema_source=None, initialize=True):
        """Synchronize the database with a schema definition.

        - `schema_source`: String containing the source code for a
          schema.  If `None`, the schema source contained in the
          database itself will be used.

        - `initialize`: True if a new database should be populated
          with initial values defined in the schema.
        """
        sync_schema_changes = True
        locked = False
        try:
            SCHEVO = self._root['SCHEVO']
            # Import old schema.
            old_schema_source = SCHEVO['schema_source']
            if old_schema_source is not None:
                old_schema_module = None
                schevo.schema.start(self)
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
                # XXX
                # Temporary code to deal with older schemata.
                schema_source = schema_source.replace("""\
from schevo import *
from schevo.namespace import schema_prep
schema_prep(locals())
""", """\
from schevo.schema import *
schevo.schema.prep(locals())
""")
                # /XXX
                schema_module = None
                schevo.schema.start(self)
                locked = True
                schema_name = schema_counter.next_schema_name()
                try:
                    schema_module = self._import_from_source(
                        schema_source, schema_name)
                finally:
                    schema = schevo.schema.finish(self, schema_module)
                    locked = False
            self.schema = schema
            self._schema_module = schema_module
            # Expose database-level namespaces.
            self.t = schema.t
            self.Q = schema.Q
            # Create an extenders namespace.
            self.x = DatabaseExtenders(self._schema_module)
            # If the schema has changed then sync with it.
            if sync_schema_changes:
                # Update schema source stored in database.
                SCHEVO['schema_source'] = schema_source
                self._sync_extents(schema)
            # Create extent instances.
            E = schema.E
            extents = self._extents = {}
            relaxed = self._relaxed = {}
            entity_classes = self._entity_classes = {}
            extent_name_id = self._extent_name_id
            for e_name in self.extent_names():
                e_id = extent_name_id[e_name]
                EntityClass = E[e_name]
                extent = Extent(self, e_name, EntityClass)
                extents[e_id] = extents[e_name] = extent
                relaxed[e_name] = {}
                entity_classes[e_id] = entity_classes[e_name] = EntityClass
                # Decorate this Database instance to support the
                # following syntax within schema code, for example:
                # tx = db.Foo.t.create()
                setattr(self, e_name, extent)
            # Initialize a new database.
            if SCHEVO['version'] == 0:
                SCHEVO['version'] = 1
                # Populate with initial data, unless overridden such as
                # when importing from an XML file.
                if initialize:
                    self._initialize()
        except:
            if locked:
                schevo.schema.import_lock.release()
            self._rollback()
            raise
        else:
            self._commit()

    def _sync_extents(self, schema):
        """Synchronize the extents based on the schema."""
        E = schema.E
        old_schema = self._old_schema
        # Determine which extents are in the schema and which are in
        # the database.
        in_db = set(self.extent_names())
        in_schema = set(iter(E))
        # Create extents that are in schema but not in db.
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
                if issubclass(field_spec[name], EntityField):
                    entity_field_names.append(name)
##                 if issubclass(field_spec[name][0], EntityField):
##                     entity_field_names.append(name)
            key_spec = EntityClass._key_spec
            index_spec = EntityClass._index_spec
            self._create_extent(
                extent_name, field_names, entity_field_names,
                key_spec, index_spec, commit=False)
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
            # Remove fields that no longer exist.
            existing_field_names = set(field_name_id.keys())
            new_field_names = set(field_spec.keys())
            old_field_names = existing_field_names - new_field_names
            for old_field_name in old_field_names:
                old_field_id = field_name_id[old_field_name]
                if old_schema:
                    # Get the field spec for the field being deleted.
                    FieldClass = old_schema.E[extent_name]._field_spec[
                        old_field_name]
                    if issubclass(FieldClass, EntityField):
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
                if issubclass(field_spec[field_name], EntityField):
                    entity_field_ids.add(field_id)
            extent_map['entity_field_ids'] = tuple(entity_field_ids)
        # Update index specs for all extents.
        for extent_name in self.extent_names():
            # Skip system extents.
            EntityClass = E[extent_name]
            key_spec = EntityClass._key_spec
            index_spec = EntityClass._index_spec
            # XXX Temporary.
            if 'indices' not in self._extent_map(extent_name):
                # Assume we need to upgrade.
                _upgrade_extent(self, extent_name)
            # /XXX
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

## This is how Zope does it:

##     def _generateId(self):
##         """Generate an id which is not yet taken.

##         This tries to allocate sequential ids so they fall into the
##         same BTree bucket, and randomizes if it stumbles upon a
##         used one.
##         """
##         while True:
##             if self._v_nextid is None:
##                 self._v_nextid = random.randint(0, 2**31)
##             uid = self._v_nextid
##             self._v_nextid += 1
##             if uid not in self.refs:
##                 return uid
##             self._v_nextid = None

    def _update_extent_key_spec(self, extent_name, key_spec, index_spec):
        """Update an existing extent to match given key spec."""
        extent_map = self._extent_map(extent_name)
        entities = extent_map['entities']
        indices = extent_map['indices']
        key_spec_ids = [_field_ids(extent_map, field_names)
                        for field_names in key_spec]
        index_spec_ids = [_field_ids(extent_map, field_names)
                          for field_names in index_spec]
        # Create new key indices for those that don't exist.
        for i_spec in key_spec_ids:
            if i_spec not in indices:
                # Create a new unique index and populate it.
                _create_index(extent_map, i_spec, True)
                for oid in entities:
                    fields_by_id = entities[oid]['fields']
                    field_values = tuple(fields_by_id.get(field_id, UNASSIGNED)
                                         for field_id in i_spec)
                    _index_add(extent_map, i_spec, None, oid, field_values)
        # Create new non-unique indices for those that don't exist.
        for i_spec in index_spec_ids:
            if i_spec not in indices:
                # Create a new non-unique index and populate it.
                _create_index(extent_map, i_spec, False)
                for oid in entities:
                    fields_by_id = entities[oid]['fields']
                    field_values = tuple(fields_by_id.get(field_id, UNASSIGNED)
                                         for field_id in i_spec)
                    _index_add(extent_map, i_spec, None, oid, field_values)
        # Remove key indices that no longer exist.
        to_remove = set(indices.keys()) - set(key_spec_ids + index_spec_ids)
        for i_spec in to_remove:
            _delete_index(extent_map, i_spec)
        # Check non-unique indices to see if any are supersets of
        # unique indices.  If any found, change them to 'unique' and
        # validate them.
        #
        # XXX: Needs testing.
        for i_spec, (unique, branch) in indices.items():
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
                        _index_validate(extent_map, i_spec, oid, field_values)
        
    def _validate_changes(self, changes):
        entity_classes = self._entity_classes
        changes = change.normalize(changes)
        for typ, extent_name, oid in changes:
            if typ in (CREATE, UPDATE):
                EntityClass = entity_classes[extent_name]
                entity = EntityClass(oid)
                field_map = entity.sys.field_map(not_fget)
                for field in field_map.itervalues():
                    field.validate(field._value)

    def _reset_all(self):
        """Clear all entities, indices, etc. in the database.

        FOR USE WITH UNIT TESTS.  NOT INDENDED FOR GENERAL USE.
        """
        for extent_name in self.extent_names():
            extent_map = self._extent_map(extent_name)
            extent_map['entities'] = BTree()
            extent_map['len'] = 0
            extent_map['next_oid'] = 1
            indices = extent_map['indices']
            for index_spec, (unique, index_tree) in indices.items():
                indices[index_spec] = (unique, BTree())
        self._commit()
        self.dispatch = Database.dispatch
        self.label = Database.label
        self._initialize()
        self._on_open()


def _create_index(extent_map, index_spec, unique):
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
    assert log(2, 'normalized_index_map.keys()', normalized_index_map.keys())
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
    assert log(2, 'normalized_index_map.keys()', normalized_index_map.keys())


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


def _index_add(extent_map, index_spec, relaxed, oid, field_values):
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
    if unique and branch.keys() and relaxed is None:
        _index_clean(extent_map, index_spec, field_values)
        raise error.KeyCollision(
            'Duplicate value %r for key %r on %r'
            % (field_values, _field_names(extent_map, index_spec),
               extent_map['name']),
            branch.keys()[0])
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
        if not branch[branch_value].keys():
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


def _index_validate(extent_map, index_spec, oid, field_values):
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
    if unique and len(branch.keys()) > 1:
        _index_clean(extent_map, index_spec, field_values)
        raise error.KeyCollision(
            'Duplicate value %r for key %r'
            % (field_values, _field_names(extent_map, index_spec)),
            None)


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
            keys = reversed(branch.keys())
            for key in keys:
                inner_branch = branch[key]
                _walk_index(inner_branch, inner_ascending, result_list)
    else:
        # We are at a leaf.
        result_list.extend(branch.iterkeys())
        

def _upgrade_extent(db, extent_name):
    # XXX: Temporary.
    #
    # Look for old altkey structures.
    extent_map = db._extent_map(extent_name)
    if 'alt_keys' in extent_map:
        print 'Updating indices for', extent_name, '...'
        print '  Creating new index structure.'
        extent_map['indices'] = PDict()
        extent_map['index_map'] = PDict()
        extent_map['normalized_index_map'] = PDict()
        key_spec = db.schema.E[extent_name]._key_spec
        for index_spec in key_spec:
            index_spec = _field_ids(extent_map, index_spec)
            print '  Creating new index for spec ', repr(
                _field_names(extent_map, index_spec)), 
            sys.stdout.flush()
            _create_index(extent_map, index_spec, True)
            entities = extent_map['entities']
            for oid in entities:
                fields_by_id = entities[oid]['fields']
                field_values = tuple(fields_by_id[field_id]
                                     for field_id in index_spec)
                _index_add(extent_map, index_spec, None, oid, field_values)
                if not (oid % 50):
                    sys.stdout.write('.')
                    sys.stdout.flush()
            print
        print '  Removing old altkey structures'
        del extent_map['alt_keys']
        print 'Committing.  This may take some time...'
        db._commit()
        print 'Done committing.'
        print


class DatabaseExtenders(NamespaceExtension):
    """Methods that extend the functionality of a database."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, schema_module):
        NamespaceExtension.__init__(self)
        # Expose functions through this namespace.
        for name in dir(schema_module):
            # Extender functions always have x_ prefix.
            if name.startswith('x_'):
                function = getattr(schema_module, name)
                # Drop the 'x_' prefix.
                name = name[2:]
                self._set(name, function)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2006 Orbtech, L.L.C.
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
