"""Field unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.constant import UNASSIGNED
from schevo.test import CreatesSchema


class BaseEntity(CreatesSchema):

    body = '''

    def default_bar():
        return db.Bar.findone(stuff=1) or UNASSIGNED

    class Foo(E.Entity):

        thing = f.string()

        _sample_unittest = [
            ('a', ),
            ('b', ),
            ('c', ),
            ]

    class Bar(E.Entity):

        stuff = f.integer()

        _key(stuff)

        _sample_unittest = [
            (1, ),
            (2, ),
            (3, ),
            ]

    class Baz(E.Entity):

        foo = f.entity('Foo')
        bar = f.entity('Bar', default=default_bar)
        foobar = f.entity('Foo', 'Bar', required=False)
    '''

    def test_allow(self):
        tx = db.Baz.t.create()
        assert tx.f.foo.allow == set(['Foo'])
        assert tx.f.bar.allow == set(['Bar'])
        assert tx.f.foobar.allow == set(['Foo', 'Bar'])

    def test_convert(self):
        tx = db.Baz.t.create()
        f = tx.f.foo
        assert f.convert('Foo-1', db) == db.Foo[1]
        assert f.convert(u'Foo-1', db) == db.Foo[1]

    def test_reversible_valid_values(self):
        tx = db.Baz.t.create()
        assert tx.f.foo.reversible_valid_values(db) == [
            ('Foo-1', db.Foo[1]),
            ('Foo-2', db.Foo[2]),
            ('Foo-3', db.Foo[3]),
            ]
        assert tx.f.bar.reversible_valid_values(db) == [
            ('Bar-1', db.Bar[1]),
            ('Bar-2', db.Bar[2]),
            ('Bar-3', db.Bar[3]),
            ]
        assert tx.f.foobar.reversible_valid_values(db) == [
            ('', UNASSIGNED),
            ('Bar-1', db.Bar[1]),
            ('Bar-2', db.Bar[2]),
            ('Bar-3', db.Bar[3]),
            ('Foo-1', db.Foo[1]),
            ('Foo-2', db.Foo[2]),
            ('Foo-3', db.Foo[3]),
            ]


class TestEntity1(BaseEntity):

    include = True

    format = 1


class TestEntity2(BaseEntity):

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
