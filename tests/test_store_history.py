"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_history.py $
$Id: utest_history.py 28338 2006-05-04 21:45:03Z dbinger $
"""
from schevo.store.connection import Connection
from schevo.store.file_storage import TempFileStorage
from schevo.store.history import HistoryConnection
from schevo.store.persistent import Persistent
from schevo.test import raises


class TestHistory(object):

    # XXX: These tests don't pass; figure out why.

    pass

##     def test_a(self):
##         connection = Connection(TempFileStorage())
##         root = connection.get_root()
##         root['a'] = Persistent()
##         root['a'].b = 1
##         connection.commit()
##         root['a'].b = 2
##         connection.commit()
##         hc = HistoryConnection(connection.get_storage().fp.name)
##         a = hc.get_root()['a']
##         assert len(hc.get_storage().index.history) == 4
##         assert a.b == 2
##         hc.previous()
##         assert a.b == 1
##         hc.next()
##         assert a.b == 2
##         hc.previous()
##         assert a.b == 1
##         hc.previous()
##         assert a._p_is_ghost()
##         assert not hasattr(a, '__dict__')
##         assert isinstance(a, Persistent)
##         raises(KeyError, getattr, a, 'b')
##         assert hc.get(a._p_oid) is a
##         hc.next()
##         assert a.b == 1

##     def test_b(self):
##         connection = Connection(TempFileStorage())
##         root = connection.get_root()
##         root['a'] = Persistent()
##         root['a'].b = 1
##         connection.commit()
##         root['b'] = Persistent()
##         connection.commit()
##         root['b'].a = root['a']
##         root['a'].b = 2
##         connection.commit()
##         root['a'].b = 3
##         connection.commit()
##         hc = HistoryConnection(connection.get_storage().fp.name)
##         a = hc.get_root()['a']
##         assert len(hc.get_storage().index.history) == 6
##         hc.previous_instance(a)
##         assert a.b == 2
##         hc.previous_instance(a)
##         assert a.b == 1
##         hc.previous_instance(a)
##         assert not hasattr(a, '__dict__')
##         assert hc.get_root().keys() == []
