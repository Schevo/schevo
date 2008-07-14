"""Transaction classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo import base
from schevo.change import summarize
from schevo.constant import (CASCADE, DEFAULT, REMOVE, RESTRICT,
                             UNASSIGN, UNASSIGNED)
from schevo.error import (
    DeleteRestricted,
    KeyCollision,
    SchemaError,
    TransactionExecuteRedefinitionRestricted,
    TransactionExpired,
    TransactionFieldsNotChanged,
    TransactionNotExecuted,
    )
from schevo.field import Entity, _EntityBase, not_fget
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import NamespaceExtension
from schevo.trace import log


T_metaclass = schema_metaclass('T')
class TransactionMeta(T_metaclass):

    def __init__(cls, class_name, bases, class_dict):
        T_metaclass.__init__(cls, class_name, bases, class_dict)
        if (cls._restrict_subclasses
            and '_restrict_subclasses' not in class_dict
            ):
            # Base class is restricting its subclasses.
            if '__init__' in class_dict or '_execute' in class_dict:
                raise TransactionExecuteRedefinitionRestricted(
                    class_name, bases)
        cls._h_names = cls.get_method_names('h_')
        cls._x_names = cls.get_method_names('x_')

    def get_method_names(cls, prefix):
        """Return list of method names that start with prefix."""
        names = []
        for name in dir(cls):
            if name.startswith(prefix):
                func = getattr(cls, name)
                if func.im_self is None:
                    names.append(name)
        return names


class Transaction(base.Transaction):

    __metaclass__ = TransactionMeta

    _db = None

    _field_spec = FieldSpecMap()

    # If True, set all fields to their default value upon
    # initialization. All standard transaction subclasses set this to
    # False, but custom subclasses of Transaction benefit from the
    # default being True.
    _populate_default_values = True

    # If True, do not allow subclasses to change the behavior of
    # `__init__` or `_execute`.
    _restrict_subclasses = False

    def __init__(self):
        self._changes_requiring_notification = []
        self._changes_requiring_validation = []
        self._deletes = set()
        self._executed = False
        self._field_map = self._field_spec.field_map(instance=self)
        self._inversions = []
        self._known_deletes = []
        self._relaxed = set()
        self.f = schevo.namespace.Fields(self)
        self.sys = TransactionSys(self)
        if self._populate_default_values:
            for field in self._field_map.itervalues():
                field.set(field.default[0], check_readonly=False)

    def __getattr__(self, name):
        if name == 'x':
            self.x = attr = TransactionExtenders(self)
        elif name == 'h':
            self.h = attr = TransactionChangeHandlers(self)
        else:
            try:
                field = self._field_map[name]
            except KeyError, e:
                raise AttributeError(*e.args)
            attr = field.get()
        return attr

    def __setattr__(self, name, value):
        if name == 'sys' or name.startswith('_') or len(name) == 1:
            return base.Transaction.__setattr__(self, name, value)
        else:
            self._field_map[name].set(value, check_readonly=True)

    def __str__(self):
        text = label(self)
        extent_name = self.sys.extent_name
        if extent_name is not None:
            text += ' :: %s' % extent_name
        return text

    @property
    def _changes(self):
        if not self._executed:
            raise TransactionNotExecuted(self)
        return self._changes_requiring_notification

    def _execute(self, db):
        """Override this in subclasses to provide actual transaction
        execution."""
        raise NotImplementedError

    @property
    def _field_was_changed(self):
        """Return True if at least one field was changed."""
        field_map = self._field_map
        for field in field_map.itervalues():
            if field.was_changed():
                return True
        return False

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(self._field_map.keys())

    def _initialize(self, field_map):
        """Initialize field values."""
        tx_field_map = self._field_map
        for name, field in field_map.iteritems():
            if name in tx_field_map:
                tx_field_map[name]._initialize(field._value)

    def _undo(self):
        """Return a transaction that can undo this one."""
        if not self._executed:
            raise TransactionNotExecuted(self)
        # The default implementation is to return the inverse of this
        # transaction.
        return Inverse(self)

    def _update_all_fields(self, name, value):
        """Update the attribute `name` to `value` on all fields."""
        for field in self._field_map.values():
            setattr(field, name, value)


class TransactionExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, tx):
        NamespaceExtension.__init__(self)
        d = self._d
        for x_name in tx._x_names:
            func = getattr(tx, x_name)
            name = x_name[2:]
            d[name] = func


class TransactionChangeHandlers(NamespaceExtension):
    """A namespace of field change handlers."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False

    def __init__(self, tx):
        NamespaceExtension.__init__(self)
        d = self._d
        for h_name in tx._h_names:
            func = getattr(tx, h_name)
            name = h_name[2:]
            d[name] = func


class TransactionSys(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__ + ['_transaction']

    def __init__(self, transaction):
        NamespaceExtension.__init__(self)
        self._transaction = transaction

    @property
    def changes(self):
        return self._transaction._changes

    @property
    def current_field_map(self):
        return self._transaction._field_map

    @property
    def executed(self):
        return self._transaction._executed

    @property
    def extent_name(self):
        if hasattr(self._transaction, '_extent_name'):
            return self._transaction._extent_name

    def field_map(self, *filters):
        # Remove fields that should not be included.
        new_fields = self._transaction._field_map.itervalues()
        for filt in filters:
            new_fields = [field for field in new_fields if filt(field)]
        return FieldMap((field.name, field) for field in new_fields)

    @property
    def field_was_changed(self):
        """True if at least one field was changed."""
        return self._transaction._field_was_changed

    @property
    def requires_changes(self):
        return getattr(self._transaction, '_requires_changes', False)

    def summarize(self):
        return summarize(self._transaction)


# --------------------------------------------------------------------


class Combination(Transaction):
    """A transaction that consists of several sub-transactions."""

    _label = u'Combination'

    _populate_default_values = False
    _restrict_subclasses = True

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

class Create(Transaction):
    """Create a new entity instance."""

    _label = u'Create'

    _style = _Create_Standard

    _populate_default_values = False
    _restrict_subclasses = True

    def __init__(self, *args, **kw):
        Transaction.__init__(self)
        field_map = self._field_map
        # Call setup, which may remove fields from this transaction.
        self._setup()
        # Assign values supplied by kw.
        for name, value in kw.iteritems():
            setattr(self, name, value)
        # Look for matching field values in objects passed as args.
        for field_name, f in field_map.iteritems():
            if not f.assigned and not f.readonly:
                for arg in args:
                    if hasattr(arg, field_name):
                        value = getattr(arg, field_name)
                        setattr(self, field_name, value)
        # Assign default values for fields that haven't yet been
        # assigned a value.
        field_spec = self._field_spec
        for f in field_map.itervalues():
            if not f.assigned:
                default = f.default[0]
                if f.may_store_entities and not callable(default):
                    field_name = f._name
                    default = resolve(f._instance._db, field_name, default,
                                      field_spec[field_name])
                while callable(default) and default is not UNASSIGNED:
                    default = default()
                f.set(default, check_readonly=False)
        # Reset metadata_changed on all fields.
        for f in self._field_map.itervalues():
            f.reset_metadata_changed()

    def _setup(self):
        """Override this in subclasses to customize a transaction."""
        pass

    def _after_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _before_execute(self, db):
        """Override this in subclasses to customize a transaction."""
        pass

    def _during_execute(self, db):
        """Override this in subclasses to customize a transaction."""
        pass

    def _execute(self, db):
        field_map = self._field_map
        # Before execute callback.
        self._before_execute(db)
        # Validate individual fields.
        for field in field_map.itervalues():
            if field.fget is None:
                field.validate(field._value)
        # Strip out unwanted fields.
        field_dump_map = field_map.dump_map()
        field_related_entity_map = field_map.related_entity_map()
        fget_fields = self._fget_fields
        field_spec = self._EntityClass._field_spec
        for name in field_dump_map.keys():
            if name in fget_fields or name not in field_spec:
                del field_dump_map[name]
                if name in field_related_entity_map:
                    del field_related_entity_map[name]
        # During execute callback.
        self._during_execute(db)
        # Proceed with execution based on the create style requested.
        extent_name = self._extent_name
        style = self._style
        if style == _Create_Standard:
            oid = db._create_entity(
                extent_name, field_dump_map, field_related_entity_map)
        else:
            oid = None
            extent = db.extent(extent_name)
            default_key = extent.default_key
            if default_key is None:
                msg = '%s does not have a default key.' % (extent_name,)
                raise RuntimeError(msg)
            criteria = {}
            field_value_map = field_map.value_map()
            for name in default_key:
                criteria[name] = field_value_map[name]
            entity = extent.findone(**criteria)
            if entity is not None:
                # Entity already exists.
                self._oid = entity._oid
                if style == _Create_If_Necessary:
                    return entity
                else:
                    raise RuntimeError('_style is not set correctly.')
            else:
                oid = db._create_entity(
                    extent_name, field_dump_map, field_related_entity_map)
        self._oid = oid
        entity = db._entity(extent_name, oid)
        # After execute callback.
        self._after_execute(db, entity)
        return entity


def find_references(db, entity, traversed,
                    restricters, cascaders, unassigners, removers):
    """Support function for Delete transactions.  Acts recursively to
    get a list of all entities directly or indirectly related to
    `entity`.

    NOTE: This function returns nothing.  Instead, the `references`
    and `traversed` arguments are mutated.

    - `db`: The database the Delete is occuring in.

    - `entity`: The entity to inspect when adding to the references
      list.

    The following arguments are directly mutated during execution:

    - `traversed`: The set of already-traversed entities.

    - `restricters`: Dictionary of ``referrer: set([(f_name,
      referred), ...])`` pairs storing information about references
      that RESTRICT deletion.

    - `cascaders`: Dictionary of ``referrer: set([f_name, ...])``
      pairs storing information about references that allow CASCADE
      deletion.

    - `unassigners`: Dictionary of ``referrer: set([(f_name,
      referred), ...])`` pairs storing information about references
      that desire to UNASSIGN values on deletion.

    - `removers`: Dictionary of ``referrer: set([(f_name, referred),
      ...])`` pairs storing information about references that desire
      to REMOVE values on deletion.
    """
    if entity in traversed:
        return
    traversed.add(entity)
    entity_extent_name = entity._extent.name
    for (e_name, f_name), others in entity.sys.links().iteritems():
        extent = db.extent(e_name)
        field_class = extent.field_spec[f_name]
        on_delete_get = field_class.on_delete.get
        on_delete_default = field_class.on_delete_default
        for referrer in others:
            on_delete = on_delete_get(entity_extent_name, on_delete_default)
            if on_delete is RESTRICT:
                if referrer == entity:
                    # Don't restrict when an entity refers to
                    # itself. Instead, treat it as a CASCADE delete.
                    field_names = cascaders.setdefault(referrer, set())
                    field_names.add(f_name)
                else:
                    field_referred_set = restricters.setdefault(
                        referrer, set())
                    field_referred_set.add((f_name, entity))
            elif on_delete is CASCADE:
                field_names = cascaders.setdefault(referrer, set())
                field_names.add(f_name)
            elif on_delete is UNASSIGN:
                field_referred_set = unassigners.setdefault(referrer, set())
                field_referred_set.add((f_name, entity))
            elif on_delete is REMOVE:
                field_referred_set = removers.setdefault(referrer, set())
                field_referred_set.add((f_name, entity))
            else:
                raise ValueError(
                    'Unrecognized on_delete value %r' % on_delete)
            find_references(db, referrer, traversed,
                            restricters, cascaders, unassigners, removers)


class Delete(Transaction):
    """Delete an existing entity instance."""

    _label = u'Delete'

    _populate_default_values = False
    _restrict_subclasses = True

    def __init__(self, entity):
        Transaction.__init__(self)
        self._entity = entity
        self._rev = entity._rev
        self.sys._set('count', entity.sys.count)
        self.sys._set('links', entity.sys.links)
        self.sys._set('old', entity)
        field_map = entity.sys.field_map(not_fget)
        self._initialize(field_map)
        self._update_all_fields('readonly', True)
        self._update_all_fields('required', False)
        self._setup()
        # Reset metadata_changed on all fields.
        for f in self._field_map.itervalues():
            f.reset_metadata_changed()

    def __getattr__(self, name):
        if name == 'm':
            self.m = attr = self._entity.m
        else:
            return Transaction.__getattr__(self, name)
        return attr

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
        if entity._rev != self._rev:
            raise TransactionExpired(self, self._rev, entity._rev)
        deletes = self._deletes
        # Before execute callback.
        self._before_execute(db, entity)
        # Build list of direct and indirect references.
        traversed = set()
        restricters = dict()
        cascaders = dict()
        unassigners = dict()
        removers = dict()
        find_references(db, entity, traversed,
                        restricters, cascaders, unassigners, removers)
        # Referrers should be removed from restricters if they are
        # also requesting cascade deletion.
        restricter_keys = set(restricters) - set(cascaders)
        # The entity whose deletion was requested should never be
        # considered a restricter.
        restricter_keys.discard(entity)
        if len(restricter_keys) != 0:
            # Raise DeleteRestricted if there are any restricters left
            # over.
            error = DeleteRestricted()
            for referrer in restricter_keys:
                restricter_set = restricters[referrer]
                for f_name, referred in restricter_set:
                    error.add(referred, referrer, f_name)
            if error.restrictions:
                raise error
        else:
            # Convert all restricters to cascaders so that fields are
            # unassigned properly before deletion.
            for referrer, field_referred_set in restricters.iteritems():
                field_names = cascaders.setdefault(referrer, set())
                for field_name, referred in field_referred_set:
                    field_names.add(field_name)
        # Unassign fields requested by unassigners.
        for referrer, field_referred_set in unassigners.iteritems():
            tx = referrer.t.update()
            for f_name, referred in field_referred_set:
                tx.f[f_name]._unassign(referred)
            db.execute(tx)
        # Remove values from fields marked as removers.
        for referrer, field_referred_set in removers.iteritems():
            tx = referrer.t.update()
            for f_name, referred in field_referred_set:
                tx.f[f_name]._remove(referred)
            db.execute(tx)
        # Forceably update fields to UNASSIGNED first to prevent
        # DeleteRestrict from being raised by the database itself.
        referrers = set()
        for referrer, field_names in cascaders.iteritems():
            field_map = referrer.sys.field_map(not_fget)
            field_dump_map = dict(field_map.dump_map())
            field_related_entity_map = dict(field_map.related_entity_map())
            new_dump_map = dict((name, UNASSIGNED) for name in field_names)
            new_related_entity_map = dict(
                (name, frozenset()) for name in field_names)
            field_dump_map.update(new_dump_map)
            field_related_entity_map.update(new_related_entity_map)
            extent = referrer._extent
            extent_name = extent.name
            oid = referrer._oid
            try:
                db._update_entity(
                    extent_name, oid, field_dump_map, field_related_entity_map)
            except KeyCollision:
                # Since it takes more time to relax an index, only do
                # it when we find a key collision.
                extent.relax_all_indices()
                # Try the update again.
                db._update_entity(
                    extent_name, oid, field_dump_map, field_related_entity_map)
            referrers.add((extent_name, oid, referrer))
        # Everything checks out okay for this entity, so add it to the
        # set of deleted entities.
        deletes.add((entity.__class__, entity._oid))
        # Delete entities in a deterministic (sorted) fashion.
        for extent_name, oid, referrer in sorted(referrers):
            referrer_e_o = referrer.__class__, referrer._oid
            if referrer_e_o in deletes:
                # Skip the original entity whose deletion was
                # requested, since we must delete it using a call to
                # the database's `_delete_entity` method.  Also skip
                # any entity that has already been deleted.
                continue
            if not db._extent_contains_oid(extent_name, oid):
                # A nested transaction or cascade deleted this entity
                # before we could.
                continue
            tx = referrer.t.delete()
            tx._deletes.update(deletes)
            db.execute(tx, strict=False)
        # Attempt to delete the entity itself.
        extent_name = self._extent_name
        oid = entity._oid
        db._delete_entity(extent_name, oid)
        self._after_execute(db)
        return None


class Update(Transaction):
    """Update an existing entity instance."""

    _label = u'Update'

    _call_change_handlers_on_init = True

    _requires_changes = True

    _populate_default_values = False
    _restrict_subclasses = True

    def __init__(self, _entity, **kw):
        Transaction.__init__(self)
        self._entity = _entity
        self.sys._set('count', _entity.sys.count)
        self.sys._set('links', _entity.sys.links)
        self.sys._set('old', _entity)
        self._oid = _entity._oid
        self._rev = _entity._rev
        field_map = _entity.sys.field_map(not_fget)
        self._initialize(field_map)
        # Call change handlers to prepare fields based on stored
        # values.  Call them in order of field definition, so
        # side-effects are deterministic.
        if self._call_change_handlers_on_init:
            for name in self.f:
                handler_name = 'h_%s' % name
                handler = getattr(self, handler_name, None)
                if handler is not None:
                    handler()
        # Apply values from keyword arguments.
        for name, value in kw.iteritems():
            setattr(self, name, value)
        self._setup()
        # Reset metadata_changed on all fields.
        for f in self._field_map.itervalues():
            f.reset_metadata_changed()

    def __getattr__(self, name):
        if name == 'm':
            self.m = attr = self._entity.m
        else:
            return Transaction.__getattr__(self, name)
        return attr

    def _setup(self):
        """Override this in subclasses to customize a transaction."""
        pass

    def _after_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _before_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _during_execute(self, db, entity):
        """Override this in subclasses to customize a transaction."""
        pass

    def _execute(self, db):
        entity = self._entity
        field_map = self._field_map
        if entity._rev != self._rev:
            raise TransactionExpired(self, self._rev, entity._rev)
        self._before_execute(db, entity)
        if self._requires_changes:
            if not self._field_was_changed:
                raise TransactionFieldsNotChanged(self)
        # Validate individual fields.
        for field in field_map.itervalues():
            if field.fget is None:
                field.validate(field._value)
        extent_name = self._extent_name
        oid = self._oid
        # Strip out unwanted fields.
        field_dump_map = field_map.dump_map()
        field_related_entity_map = field_map.related_entity_map()
        fget_fields = self._fget_fields
        field_spec = self._EntityClass._field_spec
        for name in field_dump_map.keys():
            if name in fget_fields or name not in field_spec:
                del field_dump_map[name]
                if name in field_related_entity_map:
                    del field_related_entity_map[name]
        self._during_execute(db, entity)
        db._update_entity(
            extent_name, oid, field_dump_map, field_related_entity_map)
        entity = db._entity(extent_name, oid)
        self._after_execute(db, entity)
        return entity


# --------------------------------------------------------------------


class Inverse(Transaction):
    """An inversion of an executed transaction."""

    _populate_default_values = False
    _restrict_subclasses = True

    def __init__(self, original_tx):
        Transaction.__init__(self)
        if not original_tx._executed:
            raise TransactionNotExecuted(self)
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

    _populate_default_values = False

    def __init__(self):
        Transaction.__init__(self)

    def _execute(self, db):
        data_attr = self._data_attr
        # Main processing loop.  Process extents by highest priority first.
        priority_attr = self._data_attr + '_priority'
        # Check if a subclass has limited the entities to be initialized.
        if self._extent_names:
            extents = [extent for extent in db.extents()
                       if extent.name in self._extent_names]
        else:
            extents = db.extents()
        # Keep track of extents we will populate.
        self._extents = extents
        # Apply the priority.
        priority_extents = reversed(sorted(
            (getattr(extent._EntityClass, priority_attr, 0), extent)
            for extent in extents
            ))
        # Process data in order of priority.
        processing = []
        for priority, extent in priority_extents:
            self._process_data(db, extent, processing)
        # Call module-level handlers.
        fn = getattr(db._schema_module, 'on' + data_attr, None)
        if callable(fn):
            fn(db)

    def _process_data(self, db, extent, processing):
        """Recursively process initial/sample data, parents before children.

        - `db`: Database to work within.
        - `extent`: Extent to process.
        - `processing`: List of extents that are being processed higher up
          in the call stack.
        """
        if extent in processing:
            return
        processing.append(extent)
        # Get the data we need to process, and short-circuit if no
        # data is specified.
        data = []
        data_attr = self._data_attr
        if hasattr(extent._EntityClass, data_attr):
            data = getattr(extent._EntityClass, data_attr)
        if callable(data):
            data = data(db)
        if not data:
            return
        # Get the field spec from the extent's create transaction
        # by instantiating a new create transaction.
        create = extent.t.create
        tx = create()
        dict_field_spec = tx._field_spec.copy()
        tuple_field_spec = tx._field_spec.copy()
        # For tuples and dicts, remove fields that don't even exist in
        # the create transaction.
        # For tuples, remove readonly fields since we can't set them,
        # and remove hidden fields since we can't "see" them.
        for name in dict_field_spec.keys():
            delete = False
            if not hasattr(tx.f, name):
                # The create transaction's _setup() might delete a
                # field without deleting the field_spec entry.
                delete = True
            else:
                field = getattr(tx.f, name)
            if delete:
                del dict_field_spec[name]
            if delete or field.readonly or field.hidden:
                del tuple_field_spec[name]
        for FieldClass in dict_field_spec.itervalues():
            if issubclass(FieldClass, Entity):
                allow = FieldClass.allow
                for extent_name in allow:
                    parent_extent = db.extent(extent_name)
                    self._process_data(db, parent_extent, processing)
        # Process the data.
        execute = db.execute
        dict_field_names = dict_field_spec.keys()
        for values in data:
            # Convert values to dict if it's a tuple.
            if isinstance(values, tuple):
                new_values = {}
                for field_name, value in zip(tuple_field_spec.iterkeys(),
                                             values):
                    new_values[field_name] = value
                values = new_values
            # Resolve the dict's values if needed.
            value_map = {}
            for field_name, FieldClass in dict_field_spec.iteritems():
                value = values.get(field_name, DEFAULT)
                if value is not DEFAULT:
                    try:
                        value = resolve(db, field_name, value, FieldClass,
                                        dict_field_names)
                    except:
                        print '-' * 40
                        print '  extent:', extent
                        print '  data:', data
                        print '  values:', values
                        print '  while resolving:', value
                        raise
                    value_map[field_name] = value
            # Assign values in field definition order, so that
            # interactions with field value-changed handlers is
            # deterministic.
            new = create()
            for field_name in dict_field_names:
                if field_name in value_map:
                    value = value_map[field_name]
                    field = new.f[field_name]
                    if (field.readonly
                        or getattr(new, field_name) == value
                        ):
                        # Skip readonly and unchanged fields.
                        continue
                    setattr(new, field_name, value)
            try:
                execute(new)
            except:
                print '-' * 40
                print '  extent:', extent
                print '  data:', data
                print '  values:', values
                print '  dict_field_spec:', dict_field_spec
                print '  tuple_field_spec:', tuple_field_spec
                print '  value_map:', value_map
                raise


class Initialize(_Populate):
    """A transaction that populates the database with initial data."""

    _label = u'Initialize'

    _data_attr = '_initial'

    _restrict_subclasses = True


class Populate(_Populate):
    """A transaction that populates the database with sample data."""

    _label = u'Populate'

    _data_attr = '_sample'

    _restrict_subclasses = True

    def __init__(self, sample_name=''):
        _Populate.__init__(self)
        if sample_name:
            self._data_attr = '%s_%s' % (self._data_attr, sample_name)


# ---------------------------------------------------------------------


class CallableWrapper(Transaction):
    """A transaction that, upon execution, calls a callable object
    with the open database."""

    _populate_default_values = False
    _restrict_subclasses = True

    def __init__(self, fn):
        assert callable(fn)
        Transaction.__init__(self)
        self._fn = fn

    def _execute(self, db):
        return self._fn(db)


# ---------------------------------------------------------------------


def resolve(db, field_name, value, FieldClass, field_names=None):
    """Resolve the entity reference(s) in `value` and return the
    actual entity references.

    - `db`: Database to search within.
    - `field_name`: Field name for the field whose value we are
      resolving.
    - `value`: Value to resolve.
    - `FieldClass`: Class of the field whose value we are
      resolving.
    - `field_names`: (optional) Full list of field names for each data
      population record, if resolving within initial or sample data.
      Used to make error messages more useful.
    """
    # Since a callable data might resolve entity fields
    # itself, we only do a lookup here if the value supplied
    # is not an Entity instance.
    if (issubclass(FieldClass, _EntityBase)
        and not isinstance(value, base.Entity)
        and value is not UNASSIGNED
        ):
        if isinstance(value, list):
            value = [
                resolve(db, field_name, v, FieldClass, field_names)
                for v in value
                ]
        elif isinstance(value, set):
            value = set([
                resolve(db, field_name, v, FieldClass, field_names)
                for v in value
                ])
        else:
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
                newvalue = []
                for key_field_name in default_key:
                    if key_field_name not in value:
                        raise ValueError('key field %r is required in %r'
                                         % (key_field_name, value))
                    newvalue.append(value[key_field_name])
                value = tuple(newvalue)
            if isinstance(value, tuple):
                if len(default_key) != len(value):
                    msg = 'mismatch between default key %r and value %r'
                    raise ValueError, msg % (default_key, value)
                kw = dict(zip(default_key, value))
                for key_field_name in default_key:
                    FClass = lookup_extent.field_spec[key_field_name]
                    v = resolve(db, key_field_name, kw[key_field_name],
                                FClass, default_key)
                    kw[key_field_name] = v
            else:
                msg = 'value %r is not valid for field %r in %r' % (
                    value, field_name, field_names)
                raise TypeError(msg)
            value = lookup_extent.findone(**kw)
            if value is None:
                raise ValueError('no entity %s found in %s' %
                                 (kw, lookup_extent))
    return value


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
