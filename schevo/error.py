"""Schevo-specific exceptions.

For copyright, license, and warranty, see bottom of file.
"""


class Restricted(RuntimeError):
    """The attempted operation was restricted."""


class DatabaseClosed(RuntimeError):
    """The database or database connection was closed."""


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


class EntityFieldAllowAttributeIsRequired(Exception):
    """The allow attribute is required on an entity field."""


class FieldDoesNotExist(KeyError):
    """A field does not exist."""


class FindoneFoundMoreThanOne(Exception):
    """Findone found more than one match."""


class IndexDoesNotExist(Exception):
    """An index does not exist."""


class KeyCollision(KeyError):
    """An entity with the given keys already exists."""


class TransactionAlreadyExecuted(RuntimeError):
    """A transaction was already executed and cannot be re-executed."""


class TransactionFieldsNotChanged(RuntimeError):
    """No transaction field values were changed."""


class TransactionNotExecuted(RuntimeError):
    """A transaction was not yet executed."""


class TransactionRuleViolation(RuntimeError):
    """A transaction rule was violated."""


class SchemaError(SyntaxError):
    """An error was found in the schema."""


class AmbiguousFieldDefinition(SchemaError):
    """A field defition's attributes were ambiguous."""


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
