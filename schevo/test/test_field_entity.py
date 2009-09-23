"""Field unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.constant import UNASSIGNED
from schevo.test import CreatesSchema


class BaseEntity(CreatesSchema):

    body = '''

    def default_bar():
        return db.Bar.findone(stuff=1) or UNASSIGNED

    class Foo(E.Entity):

        thing = f.string()

        _key(thing)

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

        foo = f.entity('Foo', default=('a', ))
        bar = f.entity('Bar', default=default_bar)
        foobar = f.entity('Foo', 'Bar', required=False)

        @f.entity('Foo')
        def foo2(self):
            return self.foo
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

    def test_default(self):
        tx = db.Baz.t.create()
        assert tx.foo == db.Foo.findone(thing='a')
        assert tx.bar == db.Bar.findone(stuff=1)

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

    def test_fget_not_treated_as_entity_storing_field_in_engine(self):
        """Database engine should not treat calculated fields as
        entity-storing fields."""
        extent_map = db._extent_map('Baz')
        field_name_id = extent_map['field_name_id']
        foo_id = field_name_id['foo']
        bar_id = field_name_id['bar']
        foobar_id = field_name_id['foobar']
        foo2_id = field_name_id['foo2']
        entity_field_ids = extent_map['entity_field_ids']
        # Entity fields -should- be in entity_field_ids.
        assert foo_id in entity_field_ids
        assert bar_id in entity_field_ids
        assert foobar_id in entity_field_ids
        # Calculated entity fields -should not- be in entity_field_ids.
        assert foo2_id not in entity_field_ids


# class TestEntity1(BaseEntity):

#     include = True

#     format = 1


class TestEntity2(BaseEntity):

    include = True

    format = 2
