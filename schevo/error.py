"""Schevo-specific exceptions."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.


# ======================================================================
# Runtime errors


class Restricted(RuntimeError):
    """The attempted operation was restricted."""


class BackendConflictError(RuntimeError):
    """Transaction could not be executed; too many backend conflict errors."""


class DatabaseAlreadyExists(RuntimeError):
    """The database already exists."""

    def __init__(self, url):
        message = 'Schevo database already at %r.' % url
        RuntimeError.__init__(self, message)
        self.url = url


class DatabaseDoesNotExist(RuntimeError):
    """The database does not exist."""

    def __init__(self, url):
        message = 'Schevo database not found at %r.' % url
        RuntimeError.__init__(self, message)
        self.url = url


class DatabaseExecutingTransaction(RuntimeError):
    """The operation cannot be completed while the database is
    executing a transaction."""


class DatabaseFileLocked(RuntimeError):
    """The database file is in use by another process."""

    def __init__(self):
        message = 'The database file is being used by another process.'
        RuntimeError.__init__(self, message)


class DatabaseFormatMismatch(RuntimeError):
    """The internal structure of the database is not in the correct
    format."""

    def __init__(self, current_format, required_format):
        message = (
            'Source database must be in format %i; currently in format %i.'
            % (required_format, current_format)
            )
        RuntimeError.__init__(self, message)
        self.current_format = current_format
        self.required_format = required_format


class DatabaseMismatch(RuntimeError):
    """A value from one database was used incorrectly in another."""

    def __init__(self, field_name, field_value):
        message = (
            '%r field of %r cannot be resolved to the current database.'
            % (field_name, field_value)
            )
        RuntimeError.__init__(self, message)
        self.field_name = field_name
        self.field_value = field_value


class DatabaseVersionMismatch(RuntimeError):
    """The schema version being evolved to is not the version
    subsequent to the current database schema."""

    def __init__(self, current_version, expected_version, requested_version):
        message = (
            'Current version is %i; expected: %i; requested: %i.'
            % (current_version, expected_version, requested_version)
            )
        RuntimeError.__init__(self, message)
        self.current_version = current_version
        self.expected_version = expected_version
        self.requested_version = requested_version


class DeleteRestricted(Restricted):
    """Delete attempted on an instance with foreign references."""

    def __init__(self, entity=None, referring_entity=None,
                 referring_field_name=None):
        message = 'Cannot delete; referenced by one or more other entities.'
        Restricted.__init__(self, message)
        self.restrictions = set()
        if (entity is not None
            and referring_entity is not None
            and referring_field_name is not None
            ):
            self.add(entity, referring_entity, referring_field_name)

    def add(self, entity, referring_entity, referring_field_name):
        self.restrictions.add((
            entity,
            referring_entity,
            referring_field_name,
            ))


class ExtentExists(KeyError):
    """An extent already exists."""

    def __init__(self, extent_name):
        message = 'Extent %r already exists.' % extent_name
        KeyError.__init__(self, message)
        self.extent_name = extent_name


class ExtentDoesNotExist(KeyError):
    """An extent does not exist."""

    def __init__(self, extent_name):
        message = 'Extent %r does not exist.' % extent_name
        KeyError.__init__(self, message)
        self.extent_name = extent_name


class EntityExists(KeyError):
    """An entity already exists."""

    def __init__(self, extent_name, oid):
        message = (
            'Entity OID %i already exists in extent %r.'
            % (oid, extent_name)
            )
        KeyError.__init__(self, message)
        self.extent_name = extent_name
        self.oid = oid


class EntityDoesNotExist(KeyError):
    """An entity does not exist."""

    def __init__(self, extent_name, field_name=None, oid=None):
        if field_name is not None:
            message = (
                'Entity referenced in field %r does not exist in extent %r.'
                % (field_name, extent_name)
                )
        elif oid is not None:
            message = (
                'OID %i does not exist in extent %r.'
                % (oid, extent_name)
                )
        KeyError.__init__(self, message)
        self.extent_name = extent_name
        self.field_name = field_name
        self.oid = oid


class FieldDoesNotExist(KeyError):
    """A field does not exist."""

    def __init__(self, object_or_name, field_name, new_field_name=None):
        message = (
            'Field %r does not exist in %r'
            % (field_name, object_or_name)
            )
        if new_field_name is not None:
            message += (
                ' while attempting to rename field to %r'
                % new_field_name
                )
        message += '.'
        KeyError.__init__(self, message)
        self.object_or_name = object_or_name
        self.field_name = field_name
        self.new_field_name = new_field_name


class FieldReadonly(AttributeError):
    """Cannot set values of readonly fields."""

    def __init__(self, message, field, instance):
        AttributeError.__init__(self, message)
        self.field = field
        self.instance = instance


class FieldRequired(AttributeError):
    """Must set values of required fields."""

    def __init__(self, message, field, instance):
        AttributeError.__init__(self, message)
        self.field = field
        self.instance = instance


class FindoneFoundMoreThanOne(Exception):
    """Findone found more than one match."""

    def __init__(self, extent_name, criteria):
        message = (
            'Found more than one match in extent %r for criteria %r.'
            % (extent_name, criteria)
            )
        Exception.__init__(self, message)
        self.extent_name = extent_name
        self.criteria = criteria[:]


class IndexDoesNotExist(Exception):
    """An index does not exist."""

    def __init__(self, extent_name, index_spec):
        message = (
            'Index %r not found in extent %r.'
            % (index_spec, extent_name)
            )
        Exception.__init__(self, message)
        self.extent_name = extent_name
        self.index_spec = index_spec


class KeyCollision(KeyError):
    """An entity with the given keys already exists."""

    def __init__(self, extent_name, key_spec, field_values):
        message = (
            'Duplicate values %r for key %r in extent %r.'
            % (field_values, key_spec, extent_name)
            )
        KeyError.__init__(self, message)
        self.extent_name = extent_name
        self.key_spec = key_spec
        self.field_values = field_values


class SchemaFileIOError(IOError):
    """The schema file could not be read."""


class TransactionAlreadyExecuted(RuntimeError):
    """A transaction was already executed and cannot be re-executed."""

    def __init__(self, transaction):
        message = 'Transaction %r already executed.' % transaction
        RuntimeError.__init__(self, message)
        self.transaction = transaction


class TransactionExpired(RuntimeError):
    """Something changed in the database that caused this transaction to
    expire."""

    def __init__(self, transaction, original_rev, current_rev):
        message = (
            'Transaction %r expired; original entity revision was %i, now %i.'
            % (transaction, original_rev, current_rev)
            )
        RuntimeError.__init__(self, message)
        self.transaction = transaction
        self.original_rev = original_rev
        self.current_rev = current_rev


class TransactionFieldsNotChanged(RuntimeError):
    """No transaction field values were changed."""

    def __init__(self, transaction):
        message = (
            'Transaction %r requires at least one field changed.'
            % transaction
            )
        RuntimeError.__init__(self, message)
        self.transaction = transaction


class TransactionNotExecuted(RuntimeError):
    """A transaction was not yet executed."""

    def __init__(self, transaction):
        message = (
            'Transaction %r must be executed to get its changes '
            'or undo transaction.'
            % transaction
            )
        RuntimeError.__init__(self, message)
        self.transaction = transaction


class TransactionRuleViolation(RuntimeError):
    """A transaction rule was violated."""

    def __init__(self, message, **kwargs):
        RuntimeError.__init__(self, message)
        self.__dict__.update(kwargs)


# ======================================================================
# Schema errors


class SchemaError(SyntaxError):
    """An error was found in the schema."""


class AmbiguousFieldDefinition(SchemaError):
    """A field defition's attributes were ambiguous."""

    def __init__(self, reason):
        message = 'Ambiguous field definition: %r' % reason
        SchemaError.__init__(self, message)
        self.reason = reason
##     def __init__(self, reason, class_name, field_name):
##         message = (
##             'Ambiguous field definition for %r in class %r: %r'
##             % (field_name, class_name, reason)
##             )
##         SchemaError.__init__(self, message)
##         self.reason = reason
##         self.class_name = class_name
##         self.field_name = field_name


class KeyIndexOverlap(SchemaError):
    """Key specs and index specs must not overlap."""

    def __init__(self, class_name, overlapping_specs):
        message = (
            'Cannot use same spec for both key and index in entity class %r.'
            % class_name
            )
        SchemaError.__init__(self, message)
        self.class_name = class_name
        self.overlapping_specs = overlapping_specs


class TransactionExecuteRedefinitionRestricted(SchemaError):
    """Overriding `__init__` or `_execute` is not allowed in this class."""

    def __init__(self, class_name, base_classes):
        message = (
            'Transaction subclass %r, with bases %r, '
            'tried to override __init__ or _execute, '
            'but that is not allowed with those bases.'
            % (class_name, base_classes)
            )
        SchemaError.__init__(self, message)
        self.class_name = class_name
        self.base_classes = base_classes


class UnsupportedFieldType(SchemaError):
    """The field type is not supported by the database engine in use."""

    def __init__(self, reason):
        message = 'Unsupported field type: %s' % reason
        SchemaError.__init__(self, message)
        self.reason = reason
