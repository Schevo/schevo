"""Field metadata changing tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema

from schevo.field import not_expensive, not_fget, not_hidden


class BaseFieldMetadataChanged(CreatesSchema):

    body = '''
    class Foo(E.Entity):

        bar = f.string()

        class _Update(T.Update):

            def x_on_bar__changed(self):
                self.f.bar.readonly = True

            def _setup(self):
                self.f.bar.required = False
    '''

    def test_metadata_not_changed_initially(self):
        tx = db.Foo.t.create()
        assert tx.f.bar.metadata_changed == False
        tx.bar = 'baz'
        foo = db.execute(tx)
        tx = foo.t.update()
        assert tx.f.bar.required == False
        assert tx.f.bar.metadata_changed == False

    def test_metadata_changed_during_change_handler(self):
        tx = db.Foo.t.create(bar='baz')
        foo = db.execute(tx)
        tx = foo.t.update()
        assert tx.f.bar.metadata_changed == False
        tx.bar = 'frob'
        assert tx.f.bar.readonly == True
        assert tx.f.bar.metadata_changed == True
        tx.f.bar.reset_metadata_changed()
        assert tx.f.bar.metadata_changed == False


class TestFieldMetadataChanged1(BaseFieldMetadataChanged):

    include = True

    format = 1


class TestFieldMetadataChanged2(BaseFieldMetadataChanged):

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
