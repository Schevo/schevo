"""EntitySetSet field unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import BaseTest, CreatesSchema, raises

from schevo.constant import UNASSIGNED
from schevo.error import KeyCollision


class BaseFieldEntitySetSet(CreatesSchema):

    body = '''
        class Foo(E.Entity):

            name = f.unicode()

            _key(name)


        class Bar(E.Entity):

            foo_set = f.entity_set_set('Foo', required=False)

            _key(foo_set)


        class Baz(E.Entity):

            foo_set = f.entity_set_set('Foo', min_size=1)


        class Bof(E.Entity):

            name = f.unicode()

            _key(name)
        '''

    def test_store_and_retrieve_UNASSIGNED(self):
        bar = ex(db.Bar.t.create(foo_set=UNASSIGNED))
        assert bar.foo_set is UNASSIGNED
        self.reopen()
        assert bar.foo_set is UNASSIGNED

    def test_store_and_retrieve_one_entity(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_set=set([frozenset([foo])])))
        assert bar.foo_set == set([frozenset([foo])])
        bar2 = ex(db.Bar.t.create(foo_set=UNASSIGNED))
        assert bar2.foo_set is UNASSIGNED
        self.reopen()
        assert bar.foo_set == set([frozenset([foo])])
        assert bar2.foo_set is UNASSIGNED

    def test_store_and_retrieve_multiple_entities(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        foo3 = ex(db.Foo.t.create(name='foo3'))
        bar = ex(db.Bar.t.create(foo_set=set([frozenset([foo1, foo2, foo1]),
                                              frozenset([foo3])])))
        assert bar.foo_set == set([frozenset([foo1, foo2]), frozenset([foo3])])
        self.reopen()
        assert bar.foo_set == set([frozenset([foo1, foo2]), frozenset([foo3])])

    def test_mutate_transaction_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_set=set([frozenset([foo1])])))
        assert bar.foo_set == set([frozenset([foo1])])
        tx = bar.t.update()
        tx.foo_set.add(frozenset([foo2]))
        db.execute(tx)
        assert bar.foo_set == set([frozenset([foo1]), frozenset([foo2])])

    def test_immutable_entity_view_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_set=set([frozenset([foo1])])))
        assert raises(AttributeError, getattr, bar.foo_set, 'add')
        v = bar.v.default()
        assert raises(AttributeError, getattr, v.foo_set, 'add')

    def test_storing_wrong_type_fails(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bof = ex(db.Bof.t.create(name='bof'))
        tx = db.Bar.t.create(foo_set=set([frozenset([foo, bof])]))
        assert raises(TypeError, db.execute, tx)

    def test_links_are_maintained(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_set=set([frozenset([foo])])))
        assert foo.m.bars() == [bar1]
        call = ex, db.Bar.t.create(foo_set=set([frozenset([foo])]))
        assert raises(KeyCollision, *call)

    def test_min_size_max_size(self):
        # Make sure that empty sets are allowed by default.
        foo = ex(db.Foo.t.create(name='foo'))
        tx = db.Bar.t.create(foo_set=set([]))
        bar = db.execute(tx)
        assert list(bar.foo_set) == []
        # Make sure they are not allowed when min_size > 0.
        tx = db.Baz.t.create(foo_set=set([]))
        call = ex, tx
        assert raises(ValueError, *call)


class TestFieldEntitySetSet2(BaseFieldEntitySetSet):

    format = 2


class TestFieldEntitySetSet1(BaseTest):
    """This tests for failure, since EntitySetSet is not allowed in
    format 1 databases.

    Create a schema that contains an EntitySetSet field::

        >>> body = '''
        ...     class Foo(E.Entity):
        ...
        ...         name = f.unicode()
        ...
        ...         _key(name)
        ...
        ...     class Bar(E.Entity):
        ...
        ...         foo_set = f.entity_set_set('Foo')
        ...
        ...     class Bof(E.Entity):
        ...
        ...         name = f.unicode()
        ...
        ...         _key(name)
        ...     '''

    Creating a format 2 database using the schema works fine::

        >>> from schevo.test import DocTest
        >>> t = DocTest(body, format=2)

    However, creating a format 1 database using the schema results in the
    database engine raising an UnsupportedFieldType error::

        >>> t = DocTest(body, format=1) #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        UnsupportedFieldType: ...

    """


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
