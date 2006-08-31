#!/usr/bin/env python
"""A client that stress tests a Durus storage server.
"""

from __future__ import division
[division] # for checker
import os
from popen2 import popen4
import sys
import time
import random
import md5
from optparse import OptionParser
from schevo.store import run_durus
from schevo.store.persistent import PersistentTester as Persistent
from schevo.store.storage_server import DEFAULT_PORT, DEFAULT_HOST
from schevo.store.client_storage import ClientStorage
from schevo.store.connection import Connection
from schevo.store.error import ConflictError

MAX_OBJECTS = 10000
MAX_DEPTH = 20
MAX_OBJECT_SIZE = 4000

_SLEEP_TIMES = [0, 0, 0, 0, 0.1, 0.2]
def maybe_sleep():
    time.sleep(random.choice(_SLEEP_TIMES))

def randbool():
    return random.random() <= 0.5

class Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1

    def __cmp__(self, other):
        return cmp(self.value, other)

class Container(Persistent):
    def __init__(self, sum=0, value=None, children=None):
        self.sum = sum
        if value is None:
            self.value = random.randint(0, 10)
        else:
            self.value = value
        if children is None:
            self.children = []
        else:
            self.children = children
        self.generate_data()

    def get_checksum(self):
        return md5.new(self.data).digest()

    def generate_data(self):
        self.data = os.urandom(random.randint(0, MAX_OBJECT_SIZE))
        self.checksum = self.get_checksum()

    def create_children(self, counter, depth=1):
        for i in range(random.randint(1, 20)):
            if counter > MAX_OBJECTS:
                break
            child = Container(self.sum + self.value)
            counter.inc()
            self.children.append(child)
            if depth < MAX_DEPTH:
                child.create_children(counter, depth + 1)

    def verify(self, sum=0, all=False):
        print self, self.sum
        assert self.sum == sum
        assert self.get_checksum() == self.checksum
        if self.children:
            if all:
                for child in self.children:
                    child.verify(sum + self.value)
            else:
                random.choice(self.children).verify(sum + self.value)

# make pickle happy
from schevo.store.tests.stress import Container

def init_db(connection):
    print 'creating object graph'
    root = connection.get_root()
    obj = Container()
    root['obj'] = obj
    obj.create_children(Counter())

def verify_db(connection, all=False):
    print 'verifying'
    root = connection.get_root()
    root['obj'].verify(all=all)

def mutate_db(connection):
    n = random.choice([2**i for i in range(8)])
    print 'mutating', n, 'objects'
    for i in range(n):
        depth = random.randint(1, MAX_DEPTH)
        parent = connection.get_root()['obj']
        while True:
            k = random.randint(0, len(parent.children)-1)
            depth -= 1
            if depth > 0 and parent.children[k].children:
                parent = parent.children[k]
            else:
                obj = parent.children[k]
                break
        if randbool():
            # replace object with a new instance
            k = parent.children.index(obj)
            obj = Container(obj.sum, obj.value, obj.children)
            parent.children[k] = obj
            parent._p_note_change()
        else:
            # just mutate it's data
            obj.generate_data()

def main():
    parser = OptionParser()
    parser.set_description('Stress test a Durus Server')
    parser.add_option('--port', dest='port', default=DEFAULT_PORT, type='int',
                      help='Port to listen on. (default=%s)' % DEFAULT_PORT)
    parser.add_option('--host', dest='host', default=DEFAULT_HOST,
                      help='Host to listen on. (default=%s)' % DEFAULT_HOST)
    parser.add_option('--cache_size', dest="cache_size", default=4000,
                      type="int",
                      help="Size of client cache (default=4000)")
    parser.add_option('--max-loops', dest='loops', default=10, type='int',
                      help='Maximum number of loops before exiting.')

    (options, args) = parser.parse_args()

    storage = ClientStorage(host=options.host, port=options.port)
    connection = Connection(storage, cache_size=options.cache_size)
    try:
        if 'obj' not in connection.get_root():
            init_db(connection)
            verify_db(connection, all=True)
            print 'start committing'
            connection.commit()
            print 'end committing'
    except ConflictError:
        print 'conflict error'
        connection.abort()
    n = options.loops
    print n, ' max loops'
    while n is None or n > 0:
        print n
        if n is not None:
            n -= 1
        try:
            if hasattr(sys, 'gettotalrefcount'):
                print 'refs =', sys.gettotalrefcount()
            if randbool():
                connection.abort()
            verify_db(connection)
            mutate_db(connection)
            connection.commit()
            maybe_sleep()
        except ConflictError:
            print 'conflict'
            connection.abort()
            maybe_sleep()

if __name__ == '__main__':
    main()
##     server = popen4('python %s --port=%s' % (
##         run_durus.__file__, DEFAULT_PORT))
##     time.sleep(3) # wait for bind
##     try:
##         main()
##     finally:
##         run_durus.stop_durus((DEFAULT_HOST, DEFAULT_PORT))
