"""Tests for using tuples in valid_values"""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.error import EntityDoesNotExist
from schevo.test import CreatesSchema, raises


class BaseValidValuesResolve(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        name = f.string()

        _key(name)

        _initial = [
            ('foo 1',),
            ('foo 2',),
            ]


    class Bar(E.Entity):

        length = f.integer()

        _key(length)

        _initial = [
            dict(length=123),
            dict(length=456),
            ]


    class Baz(E.Entity):

        foo = f.entity('Foo', required=False,
                       valid_values=[('foo 2',)])
        bar = f.entity('Bar', required=False,
                       valid_values=[(123,)])
        foo_or_bar = f.entity('Foo', 'Bar', required=False,
                              valid_values=[('Foo', ('foo 1',)),
                                            ('Bar', (456,)),
                                            ])


    class Bad(E.Entity):

        bar = f.entity('Bar', required=False,
                       valid_values=[(789,)])
    '''

    def test_resolvable(self):
        foo_1 = db.Foo.findone(name='foo 1')
        foo_2 = db.Foo.findone(name='foo 2')
        bar_123 = db.Bar.findone(length=123)
        bar_456 = db.Bar.findone(length=456)
        # Check Create transaction.
        tx = db.Baz.t.create()
        assert set(tx.f.foo.valid_values) == set([foo_2])
        assert set(tx.f.bar.valid_values) == set([bar_123])
        assert set(tx.f.foo_or_bar.valid_values) == set([foo_1, bar_456])
        tx.foo = foo_1
        assert raises(ValueError, db.execute, tx)
        tx.bar = bar_456
        assert raises(ValueError, db.execute, tx)
        tx.foo_or_bar = foo_2
        assert raises(ValueError, db.execute, tx)
        tx.foo_or_bar = bar_123
        assert raises(ValueError, db.execute, tx)
        tx.foo = foo_2
        tx.bar = bar_123
        tx.foo_or_bar = foo_1
        baz = db.execute(tx)
        # Check update transaction.
        tx = baz.t.update()
        assert set(tx.f.foo.valid_values) == set([foo_2])
        assert set(tx.f.bar.valid_values) == set([bar_123])
        assert set(tx.f.foo_or_bar.valid_values) == set([foo_1, bar_456])
        tx.foo = foo_1
        assert raises(ValueError, db.execute, tx)
        tx.bar = bar_456
        assert raises(ValueError, db.execute, tx)
        tx.foo_or_bar = foo_2
        assert raises(ValueError, db.execute, tx)
        tx.foo_or_bar = bar_123
        assert raises(ValueError, db.execute, tx)
        tx.foo = foo_2
        tx.bar = bar_123
        tx.foo_or_bar = bar_456
        db.execute(tx)

    def test_unresolvable(self):
        # Unresolvable at first.
        assert raises(ValueError, db.Bad.t.create)
        # Make it resolvable.
        bar_789 = db.execute(db.Bar.t.create(length=789))
        bad = db.execute(db.Bad.t.create(bar=bar_789))


# class TestValidValuesResolve1(BaseValidValuesResolve):

#     include = True

#     format = 1


class TestValidValuesResolve2(BaseValidValuesResolve):

    include = True

    format = 2
