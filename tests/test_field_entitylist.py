"""Custom field with entity reference unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import BaseTest, CreatesSchema, raises


class BaseFieldEntityList(CreatesSchema):

    body = '''
        class Foo(E.Entity):

            name = f.unicode()

            _key(name)


        class Bar(E.Entity):

            foo_list = f.entity_list('Foo')


        class Bof(E.Entity):

            name = f.unicode()

            _key(name)
        '''

    def test_store_and_retrieve_empty_list(self):
        bar = ex(db.Bar.t.create(foo_list=[]))
        assert bar.foo_list == []
        self.reopen()
        assert bar.foo_list == []

    def test_store_and_retrieve_one_entity(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_list=[foo]))
        assert bar.foo_list == [foo]
        self.reopen()
        assert bar.foo_list == [foo]

    def test_store_and_retrieve_multiple_entities(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_list=[foo1, foo2]))
        assert bar.foo_list == [foo1, foo2]
        self.reopen()
        assert bar.foo_list == [foo1, foo2]

    def test_storing_wrong_type_fails(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bof = ex(db.Bof.t.create(name='bof'))
        tx = db.Bar.t.create(foo_list=[foo, bof])
        assert raises(TypeError, db.execute, tx)

    def test_links_are_maintained(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_list=[foo]))
        assert foo.m.bars() == [bar1]
        bar2 = ex(db.Bar.t.create(foo_list=[foo]))
        assert set(foo.m.bars()) == set([bar1, bar2])

    def test_only_one_link_is_maintained_when_duplicates_are_in_list(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_list=[foo, foo]))
        assert foo.m.bars() == [bar1]
        bar2 = ex(db.Bar.t.create(foo_list=[foo, foo]))
        assert set(foo.m.bars()) == set([bar1, bar2])


class TestFieldEntityList2(BaseFieldEntityList):

    format = 2


class TestFieldEntityList1(BaseTest):
    """This tests for failure, since EntityList is not allowed in format 1
    databases.

    Create a schema that contains an EntityList field::

        >>> body = '''
        ...     class Foo(E.Entity):
        ...
        ...         name = f.unicode()
        ...
        ...         _key(name)
        ...
        ...     class Bar(E.Entity):
        ...
        ...         foo_list = f.entity_list('Foo')
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
