"""Multi-threading support for Schevo.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.mt.dummy import dummy_lock
from schevo.mt import mrow


def install(db):
    """Install a database locker in `db` if one does not yet exist."""
    if db.read_lock is dummy_lock:
        Plugin(db)


class Plugin(object):
    """A plugin giving a Schevo database a multiple-reader, one-writer
    locking mechanism.

    Usage::

      import schevo.database
      db = schevo.database.open(...)
      import schevo.mt
      schevo.mt.install(db)
      lock = db.read_lock()         # Or .write_lock()
      try:
          # Do stuff here.
          pass
      finally:
          lock.release()
    """

    def __init__(self, db):
        self.db = db
        # Create lock.
        rwlock = mrow.RWLock()
        reader = rwlock.reader
        writer = rwlock.writer
        # Attach sublock constructors to database.
        db.read_lock = reader
        db.write_lock = writer
        # Create and attach decorator methods.
        def db_reader(fn):
            def inner(*args, **kw):
                lock = reader()
                try:
                    return fn(*args, **kw)
                finally:
                    lock.release()
            inner.__name__ = fn.__name__
            inner.__doc__ = fn.__doc__
            inner.__dict__.update(fn.__dict__)
            return inner
        def db_writer(fn):
            def inner(*args, **kw):
                lock = reader()
                try:
                    return fn(*args, **kw)
                finally:
                    lock.release()
            inner.__name__ = fn.__name__
            inner.__doc__ = fn.__doc__
            inner.__dict__.update(fn.__dict__)
            return inner
        db.db_reader = db_reader
        db.db_writer = db_writer
        # Override execute method.
        self._execute = db.execute

    def close(self):
        pass

    def execute(self, transaction):
        db = self.db
        lock = db.write_lock()
        try:
            return self._execute(transaction)
        finally:
            lock.release()


# Copyright (C) 2001-2009 ElevenCraft Inc.
#
# Schevo
# http://schevo.org/
#
# ElevenCraft Inc.
# Bellingham, WA
# http://11craft.com/
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
