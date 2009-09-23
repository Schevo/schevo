"""Schema definition unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import unittest

from schevo.lib import module
import schevo.database
from schevo.error import KeyIndexOverlap
import schevo.schema
from schevo.test import CreatesSchema, DocTest, raises


BODY = """

class CustomString(F.String):
    pass


# Just to prove we can define an entity class named Entity, but
# nothing happens with it because it is a reserved class name.
class Entity(E.Entity):

    name = f.string()


class _Base(E.Entity):

    name = f.string()


class Derived(E._Base):

    age = f.integer()


class Person(E.Entity):

    first_name = f.string()
    last_name = f.string()
    maiden_name = f.string(required=False)
    alias = f.string()
    favorite = f.entity(allow='Animal')

    _key(last_name, first_name)
    _key(alias)


# Declare this out of order to test sorting.
class Animal(E.Entity):

    name = f.custom_string()
    wild = f.boolean()


# Just to prove we can also create a Transaction class named Entity.
class Entity(T.Transaction):

    foobar = f.string()

    def _execute(self, db):
        pass


class TxWithFields(T.Transaction):

    foo = f.string()
    bar = f.string()

    def _execute(self, db):
        pass


def t_tx_with_fields():
    return T.TxWithFields()
"""


class BaseSchema(CreatesSchema):

    body = BODY

    def test_entity_dict(self):
        E = db.schema.E
        assert len(E) == 4

    def test_entity_entity(self):
        E = db.schema.E
        assert 'Entity' not in E

    def test_entity_definition(self):
        d = db.schema
        Person = d.E.Person
        assert Person._field_spec.keys() == [
            'first_name',
            'last_name',
            'maiden_name',
            'alias',
            'favorite',
            ]
        first_name = Person._field_spec['first_name']
        assert issubclass(first_name, d.F.String)
        assert first_name.label == 'First Name'
        assert first_name.required
        last_name = Person._field_spec['last_name']
        assert issubclass(last_name, d.F.String)
        assert last_name.label == 'Last Name'
        assert last_name.required
        maiden_name = Person._field_spec['maiden_name']
        assert issubclass(maiden_name, d.F.String)
        assert maiden_name.label == 'Maiden Name'
        assert not maiden_name.required
        alias = Person._field_spec['alias']
        assert issubclass(alias, d.F.String)
        assert alias.label == 'Alias'
        assert alias.required
        favorite = Person._field_spec['favorite']
        assert issubclass(favorite, d.F.Entity)
        assert favorite.label == 'Favorite'
        assert tuple(favorite.allow) == ('Animal', )
        assert favorite.required
        assert ('alias', ) in Person._key_spec
        assert ('last_name', 'first_name') in Person._key_spec
        assert len(Person._key_spec) == 2
        assert d.E.Animal._relationships == [('Person', 'favorite')]

    def test_subclassing(self):
        d = db.schema
        _Base = d.E._Base
        assert _Base._field_spec.keys() == [
            'name',
            ]
        Derived = d.E.Derived
        assert Derived._field_spec.keys() == [
            'name',
            'age',
            ]

    def test_field_definition(self):
        d = db.schema
        Animal = d.E['Animal']
        assert Animal._field_spec.keys() == ['name', 'wild']
        name = Animal._field_spec['name']
        assert issubclass(name, d.F.CustomString)
        assert name.label == 'Name'
        assert name.required
        wild = Animal._field_spec['wild']
        assert issubclass(wild, d.F.Boolean)
        assert wild.label == 'Wild'
        assert wild.required
        assert Animal._key_spec == ()

    def test_tx_with_fields(self):
        d = db.schema
        tx = d.T.TxWithFields()
        assert 'foo' in tx._field_spec
        assert 'bar' in tx._field_spec
        assert 'foo' in tx.s.field_map()
        assert 'bar' in tx.s.field_map()
        assert type(tx.s.field_map()['foo']) is type(tx.f.foo)
        assert type(tx.s.field_map()['bar']) is type(tx.f.bar)

    def test_database_level_t_namespace(self):
        d = db.schema
        assert hasattr(d.t, 'tx_with_fields')
        tx = d.t.tx_with_fields()
        assert isinstance(tx, d.T.TxWithFields)

    def test_duplicate_key_and_index_declaration_is_a_schema_error(self):
        body = '''
            class Foo(E.Entity):
                bar = f.integer()
                _key(bar)
                _index(bar)
            '''
        try:
            DocTest(body)
        except KeyIndexOverlap, e:
            assert e.class_name == 'Foo'
            assert sorted(e.overlapping_specs) == [('bar',)]
        # Also make sure it works when subclassing.
        body = '''
            class Foo(E.Entity):
                bar = f.integer()
                _key(bar)

            class Foo(E.Foo):
                _index('bar')
            '''
        try:
            DocTest(body)
        except KeyIndexOverlap, e:
            assert e.class_name == 'Foo'
            assert sorted(e.overlapping_specs) == [('bar',)]
        body = '''
            class Foo(E.Entity):
                bar = f.integer()
                _index(bar)

            class Foo(E.Foo):
                _key('bar')
            '''
        try:
            DocTest(body)
        except KeyIndexOverlap, e:
            assert e.class_name == 'Foo'
            assert sorted(e.overlapping_specs) == [('bar',)]


# class TestSchema1(BaseSchema):

#     include = True

#     format = 1


class TestSchema2(BaseSchema):

    include = True

    format = 2
