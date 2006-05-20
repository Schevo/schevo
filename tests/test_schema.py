"""Schema definition unit tests.

For copyright, license, and warranty, see bottom of file.
"""

import unittest

from schevo.lib import module
import schevo.database
import schevo.schema
from schevo.test import BaseTest


# XXX: This schema may not be a candidate for schevo.test.schema as it
# does some very specific things to test schema loading magic.

SCHEMA = """
from schevo.schema import *
schevo.schema.prep(locals())


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

    name = f.customString()
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


class TestSchema(BaseTest):

    def setUp(self):
        # Forget existing modules.
        for m in module.MODULES:
            module.forget(m)
        # Import schema.
        schema_module = None
        schevo.schema.start()
        try:
            schema_module = self.schema_module = module.from_string(
                SCHEMA, 'TestSchema-schema')
            module.remember(schema_module)
        finally:
            self.schema_definition = schevo.schema.finish(None, schema_module)

    def tearDown(self):
        del self.schema_definition
        del self.schema_module

    def test_entity_dict(self):
        d = self.schema_definition
        m = self.schema_module
        E = d.E
        assert len(E) == 4
        assert E.Animal == m.Animal
        assert E.Person == m.Person
        assert E.Derived == m.Derived
        assert E._Base == m._Base
        
    def test_entity_entity(self):
        E = self.schema_definition.E
        assert 'Entity' not in E

    def test_entity_definition(self):
        d = self.schema_definition
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
        d = self.schema_definition
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
        d = self.schema_definition
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
        d = self.schema_definition
        tx = d.T.TxWithFields()
        assert 'foo' in tx._field_spec
        assert 'bar' in tx._field_spec
        assert 'foo' in tx.sys.fields()
        assert 'bar' in tx.sys.fields()
        assert type(tx.sys.fields()['foo']) is type(tx.f.foo)
        assert type(tx.sys.fields()['bar']) is type(tx.f.bar)

    def test_database_level_t_namespace(self):
        d = self.schema_definition
        assert hasattr(d.t, 'tx_with_fields')
        tx = d.t.tx_with_fields()
        assert isinstance(tx, d.T.TxWithFields)


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
