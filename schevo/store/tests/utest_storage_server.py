"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_storage_server.py $
$Id: utest_storage_server.py 28137 2006-04-04 14:34:21Z dbinger $
"""
from schevo.store.file_storage import TempFileStorage
from schevo.store.storage_server import StorageServer, recv
from random import choice
from sancho.utest import UTest

class Test (UTest):

    def check_storage_server(self):
        storage = TempFileStorage()
        host = '127.0.0.1'
        port = 2972
        server=StorageServer(storage, host=host, port=port)
        file = "test.durus_server"
        server=StorageServer(storage, address=file)

    def check_receive(self):
        class Dribble:
            def recv(x, n):
                return choice(['a', 'bb'])[:n]
        fake_socket = Dribble()
        recv(fake_socket, 30)


if __name__ == "__main__":
    Test()

