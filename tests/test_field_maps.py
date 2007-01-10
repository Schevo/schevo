"""Field maps, field spec maps, and filtering them.

TODO:

- Test field map implementations for views, queries, and transactions,
  as they all have a slightly unique implementation of .sys.field_map

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema

from schevo.field import not_expensive, not_fget, not_hidden


class TestFieldMaps(CreatesSchema):

    body = '''

    class Foo(E.Entity):
        
        aaa = f.unicode()
        bbb = f.unicode(hidden=True)
        @f.unicode(hidden=True)
        def ccc(self):
            return 'abc'
        @f.unicode(expensive=True)
        def ddd(self):
            return 'def'
    '''

    def test_entity_sys_field_map(self):
        tx = db.Foo.t.create()
        tx.aaa = 'a'
        tx.bbb = 'b'
        entity = db.execute(tx)
        def fkeys(*filters):
            return tuple(entity.sys.field_map(*filters).keys())
        # No filters.
        expected = 'aaa', 'bbb', 'ccc', 'ddd',
        keys = fkeys()
        assert expected == keys
        # not_expensive
        expected = 'aaa', 'bbb', 'ccc',
        keys = fkeys(not_expensive)
        assert expected == keys
        # not_fget
        expected = 'aaa', 'bbb',
        keys = fkeys(not_fget)
        assert expected == keys
        # not_hidden
        expected = 'aaa', 'ddd',
        keys = fkeys(not_hidden)
        assert expected == keys
        # not_expensive, not_hidden
        expected = 'aaa',
        keys = fkeys(not_expensive, not_hidden)
        print keys
        assert expected == keys
        # not_fget, not_hidden
        expected = 'aaa',
        keys = fkeys(not_fget, not_hidden)
        assert expected == keys
        
    def test_extent_field_spec(self):
        extent = db.Foo
        def fkeys(*filters):
            return tuple(extent.field_spec(*filters).keys())
        # No filters.
        expected = 'aaa', 'bbb', 'ccc', 'ddd',
        keys = fkeys()
        assert expected == keys
        # not_expensive
        expected = 'aaa', 'bbb', 'ccc',
        keys = fkeys(not_expensive)
        assert expected == keys
        # not_fget
        expected = 'aaa', 'bbb',
        keys = fkeys(not_fget)
        assert expected == keys
        # not_hidden
        expected = 'aaa', 'ddd',
        keys = fkeys(not_hidden)
        assert expected == keys
        # not_expensive, not_hidden
        expected = 'aaa',
        keys = fkeys(not_expensive, not_hidden)
        print keys
        assert expected == keys
        # not_fget, not_hidden
        expected = 'aaa',
        keys = fkeys(not_fget, not_hidden)
        assert expected == keys
        


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
