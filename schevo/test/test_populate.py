"""Populate transaction tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema

from schevo.constant import UNASSIGNED


class BasePopulateSimple(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        bar = f.integer()
        baz = f.string()

        _sample_unittest = [
            (1, 'one'),
            (42, 'answer'),
            ]

    class FooDict(E.Entity):

        bar = f.integer(default=42)
        baz = f.string()

        _sample_unittest = [
            dict(bar=1,
                 baz='one',
                 ),
            dict(    # Leave out 'bar' to test that it will use default.
                 baz='answer',
                 ),
            ]
    '''

    def test_populate_simple(self):
        assert len(db.Foo) == 2
        # Populated with tuples.
        assert db.Foo[1].bar == 1
        assert db.Foo[1].baz == 'one'
        assert db.Foo[2].bar == 42
        assert db.Foo[2].baz == 'answer'
        # Populated with dicts.
        assert db.FooDict[1].bar == 1
        assert db.FooDict[1].baz == 'one'
        assert db.FooDict[2].bar == 42
        assert db.FooDict[2].baz == 'answer'

    def test_datalist_simple(self):
        assert db.Foo.as_datalist() == db.Foo.EntityClass._sample_unittest


class BasePopulateComplex(CreatesSchema):

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


    class BarDict(E.Entity):

        name = f.string()
        foo = f.entity('Foo')

        _key(name, foo)

        _sample_unittest = [
            dict(name='a',
                 foo=dict(bar=42),
                 ),
            dict(name='a',
                 foo=dict(bar=1),
                 ),
            dict(name='b',
                 foo=dict(bar=42),
                 ),
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


    class BazDict(E.Entity):

        name = f.string()
        bar = f.entity('Bar', required=False)

        _key(name)

        _sample_unittest = [
            dict(name='this',
                 bar=dict(name='a', foo=dict(bar=1)),
                 ),
            dict(name='that',
                 bar=dict(name='a', foo=dict(bar=42)),
                 ),
            dict(name='them',
                 bar=dict(name='b', foo=dict(bar=42)),
                 ),
            dict(name='thee',
                 ),
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


    class MultiDict(E.Entity):

        name = f.string()
        bar = f.entity('Bar', 'Foo', required=False)

        _key(name)

        _sample_unittest = [
            dict(name='this',
                 bar=('Bar', dict(name='a', foo=dict(bar=1))),
                 ),
            dict(name='that',
                 bar=('Bar', dict(name='a', foo=dict(bar=42))),
                 ),
            dict(name='them',
                 bar=('Bar', dict(name='b', foo=dict(bar=42))),
                 ),
            dict(name='thee',
                 ),
            dict(name='thou',
                 bar=('Foo', dict(bar=1)),
                 ),
            dict(name='thy',
                 bar=('Foo', dict(bar=42)),
                 ),
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
            db.Foo.EntityClass._sample_unittest)
        assert db.Bar.as_datalist() == sorted(
            db.Bar.EntityClass._sample_unittest)
        assert db.Baz.as_datalist() == sorted(
            db.Baz.EntityClass._sample_unittest)
        assert db.Multi.as_datalist() == sorted(
            db.Multi.EntityClass._sample_unittest)
        # Test dictionary versions.
        assert db.BarDict.as_datalist() == sorted(
            db.Bar.EntityClass._sample_unittest)
        assert db.BazDict.as_datalist() == sorted(
            db.Baz.EntityClass._sample_unittest)
        assert db.MultiDict.as_datalist() == sorted(
            db.Multi.EntityClass._sample_unittest)


class BasePopulateHidden(CreatesSchema):

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


# class TestPopulateSimple1(BasePopulateSimple):

#     include = True

#     format = 1


class TestPopulateSimple2(BasePopulateSimple):

    include = True

    format = 2


# class TestPopulateComplex1(BasePopulateComplex):

#     include = True

#     format = 1


class TestPopulateComplex2(BasePopulateComplex):

    include = True

    format = 2


# class TestPopulateHidden1(BasePopulateHidden):

#     include = True

#     format = 1


class TestPopulateHidden2(BasePopulateHidden):

    include = True

    format = 2
