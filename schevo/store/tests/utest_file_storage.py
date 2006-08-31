"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_file_storage.py $
$Id: utest_file_storage.py 28063 2006-03-13 21:03:18Z dbinger $
"""
from sancho.utest import UTest
from schevo.store.file_storage import TempFileStorage, FileStorage
from schevo.store.file_storage import FileStorage1, FileStorage2
from schevo.store.serialize import pack_record
from schevo.store.utils import p64


class Test (UTest):

    def check_file_storage(self):
        self._check_file_storage(TempFileStorage())
        self._check_file_storage(FileStorage1())

    def _check_file_storage(self, storage):
        b = storage
        assert b.new_oid() == p64(1)
        assert b.new_oid() == p64(2)
        try:
            b.load(p64(0))
            assert 0
        except KeyError: pass
        record = pack_record(p64(0), 'ok', '')
        b.store(p64(0), record)
        b.begin()
        b.end()
        b.sync()
        b.begin()
        b.store(p64(1), pack_record(p64(1), 'no', ''))
        b.end()
        assert len(list(b.gen_oid_record())) == 2
        b.pack()
        import schevo.store.file_storage
        if schevo.store.file_storage.RENAME_OPEN_FILE:
            schevo.store.file_storage.RENAME_OPEN_FILE = False
            b.pack()
            c = FileStorage(b.get_filename(), readonly=True)
            try:
                c.pack()
                assert 0
            except IOError: # read-only storage
                pass
        b.close()
        try:
            b.pack()
            assert 0
        except IOError: # storage closed
            pass
        try:
            b.load(0)
            assert 0
        except IOError: # storage closed
            pass

## This test fails on Windows.

##     def check_reopen(self):
##         f = TempFileStorage()
##         filename = f.fp.name
##         g = FileStorage(filename, readonly=True)
##         h = FileStorage2(filename, readonly=True)



if __name__ == "__main__":
    Test()
