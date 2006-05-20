"""Multi-threading support for Schevo.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.database import dummy_lock
from schevo.mt import mrow


def install(db):
    """Install a database locker in `db` if one does not yet exist."""
    if db.read_lock is not dummy_lock:
        Plugin(db)


class Plugin(object):
    """A plugin giving a Schevo database a multiple-reader, one-writer
    locking mechanism.
    
    Usage::

      from schevo.database import open
      db = open(...)
      from schevomt import lockable
      lockable.install(db)
      lock = db.read_lock()         # Or .write_lock()
      try:
          # Do stuff here.
          pass
      finally:
          lock.release()
    """

    def __init__(self, db):
        self.db = db
        # Don't install if db already has an icon plugin.
        if hasattr(db, 'read_lock'):
            return
        # Create lock.
        rwlock = mrow.RWLock()
        db.read_lock = rwlock.reader
        db.write_lock = rwlock.writer
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
