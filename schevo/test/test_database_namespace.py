"""Database namespace unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema


class BaseDatabaseNamespaces(CreatesSchema):

    body = '''

    class Foo(E.Entity):
        bar = f.string()

    def t_create_foo():
        return CreateFoo()

    class CreateFoo(T.Transaction):
        def _execute(self, db):
            return db.execute(db.Foo.t.create(bar='baz'))
    '''

    def test_database_t_namespace(self):
        tx = db.t.create_foo()
        foo = db.execute(tx)
        assert foo.bar == 'baz'


# class TestDatabaseNamespaces1(BaseDatabaseNamespaces):

#     include = True

#     format = 1


class TestDatabaseNamespaces2(BaseDatabaseNamespaces):

    include = True

    format = 2
