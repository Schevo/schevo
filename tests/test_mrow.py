"""Test for MROW locking.

Commented out for now since it fails occasionally and causes unit test
harness to hang.  Needs some love :)

For copyright, license, and warranty, see bottom of file.
"""

## import threading
## import time

## from schevo.mt import mrow


## def writer(L, value, after, rwlock, times):
##     """Append value to L after a period of time."""
##     try:
##         lock = rwlock.writer()
##         # Get another lock, to test the fact that obtaining multiple
##         # write locks from the same thread context doesn't block (lock
##         # reentrancy).
##         lock2 = rwlock.writer()
##         # Get a reader lock too; should be the same as getting another
##         # writer since writers are inherently readers as well.
##         lock3 = rwlock.reader()
##         times.append(time.time())
##         time.sleep(after)
##         L.append(value)
##     finally:
##         times.append(time.time())
##         lock3.release()
##         lock2.release()
##         lock.release()


## def reader(L1, L2, after, rwlock, times):
##     """Append values from L1 to L2 after a period of time."""
##     try:
##         lock = rwlock.reader()
##         # Get another lock, to test the fact that obtaining multiple
##         # write locks from the same thread context doesn't block (lock
##         # reentrancy).
##         lock2 = rwlock.reader()
##         times.append(time.time())
##         time.sleep(after)
##         L2.extend(L1)
##     finally:
##         times.append(time.time())
##         lock2.release()
##         lock.release()


## def readerTurnedWriter(L, value, after, rwlock, times):
##     """Append value to L after a period of time."""
##     try:
##         lock = rwlock.reader()
##         lock2 = rwlock.writer()
##         times.append(time.time())
##         time.sleep(after)
##         L.append(value)
##     finally:
##         times.append(time.time())
##         lock2.release()
##         lock.release()


## def test_reentrancy():
##     lock = mrow.RWLock()
##     # Reentrant read locks.
##     rlock1 = lock.reader()
##     rlock2 = lock.reader()
##     rlock2.release()
##     rlock1.release()
##     # Reentrant write locks.
##     wlock1 = lock.writer()
##     wlock2 = lock.writer()
##     wlock2.release()
##     wlock1.release()
##     # Writers are also readers.
##     wlock = lock.writer()
##     rlock = lock.reader()
##     rlock.release()
##     wlock.release()


## def test_writeReadRead():
##     lock = mrow.RWLock()
##     W, R1, R2 = [], [], []
##     TW, TR1, TR2 = [], [], []
##     thread1 = threading.Thread(
##         target=writer,
##         args=(W, 'foo', 0.2, lock, TW),
##         )
##     thread2 = threading.Thread(
##         target=reader,
##         args=(W, R1, 0.2, lock, TR1),
##         )
##     thread3 = threading.Thread(
##         target=reader,
##         args=(W, R2, 0.2, lock, TR2),
##         )
##     thread1.start()
##     time.sleep(0.1)
##     thread2.start()
##     thread3.start()
##     time.sleep(0.8)
##     assert 'foo' in R1
##     assert 'foo' in R2
##     assert TR1[0] <= TR2[1]             # Read 1 started during read 2.
##     assert TR2[0] <= TR1[1]             # Read 2 started during read 1.
##     assert TR1[0] >= TW[1]              # Read 1 started after write.
##     assert TR2[0] >= TW[1]              # Read 2 started after write.


## def test_writeReadReadWrite():
##     lock = mrow.RWLock()
##     W, R1, R2 = [], [], []
##     TW1, TR1, TR2, TW2 = [], [], [], []
##     thread1 = threading.Thread(
##         target=writer,
##         args=(W, 'foo', 0.5, lock, TW1),
##         )
##     thread2 = threading.Thread(
##         target=reader,
##         args=(W, R1, 0.5, lock, TR1),
##         )
##     thread3 = threading.Thread(
##         target=reader,
##         args=(W, R2, 0.5, lock, TR2),
##         )
##     thread4 = threading.Thread(
##         target=writer,
##         args=(W, 'bar', 0.5, lock, TW2),
##         )
##     thread1.start()
##     time.sleep(0.2)
##     thread2.start()
##     time.sleep(0.2)
##     thread3.start()
##     time.sleep(0.2)
##     thread4.start()
##     time.sleep(1.7)
##     assert 'foo' in R1
##     assert 'foo' in R2
##     assert 'bar' not in R1
##     assert 'bar' not in R2
##     assert 'bar' in W
##     assert TR1[0] <= TR2[1]              # Read 1 started during read 2.
##     assert TR2[0] <= TR1[1]              # Read 2 started during read 1.
##     assert TR1[0] >= TW1[1]              # Read 1 started after write 1.
##     assert TR2[0] >= TW1[1]              # Read 2 started after write 1.
##     assert TW2[0] >= TR1[1]              # Write 2 started after read 1.
##     assert TW2[0] >= TR2[1]              # Write 2 started after read 2.


## def test_writeReadReadtowrite():
##     lock = mrow.RWLock()
##     W, R1 = [], []
##     TW1, TR1, TW2 = [], [], []
##     thread1 = threading.Thread(
##         target=writer,
##         args=(W, 'foo', 0.5, lock, TW1),
##         )
##     thread2 = threading.Thread(
##         target=reader,
##         args=(W, R1, 0.5, lock, TR1),
##         )
##     thread3 = threading.Thread(
##         target=readerTurnedWriter,
##         args=(W, 'bar', 0.5, lock, TW2),
##         )
##     thread1.start()
##     time.sleep(0.2)
##     thread2.start()
##     time.sleep(0.2)
##     thread3.start()
##     time.sleep(1.7)
##     assert 'foo' in R1
##     assert 'bar' not in R1
##     assert 'bar' in W
##     assert TR1[0] >= TW1[1]              # Read 1 started after write 1.
##     assert TW2[0] >= TR1[1]              # Write 2 started after read 1.
    

# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
