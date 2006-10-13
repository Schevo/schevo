"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_client_storage.py $
$Id: utest_client_storage.py 28137 2006-04-04 14:34:21Z dbinger $
"""
from schevo.store import run_durus
from schevo.store.client_storage import ClientStorage
from schevo.store.error import ReadConflictError, DurusKeyError
from schevo.store.serialize import pack_record
from schevo.store.storage_server import DEFAULT_HOST
from schevo.store.utils import p64
from popen2 import popen4
from schevo.test import raises
from time import sleep
import sys


class Test(object):

    address = (DEFAULT_HOST, 9123)

    def setUp(self):
        if type(self.address) is tuple:
            self.server = popen4('python %s --port=%s' % (
                run_durus.__file__, self.address[1]))
        else:
            self.server = popen4('python %s --address=%s' % (
                run_durus.__file__, self.address))
        sleep(3) # wait for bind

    def tearDown(self):
        run_durus.stop_durus(self.address)

    def test_check_client_storage(self):
        b = ClientStorage(address=self.address)
        c = ClientStorage(address=self.address)
        print self.address
        oid = b.new_oid()
        assert oid == p64(1), repr(oid)
        oid = b.new_oid()
        assert oid == p64(2), repr(oid)
        try:
            b.load(p64(0))
            assert 0
        except KeyError: pass
        record = pack_record(p64(0), 'ok', '')
        b.begin()
        b.store(p64(0), record)
        assert b.end() is None
        b.load(p64(0))
        assert b.sync() == []
        b.begin()
        b.store(p64(1), pack_record(p64(1), 'no', ''))
        b.end()
        assert len(list(b.gen_oid_record())) == 2
        records = b.bulk_load([p64(0), p64(1)])
        assert len(list(records)) == 2
        records = b.bulk_load([p64(0), p64(1), p64(2)])
        assert raises(DurusKeyError, list, records)
        b.pack()
        assert len(list(b.gen_oid_record())) == 1
        assert raises(ReadConflictError, c.load, p64(0))
        assert raises(ReadConflictError, c.load, p64(0))
        assert set(c.sync()) == set([p64(0), p64(1)])
        assert record == c.load(p64(0))


if sys.platform != 'win32':

    class UnixDomainSocketTest(Test):
        address = "test.durus_server"
