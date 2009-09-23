"""EntitySet field unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import BaseTest, CreatesSchema, raises

from schevo.constant import UNASSIGNED
from schevo.error import KeyCollision
from schevo.placeholder import Placeholder


class BaseFieldEntitySet(CreatesSchema):

    body = '''
        def default_foo_set():
            foo = db.Foo.findone(name='default foo')
            return set([foo])


        class Foo(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('default foo', ),
                ]


        class Bar(E.Entity):

            foo_set = f.entity_set('Foo', required=False)

            _key(foo_set)


        class Baz(E.Entity):

            foo_set = f.entity_set('Foo', min_size=1, default=default_foo_set)


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

            foo_foos = f.entity_set('FooFoo',
                                    default=set([('foofoo2', ), ('foofoo1', )]))


        class BarBar(E.Entity):

            name = f.string()
            foo_foos = f.entity_set('FooFoo')

            _key(name)

            _initial = [
                ('barbar1', set([('foofoo1',), ('foofoo2',)])),
                ('barbar2', set([('foofoo2',), ('foofoo1',)])),
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
            foo_foos_or_bar_bars = f.entity_set('FooFoo', 'BazBaz')

            _key(name)

            _initial = [
                ('bofbof1', set([('FooFoo', ('foofoo1',)),
                                 ('BazBaz', ('bazbaz2',)),
                                 ])),
                ('bofbof2', set([('FooFoo', ('foofoo2',)),
                                 ('BazBaz', ('bazbaz1',)),
                                 ])),
                ]
        '''

    def test_default(self):
        tx = db.BooBoo.t.create()
        assert tx.foo_foos == set([db.FooFoo.findone(name='foofoo2'),
                                   db.FooFoo.findone(name='foofoo1')])

    def test_store_and_retrieve_UNASSIGNED(self):
        bar = ex(db.Bar.t.create(foo_set=UNASSIGNED))
        assert bar.foo_set is UNASSIGNED
        self.reopen()
        assert bar.foo_set is UNASSIGNED

    def test_store_and_retrieve_one_entity(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_set=set([foo])))
        assert bar.foo_set == set([foo])
        self.reopen()
        assert bar.foo_set == set([foo])

    def test_store_and_retrieve_one_entity_plus_UNASSIGNED(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar = ex(db.Bar.t.create(foo_set=set([foo])))
        assert bar.foo_set == set([foo])
        bar2 = ex(db.Bar.t.create(foo_set=UNASSIGNED))
        assert bar2.foo_set is UNASSIGNED
        self.reopen()
        assert bar.foo_set == set([foo])
        assert bar2.foo_set is UNASSIGNED

    def test_store_and_retrieve_multiple_entities(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_set=set([foo1, foo2, foo1])))
        assert bar.foo_set == set([foo1, foo2])
        self.reopen()
        assert bar.foo_set == set([foo1, foo2])

    def test_mutate_transaction_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_set=set([foo1])))
        assert bar.foo_set == set([foo1])
        tx = bar.t.update()
        tx.foo_set.add(foo2)
        db.execute(tx)
        assert bar.foo_set == set([foo1, foo2])

    def test_immutable_entity_view_field_value(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        bar = ex(db.Bar.t.create(foo_set=set([foo1])))
        assert raises(AttributeError, getattr, bar.foo_set, 'add')
        v = bar.v.default()
        assert raises(AttributeError, getattr, v.foo_set, 'add')

    def test_storing_wrong_type_fails(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bof = ex(db.Bof.t.create(name='bof'))
        tx = db.Bar.t.create(foo_set=set([foo, bof]))
        assert raises(TypeError, db.execute, tx)

    def test_links_are_maintained(self):
        foo = ex(db.Foo.t.create(name='foo'))
        bar1 = ex(db.Bar.t.create(foo_set=set([foo])))
        assert foo.m.bars() == [bar1]
        try:
            ex(db.Bar.t.create(foo_set=set([foo])))
        except KeyCollision, e:
            assert e.extent_name == 'Bar'
            assert e.key_spec == ('foo_set',)
            assert e.field_values == (
                (Placeholder(foo), ),
                )

    def test_min_size_max_size(self):
        # Make sure that empty lists are allowed by default.
        foo = ex(db.Foo.t.create(name='foo'))
        tx = db.Bar.t.create(foo_set=set([]))
        bar = db.execute(tx)
        assert list(bar.foo_set) == []
        # Make sure they are not allowed when min_size > 0.
        tx = db.Baz.t.create(foo_set=set([]))
        call = ex, tx
        assert raises(ValueError, *call)

    def test_initial_values(self):
        barbar1 = db.BarBar.findone(name='barbar1')
        expected = set([
            db.FooFoo.findone(name='foofoo1'),
            db.FooFoo.findone(name='foofoo2'),
            ])
        assert barbar1.foo_foos == expected
        barbar2 = db.BarBar.findone(name='barbar2')
        expected = set([
            db.FooFoo.findone(name='foofoo2'),
            db.FooFoo.findone(name='foofoo1'),
            ])
        assert barbar2.foo_foos == expected
        bofbof1 = db.BofBof.findone(name='bofbof1')
        expected = set([
            db.FooFoo.findone(name='foofoo1'),
            db.BazBaz.findone(name='bazbaz2'),
            ])
        assert bofbof1.foo_foos_or_bar_bars == expected
        bofbof2 = db.BofBof.findone(name='bofbof2')
        expected = set([
            db.FooFoo.findone(name='foofoo2'),
            db.BazBaz.findone(name='bazbaz1'),
            ])
        assert bofbof2.foo_foos_or_bar_bars == expected


class TestFieldEntitySet2(BaseFieldEntitySet):

    include = True

    format = 2


# class TestFieldEntitySet1(BaseTest):
#     """This tests for failure, since EntitySet is not allowed in
#     format 1 databases.

#     Create a schema that contains an EntitySet field::

#         >>> body = '''
#         ...     class Foo(E.Entity):
#         ...
#         ...         name = f.string()
#         ...
#         ...         _key(name)
#         ...
#         ...     class Bar(E.Entity):
#         ...
#         ...         foo_set = f.entity_set('Foo')
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
