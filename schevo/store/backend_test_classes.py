"""schevo.store backend test classes.

For copyright, license, and warranty, see bottom of file.
"""

from StringIO import StringIO

from schevo import database
from schevo.lib import module


_db_cache = {
    # (format, version, evolve_skipped, schema_source, suffix):
    #   (db, fp),
    }
_cached_dbs = set(
    # db,
    )


class TestMethods_CreatesDatabase(object):

    __test__ = False

    @staticmethod
    def backend_base_open(test_object, suffix, schema_source, schema_version):
        """Perform the actual opening of a database, then return it.

        - `test_object`: The instance of the test class we're opening
          a database for.
        - `suffix`: The suffix to use on variable names when storing
          open databases and auxiliary information.
        - `schema_source`: Schema source code to use.
        - `schema_version`: Version of the schema to use.
        """
        db_name = 'db' + suffix
        contents = TestMethods_CreatesDatabase.backend_db_contents(
            test_object, suffix)
        fp = StringIO(contents)
        if len(contents) == 0:
            db = database.create(
                filename = None,
                backend_name = 'schevo.store',
                backend_args = dict(fp=fp, cache_size=100000),
                schema_source=schema_source,
                schema_version=schema_version,
                format=test_object.format,
                )
        else:
            db = database.open(
                filename = None,
                backend_name = 'schevo.store',
                backend_args = dict(fp=fp, cache_size=100000),
                )
        setattr(test_object, db_name, db)
        setattr(test_object, 'fp' + suffix, fp)
        return db

    @staticmethod
    def backend_close(test_object, suffix=''):
        """Perform the actual closing of a database.

        - `test_object`: The instance of the test class we're closing
          a database for.
        - `suffix`: The suffix to use on variable names when finding
          the database and auxiliary information for it.
        """
        db_name = 'db' + suffix
        db = getattr(test_object, db_name)
        if db not in _cached_dbs:
            db.close()
        delattr(test_object, 'fp' + suffix)

    @staticmethod
    def backend_convert_format(test_object, suffix, format):
        """Convert the internal structure format of an already-open database.

        - `test_object`: The instance of the test class we're
          converting a database for.
        - `suffix`: The suffix to use on variable names when finding
          the database and auxiliary information for it.
        """
        # Get the contents of the database from the fpv attribute.
        contents = TestMethods_CreatesDatabase.backend_db_contents(
            test_object, suffix)
        # Turn it into a fresh StringIO.
        fp = StringIO(contents)
        # Convert it to the requested format.
        database.convert_format(
            filename = None,
            backend_name = 'schevo.store',
            backend_args = dict(fp=fp),
            format = format,
            )
        # Turn it back into a fpv attribute.
        setattr(test_object, 'fpv' + suffix, fp.getvalue())

    @staticmethod
    def backend_reopen_finish(test_object, suffix):
        """Perform cleanup required at the end of a call to
        `self.reopen()` within a test.

        - `test_object`: The instance of the test class performing the
          reopen.
        - `suffix`: The suffix to use on variable names when finding
          the database and auxiliary information for it.
        """
        delattr(test_object, 'fpv' + suffix)

    @staticmethod
    def backend_reopen_save_state(test_object, suffix):
        """Save the state of a database file before it gets closed
        during a call to `self.reopen()` within a test.

        - `test_object`: The instance of the test class performing the
          reopen.
        - `suffix`: The suffix to use on variable names when finding
          the database and auxiliary information for it.
        """
        setattr(test_object, 'fpv' + suffix,
                getattr(test_object, 'fp' + suffix).getvalue())

    @staticmethod
    def backend_db_contents(test_object, suffix=''):
        """Internal method to return the file contents of a database."""
        value = ''
        if hasattr(test_object, 'fpv' + suffix):
            value = getattr(test_object, 'fpv' + suffix)
        return value


class TestMethods_CreatesSchema(TestMethods_CreatesDatabase):

    __test__ = False

    @staticmethod
    def backend_open(test_object, suffix, schema):
        """Perform the actual opening of a database for a test
        instance.

        - `test_object`: The instance of the test class we're opening
          a database for.
        - `suffix`: The suffix to use on variable names when storing
          open databases and auxiliary information.
        - `schema`: Schema source code to use.
        """
        format = test_object.format
        db_name = 'db' + suffix
        fpv_name = 'fpv' + suffix
        cache_key = (format, 1, None, schema, suffix)
        if (test_object._use_db_cache
            and cache_key in _db_cache
            and not hasattr(test_object, fpv_name)
            ):
            db, fp = _db_cache[cache_key]
            setattr(test_object, 'fp' + suffix, fp)
            if not hasattr(test_object, db_name):
                db.backend.open()
                db._reset_all()
            setattr(test_object, db_name, db)
        else:
            # Forget existing modules.
            for m in module.MODULES:
                module.forget(m)
            db = test_object._base_open(suffix, schema)
            if test_object._use_db_cache:
                fp = getattr(test_object, 'fp' + suffix)
                cache_key = (format, 1, None, schema, suffix)
                db_info = (db, fp)
                _db_cache[cache_key] = db_info
                _cached_dbs.add(db)
        return db


class TestMethods_EvolvesSchemata(TestMethods_CreatesDatabase):

    __test__ = False

    @staticmethod
    def backend_open(test_object):
        """Perform the actual opening of a database for a test
        instance.

        - `test_object`: The instance of the test class we're opening
          a database for.
        """
        format = test_object.format
        use_db_cache = test_object._use_db_cache
        db_name = 'db'
        ex_name = 'ex'
        fpv_name = 'fpv'
        schema = test_object.schemata[-1]
        version = test_object.schema_version
        skip_evolution = test_object.skip_evolution
        suffix = ''
        cache_key = (format, version, skip_evolution, schema, suffix)
        if (use_db_cache
            and cache_key in _db_cache
            and not hasattr(test_object, fpv_name)
            ):
            db, fp = _db_cache[cache_key]
            test_object.fp = fp
            if not hasattr(test_object, 'db'):
                db.backend.open()
                db._reset_all()
            test_object.db = db
        else:
            # Forget existing modules.
            for m in module.MODULES:
                module.forget(m)
            if not skip_evolution:
                # Open database with version 1.
                db = test_object._base_open(suffix, test_object.schemata[0])
                # Evolve to latest.
                for i in xrange(1, len(test_object.schemata)):
                    schema_source = test_object.schemata[i]
                    database.evolve(db, schema_source, version=i+1)
            else:
                # Open database with target version.
                db = test_object._base_open(
                    suffix, schema, schema_version=version)
            if use_db_cache:
                fp = test_object.fp
                _db_cache[cache_key] = (db, fp)
                _cached_dbs.add(db)
        return db


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
