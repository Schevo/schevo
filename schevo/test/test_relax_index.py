"""relax_index/enforce_index unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises


class BaseRelaxIndex(CreatesSchema):

    body = """

    class Foo(E.Entity):

        name = f.string()

        _key(name)

        @extentmethod
        def t_swap(extent):
            return E.Foo._Swap()

        @extentmethod
        def t_enforce(extent):
            return E.Foo._Enforce()

        class _Swap(T.Transaction):

            foo1 = f.entity('Foo')
            foo2 = f.entity('Foo')

            def _execute(self, db):
                db.Foo.relax_index('name')
                # The following sub-transaction tells the database to
                # enforce the same index, but it should not override
                # the above request to relax the index.
                db.execute(db.Foo.t.enforce())
                # Now perform some other steps as if the key is
                # relaxed.
                foo1, foo2 = self.foo1, self.foo2
                foo1_name = foo1.name
                foo2_name = foo2.name
                db.execute(foo1.t.update(name=foo2_name))
                db.execute(foo2.t.update(name=foo1_name))

        class _Enforce(T.Transaction):

            def _execute(self, db):
                db.Foo.enforce_index('name')

    """

    def test_swap(self):
        foo1 = ex(db.Foo.t.create(name='foo1'))
        foo2 = ex(db.Foo.t.create(name='foo2'))
        tx = db.Foo.t.swap()
        tx.foo1 = foo1
        tx.foo2 = foo2
        ex(tx)
        assert foo1.name == 'foo2'
        assert foo2.name == 'foo1'


# class TestRelaxIndex1(BaseRelaxIndex):

#     include = True

#     format = 1


class TestRelaxIndex2(BaseRelaxIndex):

    include = True

    format = 2
