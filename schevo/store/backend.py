"""schevo.store backend.

For copyright, license, and warranty, see bottom of file.
"""

import sys

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

    description = 'Built-in backend, based on Durus 3.4'
    backend_args_help = """
    cache_size=SIZE
        Set the size of the in-memory object cache to SIZE, which is an
        integer specifying the maximum number of objects to keep in the
        cache.
    """

    __test__ = False

    BTree = BTree
    PDict = PersistentDict
    PList = PersistentList

    TestMethods_CreatesDatabase = TestMethods_CreatesDatabase
    TestMethods_CreatesSchema = TestMethods_CreatesSchema
    TestMethods_EvolvesSchemata = TestMethods_EvolvesSchemata

    def __init__(self, filename, fp=None, cache_size=100000):
        """Create a new `SchevoStoreBackend` instance.

        - `filename`: Name of file to open with this backend. If
          `None`, the backend will expect that you passed in a value
          for `fp` instead.
        - `fp`: (optional) File-like object to use instead of an
          actual file in the filesystem.
        - `cache_size`: Maximum number of objects to keep in the
          in-memory object cache.
        """
        self._filename = filename
        self._fp = fp
        self._cache_size = cache_size
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
                if name == 'cache_size':
                    kw[name] = int(value)
                else:
                    raise KeyError(
                        '%s is not a valid name for backend args' % name)
        return kw

    @classmethod
    def usable_by_backend(cls, filename):
        """Return (`True`, *additional backend args*) if the named
        file is usable by this backend, or `False` if not."""
        # Get first 128 bytes of file.
        try:
            f = open(filename, 'rb')
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
        self._is_open = False

    def get_root(self):
        """Return the backend's `root` object."""
        return self.conn.get_root()

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def open(self):
        """Open the underlying storage based on initial arguments."""
        if not self._is_open:
            try:
                self.storage = FileStorage(self._filename, fp=self._fp)
            except RuntimeError:
                raise DatabaseFileLocked()
            self.conn = Connection(self.storage, cache_size=self._cache_size)
            self._is_open = True

    def pack(self):
        """Pack the underlying storage."""
        self.conn.pack()

    def rollback(self):
        """Abort the current transaction."""
        self.conn.abort()


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
