"""Transaction unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema, raises
from schevo import error


class TestTransactionRequireChanges(CreatesSchema):

    body = '''

    class Alpha(E.Entity):

        foo = f.integer()

        class _Update(T.Update):

            _require_changes = False

    class Bravo(E.Entity):

        bar = f.integer()

    '''

    def test_require_changes(self):
        """Update transaction subclasses require a change to at least
        one field by default. A TransactionFieldsNotChanged error is
        raised if no changes were made to any fields."""
        b = db.execute(db.Bravo.t.create(bar=1))
        tx = b.t.update()
        # Error is raised when no fields are changed.
        assert raises(error.TransactionFieldsNotChanged, db.execute, tx)
        # No error is raised when changes are made.
        b = db.execute(b.t.update(bar=2))
        assert b.bar == 2
        
    def test_do_not_require_changes(self):
        """Update transaction subclasses that set _require_changes to
        False succeed if no changes have been made to any fields."""
        a = db.execute(db.Alpha.t.create(foo=1))
        a = db.execute(a.t.update())
        assert a.foo == 1


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
