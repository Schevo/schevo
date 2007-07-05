"""Transaction _before and _after unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema, raises


class BaseTransaction(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        name = f.unicode()

        _key(name)

        class _Create(T.Create):

            def _before_execute(self, db):
                self.x.bar = 5

            def _after_execute(self, db, foo):
                assert foo.name == self.name
                assert self.x.bar == 5

        class _Update(T.Update):

            def _before_execute(self, db, foo):
                self.x.bar = 42

            def _after_execute(self, db, foo):
                assert foo.name == self.name
                assert self.x.bar == 42

        class _Delete(T.Delete):

            def _before_execute(self, db, foo):
                self.x.bar = 12

            def _after_execute(self, db):
                assert self.x.bar == 12
    
    '''

    def test(self):
        tx = db.Foo.t.create(name='foo1')
        foo = ex(tx)
        assert tx.x.bar == 5
        tx = foo.t.update(name='foo2')
        ex(tx)
        assert tx.x.bar == 42
        tx = foo.t.delete()
        ex(tx)
        assert tx.x.bar == 12


class TestTransaction1(BaseTransaction):

    format = 1


class TestTransaction2(BaseTransaction):

    format = 2


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
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
