"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_storage.py $
$Id: utest_storage.py 27487 2005-09-29 13:18:29Z dbinger $
"""
from schevo.test import raises
from schevo.store.storage import MemoryStorage
from schevo.store.serialize import pack_record
from schevo.store.utils import p64

class Test(object):

    def test_check_memory_storage(self):
        b = MemoryStorage()
        assert b.new_oid() == p64(1)
        assert b.new_oid() == p64(2)
        assert raises(KeyError, b.load, p64(0))
        record = pack_record(p64(0), 'ok', '')
        b.begin()
        b.store(p64(0), record)
        b.end()
        b.sync()
        b.begin()
        b.store(p64(1), pack_record(p64(1), 'no', ''))
        b.end()
        assert len(list(b.gen_oid_record())) == 2
        assert record == b.load(p64(0))
        records = b.bulk_load([p64(0), p64(1)])
        assert len(list(records)) == 2
        records = b.bulk_load([p64(0), p64(1), p64(2)])
        assert raises(KeyError, list, records)
