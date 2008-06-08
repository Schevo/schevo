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


class DatabaseMismatch(RuntimeError):
    """A value from one database was used incorrectly in another."""


class DatabaseVersionMismatch(RuntimeError):
    """The schema version being evolved to is not the version
    subsequent to the current database schema."""


class DeleteRestricted(Restricted):
    """Delete attempted on an instance with foreign references."""


class ExtentExists(KeyError):
    """An extent already exists."""


class ExtentDoesNotExist(KeyError):
    """An extent does not exist."""


class EntityExists(KeyError):
    """An entity already exists."""


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
