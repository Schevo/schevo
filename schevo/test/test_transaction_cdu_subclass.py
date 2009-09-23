"""Transaction create/delete/update subclass unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema

class BaseTransactionCDUSubclass(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        name = f.string()

        _key(name)

        @extentmethod
        def t_custom_create(extent, **kw):
            return E.Foo._CustomCreate(**kw)

        def t_custom_delete(self):
            return self._CustomDelete(self)

        def t_custom_update(self, **kw):
            return self._CustomUpdate(self, **kw)

        class _CustomCreate(T.Create):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db):
                self.x.before = True

            def _after_execute(self, db, foo):
                self.x.after = True

        class _CustomDelete(T.Delete):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db, foo):
                self.x.before = True

            def _after_execute(self, db):
                self.x.after = True

        class _CustomUpdate(T.Update):

            def _setup(self):
                self.x.before = False
                self.x.after = False

            def _before_execute(self, db, foo):
                self.x.before = True

            def _after_execute(self, db, foo):
                self.x.after = True
    '''

    def test(self):
        tx = db.Foo.t.custom_create()
        assert tx.x.before == False
        assert tx.x.after == False
        tx.name = 'hi'
        foo = db.execute(tx)
        assert foo.name == 'hi'
        assert tx.x.before == True
        assert tx.x.after == True
        tx = foo.t.custom_update()
        assert tx.x.before == False
        assert tx.x.after == False
        tx.name = 'ha'
        db.execute(tx)
        assert foo.name == 'ha'
        assert tx.x.before == True
        assert tx.x.after == True
        tx = foo.t.custom_delete()
        assert tx.x.before == False
        assert tx.x.after == False
        db.execute(tx)
        assert foo not in db.Foo
        assert tx.x.before == True
        assert tx.x.after == True


# class TestTransactionCDUSubclass1(BaseTransactionCDUSubclass):

#     include = True

#     format = 1


class TestTransactionCDUSubclass2(BaseTransactionCDUSubclass):

    include = True

    format = 2
