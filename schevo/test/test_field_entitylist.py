"""EntityList field unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import BaseTest, CreatesSchema, raises

from schevo.constant import UNASSIGNED
from schevo.error import KeyCollision
from schevo.placeholder import Placeholder


class BaseFieldEntityList(CreatesSchema):

    body = '''

        def default_foo_list():
            foo = db.Foo.findone(name='default foo')
            return [foo]


        class Foo(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('default foo', ),
                ]


        class Bar(E.Entity):

            foo_list = f.entity_list('Foo', required=False)

            _key(foo_list)


        class Baz(E.Entity):

            foo_list = f.entity_list('Foo', min_size=1)

            _key(foo_list)


        class Bee(E.Entity):

            foo_list = f.entity_list('Foo', allow_duplicates=False,
                                     default=default_foo_list)

            _key(foo_list)


        class Boo(E.Entity):

            foo_list = f.entity_list('Foo', allow_unassigned=True)

            _key(foo_list)


        class Bof(E.Entity):

            name = f.string()

            _key(name)


        class FooFoo(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('foofoo1', ),
                ('foofoo2', ),
                ]

            _initial_priority = 1


        class BooBoo(E.Entity):

            foo_foos = f.entity_list('FooFoo',
                                     default=[('foofoo2', ), ('foofoo1', )])


        class BarBar(E.Entity):

            name = f.string()
            foo_foos = f.entity_list('FooFoo')

            _key(name)

            _initial = [
                ('barbar1', [('foofoo1',), ('foofoo2',)]),
                ('barbar2', [('foofoo2',), ('foofoo1',)]),
                ]


        class BazBaz(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('bazbaz1', ),
                ('bazbaz2', ),
                ]

            _initial_priority = 1


        class BofBof(E.Entity):

            name = f.string()
            foo_foos_or_bar_bars = f.entity_list('FooFoo', 'BazBaz')

            _key(name)

            _initial = [
                ('bofbof1', [('FooFoo', ('foofoo1',)),
                             ('BazBaz', ('bazbaz2',)),
                             ]),
                ('bofbof2', [('FooFoo', ('foofoo2',)),
                             ('BazBaz', ('bazbaz1',)),
                             ]),
                ]
        '''

    def test_default(self):
        tx = db.BooBoo.t.create()
        assert tx.foo_foos == [db.FooFoo.findone(name='foofoo2'),
                               db.FooFoo.findone(name='foofoo1')]

    def test_store_and_retrieve_UNASSIGNED(self):
        bar = ex(db.Bar.t.create(foo_list=UNASSIGNED))
        assert bar.foo_list is UNASSIGNED
        self.reopen()
        assert bar.foo_list is UNASSIGNED

    def test_store_and_retrieve_one_entity(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_list=[foo]))
        assert list(bar.foo_list) == [foo]
        self.reopen()
        assert list(bar.foo_list) == [foo]

    def test_store_and_retrieve_multiple_entities(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_list=[foo1, foo2]))
        assert list(bar.foo_list) == [foo1, foo2]
        self.reopen()
        assert list(bar.foo_list) == [foo1, foo2]

    def test_mutate_transaction_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_list=[foo1]))
        assert list(bar.foo_list) == [foo1]
        tx = bar.t.update()
        tx.foo_list.append(foo2)
        db.execute(tx)
        assert list(bar.foo_list) == [foo1, foo2]

    def test_immutable_entity_view_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_list=[foo1]))
        assert raises(AttributeError, getattr, bar.foo_list, 'append')
        v = bar.v.default()
        assert raises(AttributeError, getattr, v.foo_list, 'append')

    def test_storing_wrong_type_fails(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bof = ex(db.Bof.t.create(name='bof'))
        tx = db.Bar.t.create(foo_list=[foo, bof])
        assert raises(TypeError, db.execute, tx)

    def test_links_are_maintained(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_list=[foo]))
        assert foo.m.bars() == [bar1]
        try:
            ex(db.Bar.t.create(foo_list=[foo]))
        except KeyCollision, e:
            assert e.extent_name == 'Bar'
            assert e.key_spec == ('foo_list',)
            assert e.field_values == (
                [Placeholder(foo)],
                )

    def test_only_one_link_is_maintained_when_duplicates_are_in_list(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_list=[foo, foo]))
        assert foo.m.bars() == [bar1]
        bar2 = ex(db.Bar.t.create(foo_list=[foo, foo, foo]))
        assert set(foo.m.bars()) == set([bar1, bar2])

    def test_min_size_max_size(self):
        # Make sure that empty lists are allowed by default.
        foo = ex(db.Foo.t.create(name='foo'))
        tx = db.Bar.t.create(foo_list=[])
        bar = db.execute(tx)
        assert list(bar.foo_list) == []
        # Make sure they are not allowed when min_size > 0.
        tx = db.Baz.t.create(foo_list=[])
        call = ex, tx
        assert raises(ValueError, *call)

    def test_disallow_duplicates(self):
        # Make sure that duplicates are allowed by default.
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_list=[foo, foo]))
        assert list(bar.foo_list) == [foo, foo]
        # Make sure they are disallowed when allow_duplicates is False.
        tx = db.Bee.t.create(foo_list=[foo, foo])
        call = ex, tx
        assert raises(ValueError, *call)

    def test_allow_unassigned(self):
        # Make sure that UNASSIGNED members are disallowed by default.
        foo = ex(db.Foo.t.create(name='foo'))
        tx = db.Bar.t.create(foo_list=[foo, UNASSIGNED])
        call = ex, tx
        assert raises(ValueError, *call)
        # Make sure they are allowed when allow_unassigned is True.
        tx = db.Boo.t.create(foo_list=[foo, UNASSIGNED])
        boo = db.execute(tx)
        assert list(boo.foo_list) == [foo, UNASSIGNED]

    def test_initial_values(self):
        barbar1 = db.BarBar.findone(name='barbar1')
        expected = [
            db.FooFoo.findone(name='foofoo1'),
            db.FooFoo.findone(name='foofoo2'),
            ]
        assert list(barbar1.foo_foos) == expected
        barbar2 = db.BarBar.findone(name='barbar2')
        expected = [
            db.FooFoo.findone(name='foofoo2'),
            db.FooFoo.findone(name='foofoo1'),
            ]
        assert list(barbar2.foo_foos) == expected
        bofbof1 = db.BofBof.findone(name='bofbof1')
        expected = [
            db.FooFoo.findone(name='foofoo1'),
            db.BazBaz.findone(name='bazbaz2'),
            ]
        assert list(bofbof1.foo_foos_or_bar_bars) == expected
        bofbof2 = db.BofBof.findone(name='bofbof2')
        expected = [
            db.FooFoo.findone(name='foofoo2'),
            db.BazBaz.findone(name='bazbaz1'),
            ]
        assert list(bofbof2.foo_foos_or_bar_bars) == expected


class TestFieldEntityList2(BaseFieldEntityList):

    include = True

    format = 2


# class TestFieldEntityList1(BaseTest):
#     """This tests for failure, since EntityList is not allowed in format 1
#     databases.

#     Create a schema that contains an EntityList field::

#         >>> body = '''
#         ...     class Foo(E.Entity):
#         ...
#         ...         name = f.string()
#         ...
#         ...         _key(name)
#         ...
#         ...     class Bar(E.Entity):
#         ...
#         ...         foo_list = f.entity_list('Foo')
#         ...
#         ...     class Bof(E.Entity):
#         ...
#         ...         name = f.string()
#         ...
#         ...         _key(name)
#         ...     '''

#     Creating a format 2 database using the schema works fine::

#         >>> from schevo.test import DocTest
#         >>> t = DocTest(body, format=2)

#     However, creating a format 1 database using the schema results in the
#     database engine raising an UnsupportedFieldType error::

#         >>> t = DocTest(body, format=1) #doctest: +ELLIPSIS
#         Traceback (most recent call last):
#           ...
#         UnsupportedFieldType: ...

#     """
