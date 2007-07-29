"""Transaction create/delete/update subclass unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema

class BaseTransactionCDUSubclass(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        name = f.unicode()

        _key(name)

        @extentmethod
        def t_custom_create(extent, **kw):
            return E.Foo._CustomCreate(**kw)

        def t_custom_delete(self):
            return self._CustomDelete(self)

        def t_custom_update(self, **kw):
            return self._CustomUpdate(self, **kw)

        class _CustomCreate(T.Create):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db):
                self.x.before = True

            def _after_execute(self, db, foo):
                self.x.after = True

        class _CustomDelete(T.Delete):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db, foo):
                self.x.before = True

            def _after_execute(self, db):
                self.x.after = True

        class _CustomUpdate(T.Update):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db, foo):
                self.x.before = True

            def _after_execute(self, db, foo):
                self.x.after = True
    '''

    def test(self):
        tx = db.Foo.t.custom_create()
        assert tx.x.before == False
        assert tx.x.after == False
        tx.name = 'hi'
        foo = db.execute(tx)
        assert foo.name == 'hi'
        assert tx.x.before == True
        assert tx.x.after == True
        tx = foo.t.custom_update()
        assert tx.x.before == False
        assert tx.x.after == False
        tx.name = 'ha'
        db.execute(tx)
        assert foo.name == 'ha'
        assert tx.x.before == True
        assert tx.x.after == True
        tx = foo.t.custom_delete()
        assert tx.x.before == False
        assert tx.x.after == False
        db.execute(tx)
        assert foo not in db.Foo
        assert tx.x.before == True
        assert tx.x.after == True


class TestTransactionCDUSubclass1(BaseTransactionCDUSubclass):

    format = 1


class TestTransactionCDUSubclass2(BaseTransactionCDUSubclass):

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
