"""Transaction _before and _after unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises


class BaseTransactionBeforeAfter(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        name = f.string()

        _key(name)

        class _Create(T.Create):

            def _before_execute(self, db):
                self.x.bar = 5

            def _after_execute(self, db, foo):
                assert foo.name == self.name
                assert self.x.bar == 5

        class _Update(T.Update):

            def _before_execute(self, db, foo):
                self.x.bar = 42

            def _after_execute(self, db, foo):
                assert foo.name == self.name
                assert self.x.bar == 42

        class _Delete(T.Delete):

            def _before_execute(self, db, foo):
                self.x.bar = 12

            def _after_execute(self, db):
                assert self.x.bar == 12

    '''

    def test(self):
        tx = db.Foo.t.create(name='foo1')
        foo = ex(tx)
        assert tx.x.bar == 5
        tx = foo.t.update(name='foo2')
        ex(tx)
        assert tx.x.bar == 42
        tx = foo.t.delete()
        ex(tx)
        assert tx.x.bar == 12


# class TestTransactionBeforeAfter1(BaseTransactionBeforeAfter):

#     include = True

#     format = 1


class TestTransactionBeforeAfter2(BaseTransactionBeforeAfter):

    include = True

    format = 2
