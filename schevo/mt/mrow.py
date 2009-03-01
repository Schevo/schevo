"""Multiple-reader-one-writer resource locking."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

__svn__ = "$Id$"
__rev__ = "$Rev$"[6:-2]

from thread import get_ident
import threading


def acquire_locked(fn):
    def _acquire_locked_wrapper(self, *args, **kw):
        L = self.acquire_lock
        try:
            L.acquire()
            result = fn(self, *args, **kw)
        finally:
            L.release()
        return result
    return _acquire_locked_wrapper


def release_locked(fn):
    def _release_locked_wrapper(self, *args, **kw):
        L = self.release_lock
        try:
            L.acquire()
            result = fn(self, *args, **kw)
        finally:
            L.release()
        return result
    return _release_locked_wrapper


class RWLock(object):
    """MROW resource lock."""

    def __init__(self):
        self.acquire_lock = threading.Lock()
        self.release_lock = threading.Lock()
        self.sublocks = []
        self.waiting = []
        self.readers = 0
        self.writing = False
        self.thread_readers = {}
        self.thread_writers = {}

    @acquire_locked
    def reader(self):
        """Return an acquired read lock."""
        thread_readers, thread_writers = (
            self.thread_readers, self.thread_writers)
        ident = get_ident()
        if ident in thread_readers:
            sublock, count = thread_readers[ident]
            thread_readers[ident] = (sublock, count + 1)
            return sublock
        elif ident in thread_writers:
            # Writers are inherently readers, so treat as a reentrant
            # write lock.
            sublock, count = thread_writers[ident]
            thread_writers[ident] = (sublock, count + 1)
            return sublock
        sublock = RLock(self)
        if self.writing:
            # Wait for acquired writers to release.
            self.waiting.append(sublock)
            sublock.acquire()
        sublock.acquire()
        self.readers += 1
        self.sublocks.append(sublock)
        thread_readers[ident] = (sublock, 1)
        return sublock

    @acquire_locked
    def writer(self):
        """Return an acquired write lock."""
        thread_readers, thread_writers = (
            self.thread_readers, self.thread_writers)
        ident = get_ident()
        wasReader = None
        if ident in thread_writers:
            sublock, count = thread_writers[ident]
            thread_writers[ident] = (sublock, count + 1)
            return sublock
        elif ident in thread_readers:
            # Readers-turned-writers must wait for any reads to complete
            # before turning into writers.
            sublock, count = thread_readers[ident]
            del thread_readers[ident]
            self.readers -= 1
            self.sublocks.remove(sublock)
            sublock._release()
            wasReader = sublock
        sublock = WLock(self)
        if self.readers or self.writing:
            # Wait for acquired readers/writers to release.
            self.waiting.append(sublock)
            sublock.acquire()
        sublock.acquire()
        self.writing = True
        self.sublocks.append(sublock)
        if wasReader is None:
            count = 0
        else:
            wasReader.becameWriter = sublock
        thread_writers[ident] = (sublock, count + 1)
        return sublock

    @release_locked
    def _release_r(self, sublock):
        sublocks = self.sublocks
        if sublock in sublocks:
            thread_readers = self.thread_readers
            ident = get_ident()
            count = thread_readers[ident][1] - 1
            if count:
                thread_readers[ident] = (sublock, count)
            else:
                del thread_readers[ident]
                self.readers -= 1
                sublocks.remove(sublock)
                sublock._release()
                waiting = self.waiting
                if waiting and not self.readers:
                    # If a lock is waiting at this point, it is a write lock.
                    waiting.pop(0)._release()

    @release_locked
    def _release_w(self, sublock):
        sublocks = self.sublocks
        if sublock in sublocks:
            thread_writers = self.thread_writers
            ident = get_ident()
            count = thread_writers[ident][1] - 1
            if count:
                thread_writers[ident] = (sublock, count)
            else:
                del thread_writers[ident]
                self.writing = False
                sublocks.remove(sublock)
                sublock._release()
                waiting = self.waiting
                # Release any waiting read locks.
                while waiting and isinstance(waiting[0], RLock):
                    waiting.pop(0)._release()


class SubLock(object):

    def __init__(self, rwlock):
        self.lock = threading.Lock()
        self.rwlock = rwlock

    def _release(self):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def __enter__(self):
        return self

    def __exit__(self, *exc_args):
        self.release()
        return False


class RLock(SubLock):

    def __init__(self, rwlock):
        SubLock.__init__(self, rwlock)
        self.becameWriter = None

    def release(self):
        if self.becameWriter is not None:
            self.becameWriter.release()
        else:
            self.rwlock._release_r(self)


class WLock(SubLock):

    def release(self):
        self.rwlock._release_w(self)
