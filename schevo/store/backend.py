"""schevo.store backend."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os
import sys
from StringIO import StringIO

from schevo import database
from schevo.error import DatabaseFileLocked
from schevo.store.backend_test_classes import (
    TestMethods_CreatesDatabase,
    TestMethods_CreatesSchema,
    TestMethods_EvolvesSchemata,
    )
from schevo.store.btree import BTree
from schevo.store.persistent_dict import PersistentDict
from schevo.store.persistent_list import PersistentList
from schevo.store.file_storage import FileStorage
from schevo.store.connection import Connection


class SchevoStoreBackend(object):

    DEFAULT_CACHE_SIZE = 100000

    description = 'Built-in backend, based on Durus 3.4'
    backend_args_help = """
    Use "schevostore:///:memory:" for an in-memory database.

    cache_size=%(DEFAULT_CACHE_SIZE)i (int)
        Set the size of the in-memory object cache to SIZE, which is an
        integer specifying the maximum number of objects to keep in the
        cache.

    fp=None (file-like object)
        Optional file object to use instead of an actual file in the
        filesystem.
    """ % locals()

    __test__ = False

    BTree = BTree
    PDict = PersistentDict
    PList = PersistentList

    TestMethods_CreatesDatabase = TestMethods_CreatesDatabase
    TestMethods_CreatesSchema = TestMethods_CreatesSchema
    TestMethods_EvolvesSchemata = TestMethods_EvolvesSchemata

    def __init__(self,
                 database,
                 fp=None,
                 cache_size=DEFAULT_CACHE_SIZE,
                 ):
        self.database = database
        if database == ':memory:' and fp is None:
            fp = StringIO()
        self.fp = fp
        self.cache_size = cache_size
        self.is_open = False
        self.open()

    @classmethod
    def usable_by_backend(cls, filename):
        """Return (`True`, *additional backend args*) if the named
        file is usable by this backend, or `False` if not."""
        # Get first 128 bytes of file.
        f = open(filename, 'rb')
        try:
            try:
                header = f.read(128)
            except IOError:
                if sys.platform == 'win32':
                    raise DatabaseFileLocked()
                else:
                    raise
        finally:
            f.close()
        # Look for Durus file storage signature and schevo.store
        # module signature.
        if header[:5] == 'DFS20':
            if 'schevo.store.persistent_dict' in header:
                return (True, {})
        return False

    @property
    def has_db(self):
        """Return `True` if the backend contains a Schevo database."""
        return self.get_root().has_key('SCHEVO')

    def close(self):
        """Close the underlying storage (and the connection if
        needed)."""
        self.storage.close()
        self.is_open = False

    def get_root(self):
        """Return the backend's `root` object."""
        return self.conn.get_root()

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def open(self):
        """Open the underlying storage based on initial arguments."""
        if not self.is_open:
            try:
                self.storage = FileStorage(self.database, fp=self.fp)
            except RuntimeError:
                raise DatabaseFileLocked()
            self.conn = Connection(self.storage, cache_size=self.cache_size)
            self.is_open = True

    def pack(self):
        """Pack the underlying storage."""
        self.conn.pack()

    def rollback(self):
        """Abort the current transaction."""
        self.conn.abort()
