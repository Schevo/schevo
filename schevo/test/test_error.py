"""schevo.error unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema, raises
from schevo.constant import UNASSIGNED
import schevo.error


# ======================================================================
# Restricted
# - base class, not directly raised


# ======================================================================
# DatabaseAlreadyExists
# - Raised by
#     schevo.database:copy
#     schevo.database:create
# - Untested
# - Metadata
#     filename


# ======================================================================
# DatabaseDoesNotExist
# - Raised by
#     schevo.database:copy
#     schevo.database:open
# - Untested
# - Metadata
#     filename


# ======================================================================
# DatabaseExecutingTransaction
# - Raised by
#     schevo.database2:Database._set_label
# - Tested by
#     test_label
# - No metadata.


# ======================================================================
# DatabaseFormatMismatch
# - Raised by
#     schevo.database:copy
# - Untested
# - Metadata
#     current_format
#     required_format


# ======================================================================
# DatabaseMismatch
# - Raised by
#     schevo.field:_EntityBase._db_resolve
# - Tested by
#     test_transaction
# - Metadata
#     field_name
#     field_value


# ======================================================================
# DatabaseVersionMismatch
# - Raised by
#     schevo.database2:Database._evolve
# - Tested by
#     test_evolve
# - Metadata
#     current_version
#     expected_version
#     requested_version


# ======================================================================
# DeleteRestricted
# - Raised by
#     schevo.database1:Database._delete_entity
#     schevo.database2:Database._delete_entity
#     schevo.transaction:Delete._execute
# - Tested by
#     test_entity_extent
#     test_on_delete
#     test_transaction
# - Metadata
#     restrictions (list of (entity, referring_entity, referring_field_name))


# ======================================================================
# ExtentExists
# - Raised by
#     schevo.database2:Database._create_extent
# - Tested by
#     test_database
# - Metadata
#     extent_name


# ======================================================================
# ExtentDoesNotExist
# - Raised by
#     schevo.database2:Database._extent_map
#     schevo.entity:EntitySys.links_filter
#     schevo.schema:prep
# - Tested by
#     test_database
#     test_entity_extent
#     test_evolve
# - Metadata
#     extent_name


# ======================================================================
# EntityExists
# - Raised by
#     schevo.database1:Database._create_entity
#     schevo.database2:Database._create_entity
# - Untested
# - Metadata
#     oid
#     extent_name


# ======================================================================
# EntityDoesNotExist
# - Raised by
#     schevo.database1:Database._create_entity
#     schevo.database1:Database._update_entity
#     schevo.database2:Database._create_entity
#     schevo.database2:Database._update_entity
#     schevo.database2:Database._entity_map
#     schevo.database2:Database._entity_extent_map
#     schevo.extent:Extent.__getitem__
# - Tested by
#     database-tour.txt
#     test_database
#     test_entity_extent
#     test_transaction
# - Metadata
#     extent_name
#     field_name (exclusive of oid)
#     oid        (exclusive of field_name)


# ======================================================================
# FieldDoesNotExist
# - Raised by
#     schevo.database1:Database._find_entity_oids
#     schevo.database2:Database._entity_links
#     schevo.database2:Database._find_entity_oids
#     schevo.database2:Database._sync_extents
#     schevo.entity:EntitySys.links_filter
#     schevo.query:Intersection.remove_match
# - Tested by
#     test_entity_extent
#     test_evolve
#     test_query
# - Metadata
#     object_or_name
#     field_name
#     new_field_name (optional)


# ======================================================================
# FindoneFoundMoreThanOne
# - Raised by
#     schevo.extent:Extent.findone
# - Tested by
#     test_entity_extent
# - Metadata
#     extent_name
#     criteria


# ======================================================================
# IndexDoesNotExist
# - Raised by
#     schevo.database2:Database._by_entity_oids
#     schevo.database2:Database._enforce_index_field_ids
#     schevo.database2:Database._relax_index
# - Untested
# - Possible metadata
#     extent_name
#     index_spec


# ======================================================================
# KeyCollision
# - Raised by
#     schevo.database2:_index_add
#     schevo.database2:_index_validate
# - Tested by
#     test_entity_extent
#     test_evolve
#     test_field_entitylist
#     test_field_entityset
#     test_field_entitysetset
#     test_label
#     test_transaction
# - Possible metadata
#     extent_name
#     key_spec
#     field_values


# ======================================================================
# TransactionAlreadyExecuted
# - Raised by
#     schevo.database2:Database.execute
# - Tested by
#     test_transaction
# - Possible metadata
#     transaction


# ======================================================================
# TransactionExpired
# - Raised by
#     schevo.transaction:Delete._execute
#     schevo.transaction:Update._execute
# - Tested by
#     test_transaction
# - Possible metadata
#     transaction
#     original_rev
#     current_rev


# ======================================================================
# TransactionFieldsNotChanged
# - Raised by
#     schevo.transaction:Update._execute
# - Tested by
#     test_transaction_require_changes
# - Possible metadata
#     transaction


# ======================================================================
# TransactionNotExecuted
# - Raised by
#     schevo.transaction:Transaction._changes
#     schevo.transaction:Transaction._undo
#     schevo.transaction:Inverse.__init__
# - Tested by
#     test_change
#     test_transaction
# - Possible metadata
#     transaction


# ======================================================================
# TransactionRuleViolation
# - Raised by custom transactions.
# - Untested in Schevo core.
# - Possible metadata
#     require message
#     accept optional keyword arguments


# ======================================================================
# SchemaFileIOError
# - Raised by
#     schevo.schema:read
#     schevo.schema:schema_filename_prefix
# - Tested by
#     test_prefix
# - Possible metadata
#     path


# ======================================================================
# SchemaError
# - base class, not directly raised


# ======================================================================
# AmbiguousFieldDefinition
# - Raised by
#     schevo.field:_EntityBase._init_final
# - Untested.
# - Possible metadata
#     class_name
#     field_name


# ======================================================================
# KeyIndexOverlap
# - Raised by
#     schevo.entity:EntityMeta.validate_key_and_index_specs
# - Tested by
#     test_schema
# - Possible metadata
#     class_name
#     spec


# ======================================================================
# TransactionExecuteRedefinitionRestricted
# - Raised by
#     schevo.transaction:TransactionMeta.__init__
# - Tested by
#     transaction-hook-methods.txt
# - Possible metadata
#     class_name
#     base_classes


# ======================================================================
# UnsupportedFieldType
# - Raised by
#     schevo.database1:_create_entity
#     schevo.database1:_update_entity
#     schevo.database1:_schema_format_compatibility_check
# - Tested by
#     test_field_entitylist
#     test_field_entityset
#     test_field_entitysetset
# - Possible metadata
#     entity_class_name
#     field_class_name
#     field_name


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
