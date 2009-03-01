"""schevo.error unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
#     database-tour.txt
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
# - Metadata
#     extent_name
#     index_spec


# ======================================================================
# KeyCollision
# - Raised by
#     schevo.database2:_index_add
#     schevo.database2:_index_validate
# - Caught by
#     schevo.transaction:Delete._execute
# - Tested by
#     test_entity_extent
#     test_evolve
#     test_field_entitylist
#     test_field_entityset
#     test_field_entitysetset
#     test_label
#     test_transaction
# - Metadata
#     extent_name
#     key_spec
#     field_values


# ======================================================================
# TransactionAlreadyExecuted
# - Raised by
#     schevo.database2:Database.execute
# - Tested by
#     test_transaction
# - Metadata
#     transaction


# ======================================================================
# TransactionExpired
# - Raised by
#     schevo.transaction:Delete._execute
#     schevo.transaction:Update._execute
# - Tested by
#     test_transaction
# - Metadata
#     transaction
#     original_rev
#     current_rev


# ======================================================================
# TransactionFieldsNotChanged
# - Raised by
#     schevo.transaction:Update._execute
# - Tested by
#     test_transaction_require_changes
# - Metadata
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
# - Metadata
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
# - Preferred metadata
#     reason
#     class_name
#     field_name
# - Metadata
#     reason


# ======================================================================
# KeyIndexOverlap
# - Raised by
#     schevo.entity:EntityMeta.validate_key_and_index_specs
# - Tested by
#     test_schema
# - Metadata
#     class_name
#     overlapping_specs


# ======================================================================
# TransactionExecuteRedefinitionRestricted
# - Raised by
#     schevo.transaction:TransactionMeta.__init__
# - Tested by
#     transaction-hook-methods.txt
# - Metadata
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
# - Preferred metadata
#     entity_class_name
#     field_class_name
#     field_name
# - Metadata
#     reason
