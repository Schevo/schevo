"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_history.py $
$Id: utest_history.py 28338 2006-05-04 21:45:03Z dbinger $
"""
from schevo.store.connection import Connection
from schevo.store.file_storage import FileStorage2
from schevo.store.history import HistoryConnection
from schevo.store.persistent import PersistentTester as Persistent
from schevo.test import raises

import os
import tempfile


class TestHistory(object):

    def test_a(self):
        filename = tempfile.mktemp()
        s = FileStorage2(filename)
        connection = Connection(s)
        root = connection.get_root()
        root['a'] = Persistent()
        root['a'].b = 1
        connection.commit()
        root['a'].b = 2
        connection.commit()
        s.close()
        hc = HistoryConnection(filename)
        a = hc.get_root()['a']
        assert len(hc.get_storage().index.history) == 4
        assert a.b == 2
        hc.previous()
        assert a.b == 1
        hc.next()
        assert a.b == 2
        hc.previous()
        assert a.b == 1
        hc.previous()
        assert a._p_is_ghost()
        assert not hasattr(a, '__dict__')
        assert isinstance(a, Persistent)
        assert raises(KeyError, getattr, a, 'b')
        assert hc.get(a._p_oid) is a
        hc.next()
        assert a.b == 1
        hc.get_storage().fp.close()
        os.unlink(filename)

    def test_b(self):
        filename = tempfile.mktemp()
        s = FileStorage2(filename)
        connection = Connection(s)
        root = connection.get_root()
        root['a'] = Persistent()
        root['a'].b = 1
        connection.commit()
        root['b'] = Persistent()
        connection.commit()
        root['b'].a = root['a']
        root['a'].b = 2
        connection.commit()
        root['a'].b = 3
        connection.commit()
        s.close()
        hc = HistoryConnection(filename)
        a = hc.get_root()['a']
        assert len(hc.get_storage().index.history) == 6
        hc.previous_instance(a)
        assert a.b == 2
        hc.previous_instance(a)
        assert a.b == 1
        hc.previous_instance(a)
        assert not hasattr(a, '__dict__')
        assert hc.get_root().keys() == []
        hc.get_storage().fp.close()
        os.unlink(filename)
