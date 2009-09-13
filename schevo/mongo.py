"""mongodb backend."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os
import sys

from pymongo.connection import Connection

import schevo.database
import schevo.database_mongo
from schevo.lib import module


class MongoBackend(object):

    description = 'mongodb backend'
    backend_args_help = """
    """

    __test__ = False

    DatabaseClass = schevo.database_mongo.Database

    def __init__(self, filename, collection_name):
        """Create a new `MongoBackend` instance.

        - `filename`: Name of database to use.
        - `collection_name`: Name of collection to use.
        """
        self._db_name = filename
        self._collection_name = collection_name
        self._is_open = False
        self.open()

    @classmethod
    def args_from_string(cls, s):
        """Return a dictionary of keyword arguments based on a string given
        to a command-line tool."""
        kw = {}
        if s is not None:
            for arg in (p.strip() for p in s.split(',')):
                name, value = (p2.strip() for p2 in arg.split('='))
                if name == 'collection_name':
                    kw[name] = value
                else:
                    raise KeyError(
                        '%s is not a valid name for backend args' % name)
        return kw

    @classmethod
    def usable_by_backend(cls, filename):
        """Return (`True`, *additional backend args*) if the named
        file is usable by this backend, or `False` if not."""
        return False

    @property
    def has_db(self):
        """Return `True` if the backend contains a Schevo database."""
        return self._collection.find_one({'SCHEVO': True}) is not None

    def close(self):
        """Close the underlying storage (and the connection if
        needed)."""
        self._is_open = False

    def open(self):
        """Open the underlying storage based on initial arguments."""
        if not self._is_open:
            self._connection = Connection()
            self._db = self._connection[self._db_name]
            self._collection = self._db[self._collection_name]
            self._is_open = True

    # Transaction operations.

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Abort the current transaction."""
        self.conn.abort()

    # Not applicable but expected in the API.

    def get_root(self):
        """Return the backend's `root` object."""
        pass

    def pack(self):
        """Pack the underlying storage."""
        pass

    # Test classes.

    class TestMethods_CreatesDatabase(object):

        __test__ = False

        @staticmethod
        def backend_base_open(test_object, suffix,
                              schema_source, schema_version):
            """Perform the actual opening of a database, then return it.

            - `test_object`: The instance of the test class we're opening
              a database for.
            - `suffix`: The suffix to use on variable names when storing
              open databases and auxiliary information.
            - `schema_source`: Schema source code to use.
            - `schema_version`: Version of the schema to use.
            """
            db_name = 'db' + suffix
            filename = 'schevo_test'
            collection_name = test_object.__class__.__name__
            conn = Connection()
            collection = conn[filename][collection_name]
            has_db = collection.find_one({'SCHEVO': True}) is not None
            if not has_db:
                db = schevo.database.create(
                    filename=filename,
                    backend_name='mongo',
                    backend_args=dict(collection_name=collection_name),
                    schema_source=schema_source,
                    schema_version=schema_version,
                    )
            else:
                db = schevo.database.open(
                    filename=filename,
                    backend_name='mongo',
                    backend_args=dict(collection_name=collection_name),
                    )
            setattr(test_object, db_name, db)
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
            db.close()

        @staticmethod
        def backend_convert_format(test_object, suffix, format):
            raise NotImplementedError()

        @staticmethod
        def backend_reopen_finish(test_object, suffix):
            pass

        @staticmethod
        def backend_reopen_save_state(test_object, suffix):
            pass

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
            # Forget existing modules.
            for m in module.MODULES:
                module.forget(m)
            db = test_object._base_open(suffix, schema)
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
            db_name = 'db'
            ex_name = 'ex'
            schema = test_object.schemata[-1]
            version = test_object.schema_version
            skip_evolution = test_object.skip_evolution
            suffix = ''
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
            return db
