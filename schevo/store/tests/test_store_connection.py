"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_connection.py $
$Id: utest_connection.py 28275 2006-04-28 17:44:20Z dbinger $
"""

import os
import sys
from time import sleep

from schevo.store.connection import Connection, touch_every_reference
from schevo.store.error import ConflictError
from schevo.store.file_storage import TempFileStorage
from schevo.store.persistent import PersistentTester as Persistent
from schevo.store.persistent import ConnectionBase, PersistentBase
from schevo.store.storage import get_reference_index, get_census
from schevo.store.storage import gen_referring_oid_record, Storage
from schevo.store.utils import p64
from schevo.test import raises


class TestConnection(object):

    def _get_storage(self):
        return TempFileStorage()

    def test_check_connection(self):
        self.conn=conn=Connection(self._get_storage())
        self.root=root=conn.get_root()
        assert root._p_is_ghost() == True
        assert root is conn.get(p64(0))
        assert root is conn.get(0)
        assert conn is root._p_connection
        assert conn.get(p64(1)) == None
        conn.abort()
        conn.commit()
        assert root._p_is_ghost() == True
        root['a'] = Persistent()
        assert root._p_is_unsaved() == True
        assert root['a']._p_is_unsaved() == True
        root['a'].f=2
        assert conn.changed.values() == [root]
        conn.commit()
        assert root._p_is_saved()
        assert conn.changed.values() == []
        root['a'] = Persistent()
        assert conn.changed.values() == [root]
        root['b'] = Persistent()
        root['a'].a = 'a'
        root['b'].b = 'b'
        conn.commit()
        root['a'].a = 'a'
        root['b'].b = 'b'
        conn.abort()
        conn.shrink_cache()
        root['b'].b = 'b'
        del conn

    def test_check_shrink(self):
        storage = self._get_storage()
        self.conn=conn=Connection(storage, cache_size=3)
        self.root=root=conn.get_root()
        root['a'] = Persistent()
        root['b'] = Persistent()
        root['c'] = Persistent()
        assert self.root._p_is_unsaved()
        conn.commit()
        root['a'].a = 1
        conn.commit()
        root['b'].b = 1
        root['c'].c = 1
        root['d'] = Persistent()
        root['e'] = Persistent()
        root['f'] = Persistent()
        conn.commit()
        root['f'].f = 1
        root['g'] = Persistent()
        conn.commit()
        conn.pack()

    def test_check_storage_tools(self):
        connection = Connection(self._get_storage())
        root = connection.get_root()
        root['a'] = Persistent()
        root['b'] = Persistent()
        connection.commit()
        index = get_reference_index(connection.get_storage())
        assert index == {p64(1): [p64(0)], p64(2): [p64(0)]}
        census = get_census(connection.get_storage())
        assert census == {'PersistentDict':1, 'PersistentTester':2}
        references = list(gen_referring_oid_record(connection.get_storage(),
                                                   p64(1)))
        assert references == [(p64(0), connection.get_storage().load(p64(0)))]
        class Fake(object):
            pass
        s = Fake()
        s.__class__ = Storage
        assert raises(RuntimeError, s.__init__)
        assert raises(NotImplementedError, s.load, None)
        assert raises(NotImplementedError, s.begin)
        assert raises(NotImplementedError, s.store, None, None)
        assert raises(NotImplementedError, s.end)
        assert raises(NotImplementedError, s.sync)
        assert raises(NotImplementedError, s.gen_oid_record)

    def test_check_touch_every_reference(self):
        connection = Connection(self._get_storage())
        root = connection.get_root()
        root['a'] = Persistent()
        root['b'] = Persistent()
        from schevo.store.persistent_list import PersistentList
        root['b'].c = PersistentList()
        connection.commit()
        touch_every_reference(connection, 'PersistentList')
        assert root['b']._p_is_unsaved()
        assert root['b'].c._p_is_unsaved()
        assert not root._p_is_unsaved()
