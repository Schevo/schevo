"""
$URL: svn+ssh://svn/repos/trunk/durus/storage_server.py $
$Id: storage_server.py 28319 2006-05-02 19:01:44Z rmasse $
"""
from datetime import datetime
from schevo.store.logger import log, is_logging
from schevo.store.serialize import extract_class_name, split_oids
from schevo.store.utils import p32, u32, u64
from os.path import exists
from time import sleep
import errno
import select
import socket


STATUS_OKAY = 'O'
STATUS_KEYERROR = 'K'
STATUS_INVALID = 'I'

TIMEOUT = 10
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 2972


def recv(s, n):
    """(s:socket, n:int) -> str
    Call the recv() method on the socket, repeating as required until n bytes
    are received.  
    """
    data = []
    while n > 0:
        hunk = s.recv(min(n, 1000000))
        if not hunk:
            raise IOError, 'connection reset by peer'
        n -= len(hunk)
        data.append(hunk)
    return ''.join(data)

class _Client:

    def __init__(self, s, addr):
        self.s = s
        self.addr = addr
        self.invalid = set()

class ClientError(Exception):
    pass


class SocketAddress (object):

    def new(address, **kwargs):
        if isinstance(address, SocketAddress):
            return address
        elif type(address) is tuple:
            host, port = address
            return HostPortAddress(host=host, port=port)
        elif type(address) is str:
            return UnixDomainSocketAddress(address, **kwargs)
        else:
            raise ValueError(address)
    new = staticmethod(new)

    def get_listening_socket(self):
        sock = socket.socket(self.get_address_family(), socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind_socket(sock)
        sock.listen(40)
        return sock

class HostPortAddress (SocketAddress):

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port

    def __str__(self):
        return "%s:%s" % (self.host, self.port)

    def get_address_family(self):
        return socket.AF_INET

    def bind_socket(self, socket):
        socket.bind( (self.host, self.port))

    def get_connected_socket(self):
        sock = socket.socket(self.get_address_family(), socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            sock.connect((self.host, self.port))
        except socket.error, exc:
            error = exc.args[0]
            if error == errno.ECONNREFUSED:
                return None
            else:
                raise
        return sock

    def set_connection_options(self, s):
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.settimeout(TIMEOUT)

    def close(self, s):
        s.close()


import sys
if sys.platform != 'win32':

    from grp import getgrnam, getgrgid
    from os import unlink, stat, chown, geteuid, getegid, umask
    from pwd import getpwnam, getpwuid

    class UnixDomainSocketAddress (SocketAddress):

        def __init__(self, filename, owner=None, group=None, umask=None):
            self.filename = filename
            self.owner = owner
            self.group = group
            self.umask = umask

        def __str__(self):
            result = self.filename
            if exists(self.filename):
                filestat = stat(self.filename)
                uid = filestat.st_uid
                gid = filestat.st_gid
                rwx = ['---', '--x', '-w-', '-wx', 'r--', 'r-x', 'rw-', 'rwx']
                owner = getpwuid(uid).pw_name
                group = getgrgid(gid).gr_name
                result += ' (%s%s%s %s %s)' % (
                   rwx[filestat.st_mode >> 6 & 7],
                   rwx[filestat.st_mode >> 3 & 7],
                   rwx[filestat.st_mode & 7],
                   owner,
                   group)
            return result

        def get_address_family(self):
            return socket.AF_UNIX

        def bind_socket(self, s):
            if self.umask is not None:
                old_umask = umask(self.umask)
            try:
                s.bind(self.filename)
            except socket.error, exc:
                error = exc.args[0]
                if not exists(self.filename):
                    raise
                if stat(self.filename).st_size > 0:
                    raise
                if error == errno.EADDRINUSE:
                    connected = self.get_connected_socket()
                    if connected:
                        connected.close()
                        raise
                    unlink(self.filename)
                    s.bind(self.filename)
                else:
                    raise
            uid = geteuid()
            if self.owner is not None:
                if type(self.owner) is int:
                    uid = self.owner
                else:
                    uid = getpwnam(self.owner).pw_uid
            gid = getegid()
            if self.group is not None:
                if type(self.group) is int:
                    gid = self.group
                else:
                    gid = getgrnam(self.group).gr_gid
            if self.owner is not None or self.group is not None:
                chown(self.filename, uid, gid)
            if self.umask is not None:
                umask(old_umask)

        def get_connected_socket(self):
            sock = socket.socket(self.get_address_family(), socket.SOCK_STREAM)
            try:
                sock.connect(self.filename)
            except socket.error, exc:
                error = exc.args[0]
                if error in (errno.ENOENT, errno.ENOTSOCK, errno.ECONNREFUSED):
                    return None
                else:
                    raise
            return sock

        def set_connection_options(self, s):
            s.settimeout(TIMEOUT)

        def close(self, s):
            s.close()
            if exists(self.filename):
                unlink(self.filename)


class StorageServer:

    protocol = p32(1)

    def __init__(self, storage, host=DEFAULT_HOST,
                 port=DEFAULT_PORT, address=None):
        self.storage = storage
        self.clients = []
        self.sockets = []
        self.packer = None
        self.address = SocketAddress.new(address or (host, port))
        self.load_record = {}

    def serve(self):
        sock = self.address.get_listening_socket()
        log(20, 'Ready on %s with %s objects', self.address,
            self.storage.get_size())
        self.sockets.append(sock)
        try:
            while 1:
                if self.packer is not None:
                    timeout = 0.0
                else:
                    timeout = None
                r, w, e = select.select(self.sockets, [], [], timeout)
                for s in r:
                    if s is sock:
                        # new connection
                        conn, addr = s.accept()
                        self.address.set_connection_options(conn)
                        self.clients.append(_Client(conn, addr))
                        self.sockets.append(conn)
                    else:
                        # command from client
                        try:
                            self.handle(s)
                        except (ClientError, socket.error, socket.timeout), exc:
                            log(10, '%s', ''.join(map(str, exc.args)))
                            self.sockets.remove(s)
                            self.clients.remove(self._find_client(s))
                if self.packer is not None:
                    try:
                        self.packer.next()
                    except StopIteration:
                        log(20, 'Pack finished at %s' % datetime.now())
                        self.packer = None # done packing
        finally:
            self.address.close(sock)

    def handle(self, s):
        command_code = s.recv(1)
        if not command_code:
            raise ClientError('EOF from client')
        handler = getattr(self, 'handle_%s' % command_code, None)
        if handler is None:
            raise ClientError('No such command code: %r' % command_code)
        handler(s)

    def _find_client(self, s):
        for client in self.clients:
            if client.s is s:
                return client
        assert 0

    def handle_N(self, s):
        # new OID
        s.sendall(self.storage.new_oid())

    def handle_M(self, s):
        # new OIDs
        count = ord(recv(s, 1))
        log(10, "oids: %s", count)
        s.sendall(''.join([self.storage.new_oid() for j in xrange(count)]))

    def handle_L(self, s):
        # load
        oid = recv(s, 8)
        self._send_load_response(s, oid)

    def _send_load_response(self, s, oid):
        if oid in self._find_client(s).invalid:
            s.sendall(STATUS_INVALID)
        else:
            try:
                record = self.storage.load(oid)
            except KeyError:
                log(10, 'KeyError %s', u64(oid))
                s.sendall(STATUS_KEYERROR)
            else:
                if is_logging(5):
                    class_name = extract_class_name(record)
                    if class_name in self.load_record:
                        self.load_record[class_name] += 1
                    else:
                        self.load_record[class_name] = 1
                    log(4, 'Load %-7s %s', u64(oid), class_name)
                s.sendall(STATUS_OKAY + p32(len(record)) + record)

    def handle_C(self, s):
        # commit
        client = self._find_client(s)
        s.sendall(p32(len(client.invalid)) + ''.join(client.invalid))
        client.invalid.clear()
        tlen = u32(recv(s, 4))
        if tlen == 0:
            return # client decided not to commit (e.g. conflict)
        tdata = recv(s, tlen)
        logging_debug = is_logging(10)
        logging_debug and log(10, 'Committing %s bytes', tlen)
        self.storage.begin()
        i = 0
        oids = []
        while i < len(tdata):
            rlen = u32(tdata[i:i+4])
            i += 4
            oid = tdata[i:i+8]
            record = tdata[i+8:i+rlen]
            i += rlen
            if logging_debug:
                class_name = extract_class_name(record)
                log(10, '  oid=%-6s rlen=%-6s %s', u64(oid), rlen, class_name)
            self.storage.store(oid, record)
            oids.append(oid)
        assert i == len(tdata)
        self.storage.end()
        self._report_load_record()
        log(20, 'Committed %3s objects %s bytes at %s',
            len(oids), tlen, datetime.now())
        s.sendall(STATUS_OKAY)
        for c in self.clients:
            if c is not client:
                c.invalid.update(oids)

    def _report_load_record(self):
        if self.load_record and is_logging(5):
            log(5, '\n'.join(
                 "%8s: %s" % (item[1], item[0])
                 for item in sorted(self.load_record.items())))
            self.load_record.clear()

    def handle_S(self, s):
        # sync
        client = self._find_client(s)
        self._report_load_record()
        log(8, 'Sync %s', len(client.invalid))
        invalid = self.storage.sync()
        assert not invalid # should have exclusive access
        s.sendall(p32(len(client.invalid)) + ''.join(client.invalid))
        client.invalid.clear()

    def handle_P(self, s):
        # pack
        log(20, 'Pack started at %s' % datetime.now())
        if self.packer is None:
            self.packer = self.storage.get_packer()
        s.sendall(STATUS_OKAY)

    def handle_B(self, s):
        # bulk read of objects
        number_of_oids = u32(recv(s, 4))
        oid_str = recv(s, 8 * number_of_oids)
        oids = split_oids(oid_str)
        for oid in oids:
            self._send_load_response(s, oid)

    def handle_Q(self, s):
        # graceful quit
        log(20, 'Quit')
        raise SystemExit

    def handle_V(self, s):
        # Verify protocol version match.
        client_protocol = recv(s, 4)
        log(10, 'Client Protocol: %s', u32(client_protocol))
        assert len(self.protocol) == 4
        s.sendall(self.protocol)
        if client_protocol != self.protocol:
            raise ClientError("Protocol not supported.")

def wait_for_server(host=DEFAULT_HOST, port=DEFAULT_PORT, maxtries=30, 
    sleeptime=2, address=None):
    # Wait for the server to bind to the port.
    server_address = SocketAddress.new(address or (host, port))
    for attempt in range(maxtries):
        connected = server_address.get_connected_socket()
        if connected:
            connected.close()
            break
        sleep(sleeptime)
    else:
        raise SystemExit('Timeout waiting for address.')
