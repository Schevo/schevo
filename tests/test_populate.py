"""Populate transaction tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema

from schevo.constant import UNASSIGNED


class TestPopulateSimple(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        bar = f.integer()
        baz = f.string()

        _sample_unittest = [
            (1, 'one'),
            (42, 'answer'),
            ]
    '''

    def test_populate_simple(self):
        assert len(db.Foo) == 2
        assert db.Foo[1].bar == 1
        assert db.Foo[1].baz == 'one'
        assert db.Foo[2].bar == 42
        assert db.Foo[2].baz == 'answer'

    def test_datalist_simple(self):
        assert db.Foo.as_datalist() == db.Foo._EntityClass._sample_unittest


class TestPopulateComplex(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        bar = f.integer()
        baz = f.string()

        _key(bar)

        _sample_unittest = [
            (1, 'one'),
            (42, 'answer'),
            ]


    class Bar(E.Entity):

        name = f.string()
        foo = f.entity('Foo')

        _key(name, foo)

        _sample_unittest = [
            ('a', (42,)),
            ('a', (1,)),
            ('b', (42,)),
            ]


    class Baz(E.Entity):

        name = f.string()
        bar = f.entity('Bar', required=False)

        _key(name)

        _sample_unittest = [
            ('this', ('a', (1,))),
            ('that', ('a', (42,))),
            ('them', ('b', (42,))),
            ('thee', UNASSIGNED),
            ]


    class Multi(E.Entity):

        name = f.string()
        bar = f.entity('Bar', 'Foo', required=False)

        _key(name)

        _sample_unittest = [
            ('this', ('Bar', ('a', (1,)))),
            ('that', ('Bar', ('a', (42,)))),
            ('them', ('Bar', ('b', (42,)))),
            ('thee', UNASSIGNED),
            ('thou', ('Foo', (1,))),
            ('thy', ('Foo', (42,))),
            ]
    '''

    def test_populate_complex(self):
        assert len(db.Bar) == 3
        assert db.Bar[1].name == 'a'
        assert db.Bar[1].foo.baz == 'answer'
        assert db.Bar[2].name == 'a'
        assert db.Bar[2].foo.baz == 'one'
        assert db.Bar[3].name == 'b'
        assert db.Bar[3].foo.baz == 'answer'

    def test_datalist_complex(self):
        assert db.Foo.as_datalist() == sorted(
            db.Foo._EntityClass._sample_unittest)
        assert db.Bar.as_datalist() == sorted(
            db.Bar._EntityClass._sample_unittest)
        assert db.Baz.as_datalist() == sorted(
            db.Baz._EntityClass._sample_unittest)
        assert db.Multi.as_datalist() == sorted(
            db.Multi._EntityClass._sample_unittest)


class TestPopulateHidden(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        bar = f.integer()
        baz = f.string(required=False)
        bof = f.float()

        class _Create(T.Create):

            def _setup(self):
                self.f.baz.hidden = True

        _sample_unittest = [
            (1, 2.3),
            (4, 5.6),
            ]
    '''

    def test_populate_ignoring_hidden_fields(self):
        # If a create transaction hides fields, the Populate
        # transaction should ignore those when parsing tuples.
        assert len(db.Foo) == 2
        assert db.Foo[1].bar == 1
        assert db.Foo[1].baz is UNASSIGNED
        assert db.Foo[1].bof == 2.3
        assert db.Foo[2].bar == 4
        assert db.Foo[2].baz is UNASSIGNED
        assert db.Foo[2].bof == 5.6


# Copyright (C) 2001-2006 Orbtech, L.L.C. and contributors.
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
