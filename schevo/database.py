"""Schevo database.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize


from schevo import database1
from schevo import database2
from schevo.field import not_fget
from schevo import icon
from schevo.store.connection import Connection
from schevo.store.file_storage import FileStorage


format_dbclass = {
    # Default database class.
    None: database2.Database,

    # Format-specific database classes.
    1: database1.Database,
    2: database2.Database,
    }


format_converter = {
    2: database2.convert_from_format1,
    }


def convert_format(filename_or_fp, format):
    """Convert database to a new storage format.

    - `filename_or_fp`: The filename or file pointer to convert.
    - `format`: The format to convert to.
    """
    if isinstance(filename_or_fp, basestring):
        # If it's a string, assume it's a filename.
        fs = FileStorage(filename_or_fp)
        # Since it's an actual filesystem file, close the FileStorage after
        # the entire conversion is done.
        close_when_done = True
    else:
        # Otherwise, assume it's a file-like object.
        fs = FileStorage(fp=filename_or_fp)
        # Since StringIO and similar file-liike objects' values cannot be
        # inspected after closing, do not explicitly close the FileStorage
        # object when conversion is done.
        close_when_done = False
    # Check the format of the database.
    conn = Connection(fs)
    root = conn.get_root()
    # XXX: Better error checking might be handy.
    schevo = root['SCHEVO']
    original_format = schevo['format']
    # Convert one version at a time, ensuring that failures result in a
    # rollback to the database's original state.
    try:
        try:
            for new_format in xrange(original_format + 1, format + 1):
                converter = format_converter[new_format]
                converter(conn)
        except:
            conn.abort()
            raise
        else:
            conn.commit()
    finally:
        if close_when_done:
            fs.close()


def equivalent(db1, db2, require_identical_schema_source=True):
    """Return True if `db1` and `db2` are functionally equivalent, or False
    if they differ.

    - `db1` and `db2`: The open databases to compare.
    - `require_identical_schema_source`: True if `db1` and `db2` must have
      identical schema. This is typical, since this function is intended to test
      equivalence between a database that has been created at version `n` and a
      database that has been created at version 1 and then evolved to version
      `n`. Set to False if the schemata are non-identical, as in the unit tests
      for this function.  **BE CAREFUL** when doing so, and in particular,
      make sure field names are declared in the same order in each schema.

    "Functionally equivalent" in this scenario means that details meant to
    be used internally are ignored by this tool.  Rather, it performs a
    higher-level comparison of the database.  For example, the following
    details are ignored:

    - Entity OIDs
    - Entity revision numbers
    - Order of results when iterating over an extent
    """
    if require_identical_schema_source:
        if db1.schema_source != db2.schema_source:
            return False
    # Create value count dictionaries for each extent in each database.
    extents1, extents2 = {}, {}
    for extents, db in [(extents1, db1), (extents2, db2)]:
        for extent in db.extents():
            counts = {
                # value-tuple: instance-count,
                }
            extents[extent.name] = counts
            # Get field values for each entity in the extent, and increment
            # value counts.
            for entity in extent:
                field_map = entity.sys.field_map(not_fget)
                stop_entities = frozenset([entity])
                values = tuple(
                    field.db_equivalence_value(stop_entities)
                    for field in field_map.itervalues()
                    )
                counts[values] = counts.get(values, 0) + 1
    # Now that the structures are filled in, they can be directly compared.
    return extents1 == extents2


def evolve(db, schema_source, version):
    """Evolve database to new version and new schema source.

    - `db`: The database to evolve.
    - `schema_source`: The new schema source to evolve to.
    - `version`: The new version number of the database schema.
    """
    db._evolve(schema_source, version)
    db._on_open()


def inject(filename, schema_source, version):
    """Inject a new schema and schema version into a database file. DANGEROUS!

    PLEASE USE WITH CAUTION; this is not intended to be used in normal course
    of Schevo operation, but can be useful in some corner cases and during
    application development.

    Inject in **no way shape or form evolves data or updates internal
    structures** to reflect changes between the database's current schema and
    that provided in the `schema_source` argument.

    - `filename`: Filename of database to inject new schema into.
    - `schema_source`: The new schema source to inject into the database.
    - `version`: The new version number of the database schema to inject.
    """
    fs = FileStorage(filename)
    conn = Connection(fs)
    root = conn.get_root()
    schevo = root['SCHEVO']
    schevo['schema_source'] = schema_source
    schevo['version'] = version
    conn.commit()
    fs.close()


def open(filename=None, schema_source=None, schema_version=None,
         initialize=True, label='', fp=None, cache_size=100000,
         format_for_new=None):
    """Return an open database by opening an existing database or creating
    a new one.

    If a new database is created, it is assumed that the `schema_source` given
    is schema version 1.

    - `filename`: Filename of database to create or open, or None if using `fp`.
    - `schema_source`: Schema source to create a new database with, or None
      if not creating a new database.
    - `schema_version`: Schema version to create a new database with, if
      skipping evolution from version 1.
    - `initialize`: If True, will create initial values in the database if
      creating a new database.
    - `label`: The label of the database, to be used for a return value when
      the open database instance is passed to `schevo.label.label`.
    - `fp`: A file-like object, such as a StringIO instance, to use instead of
      opening a file in the filesystem.  None if using `filename`.
    - `cache_size`: The number of Python objects that the stoage backend
      will cache in memory before re-ghosting old objects.
    - `format_for_new`: The version number of the database format to use when
      creating a new database, or None to use the default format.
    """
    # Create a FileStorage instance for the database based on `fp` or
    # `filename` arguments.
    if fp is not None:
        fs = FileStorage(fp=fp)
    else:
        fs = FileStorage(filename)
    # Create a Connection instance for the file storage, with a specific
    # cache size.
    conn = Connection(fs, cache_size)
    # Determine the version of the database.
    root = conn.get_root()
    if 'SCHEVO' in root:
        schevo = root['SCHEVO']
        format = schevo['format']
    else:
        format = format_for_new
    # Determine database class based on format number.
    Database = format_dbclass[format]
    # Create the Database instance.
    db = Database(conn)
    if label:
        db.label = label
    # Synchronize it with the given schema source.
    db._sync(
        schema_source, schema_version=schema_version, initialize=initialize)
    # Install icon support and finalize opening of database.
    icon.install(db)
    db._on_open()
    return db


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
