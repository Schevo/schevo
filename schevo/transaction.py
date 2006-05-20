"""Transaction classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.change import summarize
from schevo.constant import CASCADE, DEFAULT, RESTRICT, UNASSIGN, UNASSIGNED
from schevo.error import KeyCollision, DeleteRestricted, TransactionNotExecuted
from schevo import field
from schevo.fieldspec import (
    FieldDefinition, FieldSpecMap, field_spec_from_class)
from schevo.label import label, label_from_name
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo.trace import log


class Transaction(base.Transaction):

    __metaclass__ = schema_metaclass('T')

    _field_spec = FieldSpecMap()

    def __init__(self):
        self._changes_requiring_notification = []
        self._changes_requiring_validation = []
        self._executed = False
        self._fields = self._field_spec.field_map(instance=self)
        self._inversions = []
        self._relaxed = set()
        self.f = schevo.namespace.Fields(self)
        self.sys = TransactionSys(self)
        self.x = TransactionExtenders()

    def __getattr__(self, name):
        return self._fields[name].get()

    def __setattr__(self, name, value):
        if name == 'sys' or name.startswith('_') or len(name) == 1:
            return base.Transaction.__setattr__(self, name, value)
        else:
            self._fields[name].assign(value)

    def __str__(self):
        text = label(self)
        extent_name = self.sys.extent_name
        if extent_name is not None:
            text += ' :: %s' % extent_name
        return text

    @property
    def _changes(self):
        if not self._executed:
            raise TransactionNotExecuted()
        return self._changes_requiring_notification

    def _execute(self, db):
        """Override this in subclasses to provide actual transaction
        execution."""
        raise NotImplementedError

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(self._fields.keys())

    def _undo(self):
        """Return a transaction that can undo this one."""
        if not self._executed:
            raise TransactionNotExecuted(
                'A transaction must be executed before its undo transaction '
                'is requested.')
        # The default implementation is to return the inverse of this
        # transaction.
        return Inverse(self)
    
    def _update(self, fields):
        """Update fields and make sure they reference this instance."""
        self._fields.update(fields)
        # Make sure that the instance associated with each field is
        # this transaction, not some other object such as an entity
        # instance.
        for name in fields.iterkeys():
            self._fields[name]._instance = self

    def _update_all_fields(self, name, value):
        """Update the attribute `name` to `value` on all fields."""
        for field in self._fields.values():
            setattr(field, name, value)


class TransactionExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False


class TransactionSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_transaction']

    def __init__(self, transaction):
        NamespaceExtension.__init__(self)
        self._transaction = transaction

    @property
    def changes(self):
        return self._transaction._changes

    @property
    def executed(self):
        return self._transaction._executed

    @property
    def extent_name(self):
        if hasattr(self._transaction, '_extent_name'):
            return self._transaction._extent_name

    def fields(self):
        return self._transaction._fields
        
    def summarize(self):
        return summarize(self._transaction)


# --------------------------------------------------------------------


class Combination(Transaction):
    """A transaction that consists of several sub-transactions."""

    _label = u'Combination'

    def __init__(self, transactions):
        Transaction.__init__(self)
        self._transactions = transactions

    def _execute(self, db):
        results = []
        for tx in self._transactions:
            results.append(db.execute(tx))
        return results


_Create_Standard = 0
_Create_If_Necessary = 1
_Create_Or_Update = 2

class Create(Transaction):
    """Create a new entity instance."""

    _label = u'Create'

    _style = _Create_Standard

    def __init__(self, **kw):
        Transaction.__init__(self)
        fields = self._fields
        for name, value in kw.iteritems():
            # Bypass using field.assign(), so that validation does not
            # occur.  Programmatically passing in keyword arguments to
            # a transaction is given more trust than fields set via a
            # user interface.
            field = fields[name]
            field._value = field.convert(value)
            field.assigned = True
        self._setup()
        # Assign default values for fields that haven't yet been
        # assigned a value.
        for field in fields.itervalues():
            if not field.assigned and not field.readonly:
                default = field.default[0]
                while callable(default) and default is not UNASSIGNED:
                    default = default()
                field.assign(default)

    def _setup(self):
        """Override this in subclasses to customize a transaction."""
        pass

    def _after_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _before_execute(self, db):
        """Override this in subclasses to customize a transaction."""
        pass

    def _execute(self, db):
        self._before_execute(db)
        style = self._style
        extent_name = self._extent_name
        fields = self._fields.value_map()
        # Strip out unwanted fields.
        fget_fields = self._fget_fields
        field_spec = self._EntityClass._field_spec
        for name in fields.keys():
            if name in fget_fields or name not in field_spec:
                del fields[name]
        if style == _Create_Standard:
            oid = db._create_entity(extent_name, fields)
        else:
            oid = None
            extent = db.extent(extent_name)
            default_key = extent.default_key
            if default_key is None:
                msg = '%s does not have a default key.' % (extent_name,)
                raise RuntimeError(msg)
            criteria = {}
            for name in default_key:
                criteria[name] = fields[name]
            entity = extent.findone(**criteria)
            if entity is not None:
                # Entity already exists.
                self._oid = entity._oid
                if style == _Create_If_Necessary:
                    return entity
                elif style == _Create_Or_Update:
                    entity = db.execute(entity.t.update(**fields))
                    return entity
                else:
                    raise RuntimeError('_style is not set correctly.')
            else:
                oid = db._create_entity(extent_name, fields)
        self._oid = oid
        entity = db._entity(extent_name, oid)
        self._after_execute(db, entity)
        return entity


class Delete(Transaction):
    """Delete an existing entity instance."""

    _label = u'Delete'

    def __init__(self, entity):
        Transaction.__init__(self)
        self._entity = entity
        self.sys._set('count', entity.sys.count)
        self.sys._set('links', entity.sys.links)
        self.sys._set('old', entity)
        fields = entity.sys.fields(include_readonly_fget=False)
        self._update(fields)
        self._update_all_fields('readonly', True)
        self._setup()

    def _setup(self):
        """Override this in subclasses to customize a transaction."""
        pass

    def _after_execute(self, db):
        """Override this in subclasses to customize a transaction."""
        pass

    def _before_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _execute(self, db):
        entity = self._entity
        self._before_execute(db, entity)
        # Traverse through entities that link to this one, and delete
        # or update them accordingly.
        #
        # Set of (EntityClass, oid) for entities that have already
        # been traversed.
        traversed = set()
        # Assume we've already traversed this entity.
        traversed.add((entity.__class__, entity.sys.oid))
        # Dict of {(EntityClass, oid): [field_name, ...]} for fields
        # to delete.
        to_delete = {}
        # Dict of {(EntityClass, oid): [field_name, ...]} for fields
        # to unassign.
        to_unassign = {}
        # Iterate through links and carry out appropriate actions.
        for (e_name, f_name), others in entity.sys.links().iteritems():
            EntityClass = db.extent(e_name)._EntityClass
            for other in others:
                e_o = (EntityClass, other.sys.oid)
                if e_o in traversed:
                    continue
                traversed.add(e_o)
                field = getattr(other.f, f_name)
                on_delete = field.on_delete.get(
                    entity.__class__.__name__, field.on_delete_default)
                if on_delete is CASCADE:
                    L = to_delete.setdefault(e_o, [])
                    L.append(f_name)
                elif on_delete is UNASSIGN:
                    L = to_unassign.setdefault(e_o, [])
                    L.append(f_name)
                else:
                    raise DeleteRestricted(
                        '%r cannot be deleted; it is referred to by '
                        '%r.%s' % (entity, other, f_name))
        # Unassign fields.
        for (EntityClass, oid), field_names in to_unassign.iteritems():
            other = EntityClass(oid)
            tx = other.t.update()
            for field_name in field_names:
                tx.f[field_name].readonly = False
                setattr(tx, field_name, UNASSIGNED)
            db.execute(tx)
        # Delete entities.
        for (EntityClass, oid), field_names in to_delete.iteritems():
            other = EntityClass(oid)
            # Must update fields to UNASSIGNED first to prevent
            # DeleteRestrict from being raised by the database itself.
            tx = other.t.update()
            for field_name in field_names:
                tx.f[field_name].readonly = False
                setattr(tx, field_name, UNASSIGNED)
            db.execute(tx, strict=False)
            tx = other.t.delete()
            db.execute(tx, strict=False)
        # Attempt to delete the entity itself.
        extent_name = self._extent_name
        oid = entity._oid
        self._old_rev = db._entity_rev(extent_name, oid)
        self._old_fields = db._entity_fields(extent_name, oid)
        db._delete_entity(extent_name, oid)
        self._after_execute(db)
        return None


class Update(Transaction):
    """Update an existing entity instance."""

    _label = u'Update'

    def __init__(self, entity, **kw):
        Transaction.__init__(self)
        self._entity = entity
        self.sys._set('count', entity.sys.count)
        self.sys._set('links', entity.sys.links)
        self.sys._set('old', entity)
        self._oid = entity._oid
        fields = entity.sys.fields(include_readonly_fget=False)
        self._update(fields)
        for name, value in kw.iteritems():
            setattr(self, name, value)
        self._setup()

    def _setup(self):
        """Override this in subclasses to customize a transaction."""
        pass

    def _after_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _before_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _execute(self, db):
        self._before_execute(db, self._entity)
        extent_name = self._extent_name
        oid = self._oid
        self._old_rev = db._entity_rev(extent_name, oid)
        self._old_fields = db._entity_fields(extent_name, oid)
        fields = self._fields.value_map()
        # Strip out unwanted fields.
        fget_fields = self._fget_fields
        field_spec = self._EntityClass._field_spec
        for name in fields.keys():
            if name in fget_fields or name not in field_spec:
                del fields[name]
        db._update_entity(extent_name, oid, fields)
        entity = db._entity(extent_name, oid)
        self._after_execute(db, entity)
        return entity


# --------------------------------------------------------------------


class Inverse(Transaction):
    """An inversion of an executed transaction."""

    def __init__(self, original_tx):
        Transaction.__init__(self)
        if not original_tx._executed:
            raise TransactionNotExecuted(
                'Transaction must be executed before inverse can be '
                'determined.')
        self._original_tx = original_tx
        self._label = u'Inverse of %s' % label(original_tx)

    def _execute(self, db):
        inversions = self._original_tx._inversions
        while inversions:
            method, args, kw = inversions.pop()
            method(*args, **kw)


# --------------------------------------------------------------------


class _Populate(Transaction):
    """A transaction that populates the database with data."""

    _label = u''

    _data_attr = ''

    # Subclasses can limit the extents to populate via this list.
    _extent_names = []

    def __init__(self):
        Transaction.__init__(self)

    def _execute(self, db):
        execute = db.execute
        processing = []
        data_attr = self._data_attr
        def process_data(extent):
            """Recursively process data, parents before children."""
            if extent in processing:
                return
            processing.append(extent)
            # Get the field spec from the extent's create transaction
            # by instantiating a new create transaction.
            create = extent.t.create
            tx = create()
            field_spec = tx._field_spec.copy()
            # Remove readonly fields since we can't set them, and
            # remove hidden fields since we can't "see" them.
            for name in field_spec.iterkeys():
                delete = False
                if not hasattr(tx.f, name):
                    # The create transaction's _setup() might delete a
                    # field without deleting the field_spec entry.
                    delete = True
                else:
                    f = getattr(tx.f, name)
                if delete or f.readonly or f.hidden:
                    del field_spec[name]
            field_names = field_spec.keys()
            field_classes = field_spec.values()
            has_entity_field = False
            for FieldClass in field_classes:
                if issubclass(FieldClass, field.Entity):
                    has_entity_field = True
                    allow = FieldClass.allow
                    for extent_name in allow:
                        parent_extent = db.extent(extent_name)
                        process_data(parent_extent)
            # Get the data we need to process.
            data = []
            if hasattr(extent._EntityClass, data_attr):
                data = getattr(extent._EntityClass, data_attr)
            if callable(data):
                data = data(db)
            if not data:
                return
            for values in data:
                value_map = {}
                for field_name, value, FieldClass in zip(
                    field_names, values, field_classes
                    ):
                    if value is not DEFAULT:
                        value = resolve(value, FieldClass)
                        value_map[field_name] = value
                new = create(**value_map)
                execute(new)
        def resolve(value, FieldClass):    
            # Since a callable data might resolve entity fields
            # itself, we only do a lookup here if the value supplied
            # is not an Entity instance.
            if (issubclass(FieldClass, field.Entity)
                and not isinstance(value, base.Entity)
                and value is not UNASSIGNED):
                allow = FieldClass.allow
                if len(allow) > 1:
                    # With more than one allow we need to have been
                    # told which extent to use.
                    extent_name, value = value
                else:
                    # Only one Entity is allowed so we do not expect
                    # the extent name in the data.
                    extent_name = set(allow).pop()
                lookup_extent = db.extent(extent_name)
                default_key = lookup_extent.default_key
                if isinstance(value, dict):
                    kw = value
                elif isinstance(value, tuple):
                    kw = dict(zip(default_key, value))
                    for field_name in default_key:
                        FClass = lookup_extent.field_spec[field_name]
                        kw[field_name] = resolve(kw[field_name], FClass)
                else:
                    msg = 'value is %r, which is not supported' % (value, )
                    raise TypeError(msg)
                value = lookup_extent.findone(**kw)
            return value
        # Main processing loop.  Process extents by highest priority first.
        priority_attr = self._data_attr + '_priority'
        # Check if a subclass has limited the entities to be initialized.
        if self._extent_names:
            extents = [extent for extent in db.extents()
                       if extent.name in self._extent_names]
        else:
            extents = db.extents()
        # Apply the priority.
        extents = reversed(sorted(
            (getattr(extent._EntityClass, priority_attr, 0), extent)
            for extent in extents
            ))
        for priority, extent in extents:
            process_data(extent)
        # Call module-level handlers.
        fn = getattr(db._schema_module, 'on' + data_attr, None)
        if callable(fn):
            fn(db)


class Initialize(_Populate):
    """A transaction that populates the database with initial data."""

    _label = u'Initialize'

    _data_attr = '_initial'


class Populate(_Populate):
    """A transaction that populates the database with sample data."""

    _label = u'Populate'

    _data_attr = '_sample'

    def __init__(self, sample_name=''):
        _Populate.__init__(self)
        if sample_name:
            self._data_attr = '%s_%s' % (self._data_attr, sample_name)


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
