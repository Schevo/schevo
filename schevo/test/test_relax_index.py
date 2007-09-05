"""relax_index/enforce_index unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema, raises


class BaseRelaxIndex(CreatesSchema):

    body = """

    class Foo(E.Entity):

        name = f.unicode()

        _key(name)

        @extentmethod
        def t_swap(extent):
            return E.Foo._Swap()

        @extentmethod
        def t_enforce(extent):
            return E.Foo._Enforce()

        class _Swap(T.Transaction):

            foo1 = f.entity('Foo')
            foo2 = f.entity('Foo')

            def _execute(self, db):
                db.Foo.relax_index('name')
                # The following sub-transaction tells the database to
                # enforce the same index, but it should not override
                # the above request to relax the index.
                db.execute(db.Foo.t.enforce())
                # Now perform some other steps as if the key is
                # relaxed.
                foo1, foo2 = self.foo1, self.foo2
                foo1_name = foo1.name
                foo2_name = foo2.name
                db.execute(foo1.t.update(name=foo2_name))
                db.execute(foo2.t.update(name=foo1_name))

        class _Enforce(T.Transaction):

            def _execute(self, db):
                db.Foo.enforce_index('name')

    """

    def test_swap(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        tx = db.Foo.t.swap()
        tx.foo1 = foo1
        tx.foo2 = foo2
        ex(tx)
        assert foo1.name == 'foo2'
        assert foo2.name == 'foo1'


class TestRelaxIndex1(BaseRelaxIndex):

    include = True

    format = 1


class TestRelaxIndex2(BaseRelaxIndex):

    include = True

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
