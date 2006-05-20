"""Transaction field reordering tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema


class TestTransaction(CreatesSchema):

    body = '''

    class Something(E.Entity):

        field1 = f.string()
        field2 = f.integer()

        class _Create(T.Create):

            field3 = f.memo()
            field2 = f.integer()
    '''

    def test_reorder_by_reassignment(self):
        # The Create transaction for a Something entity first should
        # have ``field1``, since that is implied by
        # create/delete/update. Then, ``field3`` should be next,
        # because ``field2`` was recreated afterwards, thus overriding
        # the original position of ``field2``.
        tx = db.Something.t.create()
        assert list(tx.f) == ['field1', 'field3', 'field2']


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
