"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_client_storage.py $
$Id: utest_client_storage.py 28137 2006-04-04 14:34:21Z dbinger $
"""
from schevo.store import run_durus
from schevo.store.client_storage import ClientStorage
from schevo.store.error import ReadConflictError
from schevo.store.serialize import pack_record
from schevo.store.storage_server import DEFAULT_HOST
from schevo.store.utils import p64
from popen2 import popen4
from sancho.utest import UTest, raises
from sets import Set
from time import sleep

class Test (UTest):

    address = (DEFAULT_HOST, 9123)

    def _pre(self):
        if type(self.address) is tuple:
            self.server = popen4('python %s --port=%s' % (
                run_durus.__file__, self.address[1]))
        else:
            self.server = popen4('python %s --address=%s' % (
                run_durus.__file__, self.address))
        sleep(3) # wait for bind

    def _post(self):
        run_durus.stop_durus(self.address)

    def check_client_storage(self):
        b = ClientStorage(address=self.address)
        c = ClientStorage(address=self.address)
        assert b.new_oid() == p64(1)
        assert b.new_oid() == p64(2)
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
        b.pack()
        assert len(list(b.gen_oid_record())) == 1
        raises(ReadConflictError, c.load, p64(0))
        raises(ReadConflictError, c.load, p64(0))
        assert Set(c.sync()) == Set([p64(0), p64(1)])
        assert record == c.load(p64(0))

class UnixDomainSocketTest(Test):

    address = "test.durus_server"

if __name__ == "__main__":
    Test()
    import sys
    if sys.platform != 'win32':
        UnixDomainSocketTest()
