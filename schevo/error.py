"""Schevo-specific exceptions.

For copyright, license, and warranty, see bottom of file.
"""


# ======================================================================
# Runtime errors


class Restricted(RuntimeError):
    """The attempted operation was restricted."""


class DatabaseAlreadyExists(RuntimeError):
    """The database already exists."""

    def __init__(self, filename):
        message = 'Schevo database already in file %r.' % filename
        super(DatabaseAlreadyExists, self).__init__(message)
        self.filename = filename


class DatabaseDoesNotExist(RuntimeError):
    """The database does not exist."""

    def __init__(self, filename):
        message = 'Schevo database not found in file %r.' % filename
        super(DatabaseDoesNotExist, self).__init__(message)
        self.filename = filename


class DatabaseExecutingTransaction(RuntimeError):
    """The operation cannot be completed while the database is
    executing a transaction."""


class DatabaseFormatMismatch(RuntimeError):
    """The internal structure of the database is not in the correct
    format."""

    def __init__(self, current_format, required_format):
        message = (
            'Source database must be in format %i; currently in format %i.'
            % (required_format, current_format)
            )
        super(DatabaseFormatMismatch, self).__init__(message)
        self.current_format = current_format
        self.required_format = required_format


class DatabaseMismatch(RuntimeError):
    """A value from one database was used incorrectly in another."""

    def __init__(self, field_name, field_value):
        message = (
            '%r field of %r cannot be resolved to the current database.'
            % (field_name, field_value)
            )
        super(DatabaseMismatch, self).__init__(message)
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
        super(DatabaseVersionMismatch, self).__init__(message)
        self.current_version = current_version
        self.expected_version = expected_version
        self.requested_version = requested_version


class DeleteRestricted(Restricted):
    """Delete attempted on an instance with foreign references."""

    def __init__(self, entity=None, referring_entity=None,
                 referring_field_name=None):
        message = 'Cannot delete; referenced by one or more other entities.'
        super(DeleteRestricted, self).__init__(message)
        self.restrictions = []
        if (entity is not None
            and referring_entity is not None
            and referring_field_name is not None
            ):
            self.append(entity, referring_entity, referring_field_name)

    def append(self, entity, referring_entity, referring_field_name):
        self.restrictions.append((
            entity,
            referring_entity,
            referring_field_name,
            ))


class ExtentExists(KeyError):
    """An extent already exists."""

    def __init__(self, extent_name):
        message = 'Extent %r already exists.' % extent_name
        super(ExtentExists, self).__init__(message)
        self.extent_name = extent_name


class ExtentDoesNotExist(KeyError):
    """An extent does not exist."""

    def __init__(self, extent_name):
        message = 'Extent %r does not exist.' % extent_name
        super(ExtentDoesNotExist, self).__init__(message)
        self.extent_name = extent_name


class EntityExists(KeyError):
    """An entity already exists."""

    def __init__(self, extent_name, oid):
        message = (
            'Entity OID %i already exists in extent %r.'
            % (oid, extent_name)
            )
        super(EntityExists, self).__init__(message)
        self.extent_name = extent_name
        self.oid = oid


class EntityDoesNotExist(KeyError):
    """An entity does not exist."""


class FieldDoesNotExist(KeyError):
    """A field does not exist."""


class FindoneFoundMoreThanOne(Exception):
    """Findone found more than one match."""


class IndexDoesNotExist(Exception):
    """An index does not exist."""


class KeyCollision(KeyError):
    """An entity with the given keys already exists."""


class SchemaFileIOError(IOError):
    """The schema file could not be read."""


class TransactionAlreadyExecuted(RuntimeError):
    """A transaction was already executed and cannot be re-executed."""


class TransactionExpired(RuntimeError):
    """Something changed in the database that caused this transaction to
    expire."""


class TransactionFieldsNotChanged(RuntimeError):
    """No transaction field values were changed."""


class TransactionNotExecuted(RuntimeError):
    """A transaction was not yet executed."""


class TransactionRuleViolation(RuntimeError):
    """A transaction rule was violated."""


# ======================================================================
# Schema errors


class SchemaError(SyntaxError):
    """An error was found in the schema."""


class AmbiguousFieldDefinition(SchemaError):
    """A field defition's attributes were ambiguous."""


class KeyIndexOverlap(SchemaError):
    """Key specs and index specs must not overlap."""


class TransactionExecuteRedefinitionRestricted(SchemaError):
    """Overriding `__init__` or `_execute` is not allowed in this class."""


class UnsupportedFieldType(SchemaError):
    """The field type is not supported by the database engine in use."""


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
