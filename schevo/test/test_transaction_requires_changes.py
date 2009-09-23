"""Transaction unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema, raises
from schevo import error


class BaseTransactionRequireChanges(CreatesSchema):

    body = '''

    class Alpha(E.Entity):

        foo = f.integer()

        class _Update(T.Update):

            _requires_changes = False

    class Bravo(E.Entity):

        bar = f.integer()

    '''

    def test_require_changes(self):
        """Update transaction subclasses require a change to at least
        one field by default. A TransactionFieldsNotChanged error is
        raised if no changes were made to any fields."""
        b = db.execute(db.Bravo.t.create(bar=1))
        tx = b.t.update()
        # Error is raised when no fields are changed.
        try:
            db.execute(tx)
        except error.TransactionFieldsNotChanged, e:
            assert e.transaction == tx
        # No error is raised when changes are made.
        b = db.execute(b.t.update(bar=2))
        assert b.bar == 2

    def test_do_not_require_changes(self):
        """Update transaction subclasses that set _require_changes to
        False succeed if no changes have been made to any fields."""
        a = db.execute(db.Alpha.t.create(foo=1))
        a = db.execute(a.t.update())
        assert a.foo == 1


# class TestTransactionRequireChanges1(BaseTransactionRequireChanges):

#     include = True

#     format = 1


class TestTransactionRequireChanges2(BaseTransactionRequireChanges):

    include = True

    format = 2
