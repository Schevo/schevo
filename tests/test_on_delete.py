"""Entity/extent unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.test import CreatesSchema


class TestOnDelete(CreatesSchema):

    body = '''

    class AlphaAlpha(E.Entity):
        """Referred to by other classes, and can also optionally refer to
        self."""

        beta = f.integer()
        alpha_alpha = f.entity('AlphaAlpha', required=False)

        _key(beta)

        _hidden = True

        def __unicode__(self):
            return u'beta %i' % self.beta


    class AlphaBravo(E.Entity):
        """Has a reference to an AlphaAlpha, such that when that
        AlphaAlpha is deleted, this AlphaBravo will also be deleted."""

        alpha_alpha = f.entity(('AlphaAlpha', CASCADE))
        foo = f.entity('Foo')

        class _Update(T.Update):

            def _before_execute(self, db, entity):
                raise RuntimeError("Update should not be used directly.")


    class Foo(E.Entity):
        """A reference to Foo is maintained by AlphaBravo."""

        name = f.unicode()

        _key(name)


    class AlphaCharlie(E.Entity):
        """Has a reference to an AlphaAlpha, such that when that
        AlphaAlpha is deleted, the operation will fail because the
        deletion of this AlphaCharlie is restricted."""

        alpha_alpha = f.entity('AlphaAlpha', on_delete=RESTRICT)


    class AlphaDelta(E.Entity):
        """Has a reference to an AlphaAlpha, such that when that
        AlphaAlpha is deleted, this field on this AlphaDelta will be set
        to UNASSIGNED."""

        alpha_alpha = f.entity('AlphaAlpha', on_delete=UNASSIGN,
                               required=False)


    class AlphaEcho(E.Entity):
        """Has a reference to an AlphaAlpha or an AlphaBravo, such that
        when a referenced AlphaAlpha is deleted, this field on this
        AlphaEcho will be set to UNASSIGNED, and when a referenced
        AlphaBravo is deleted, this AlphaEcho will also be deleted."""

        alpha_or_bravo = f.entity(('AlphaAlpha', UNASSIGN),
                                  ('AlphaBravo', CASCADE), required=False)


    class AlphaFoxtrot(E.Entity):
        """Has a reference to an AlphaAlpha, such that when that
        AlphaAlpha is deleted, this field on this AlphaDelta will be set
        to UNASSIGNED."""

        alpha_alpha = f.entity('AlphaAlpha', on_delete=UNASSIGN,
                               required=False)

        class _Update(T.Update):

            def _before_execute(self, db, entity):
                raise RuntimeError("We expect this to get called and fail.")
    '''

    def _alpha_alpha(self):
        """Return an AlphaAlpha instance."""
        tx = db.AlphaAlpha.t.create(beta=1)
        aa = db.execute(tx)
        # Set a self reference to make sure those are handled
        # properly.
        tx = aa.t.update(alpha_alpha=aa)
        return db.execute(tx)

    def _alpha_and_bravo(self):
        """Return an AlphaAlpha and AlphaBravo instance."""
        tx = db.AlphaAlpha.t.create(beta=1)
        aa = db.execute(tx)
        tx = aa.t.update(alpha_alpha=aa)
        db.execute(tx)
        tx = db.Foo.t.create(name='Foo')
        foo = db.execute(tx)
        tx = db.AlphaBravo.t.create(alpha_alpha=aa, foo=foo)
        ab = db.execute(tx)
        return (aa, ab)

    def test_cascade(self):
        alpha_alpha, alpha_bravo = self._alpha_and_bravo()
        tx = alpha_alpha.t.delete()
        db.execute(tx)
        assert alpha_bravo not in db.AlphaBravo

    def test_restrict(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaCharlie.t.create(alpha_alpha=alpha_alpha)
        alpha_charlie = db.execute(tx)
        tx = alpha_alpha.t.delete()
        self.assertRaises(error.DeleteRestricted,
                          db.execute, tx)

    def test_unassign(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaDelta.t.create(alpha_alpha=alpha_alpha)
        alpha_delta = db.execute(tx)
        tx = alpha_alpha.t.delete()
        db.execute(tx)
        assert alpha_delta.alpha_alpha is UNASSIGNED

    def test_unassign_with_customized_update(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaFoxtrot.t.create(alpha_alpha=alpha_alpha)
        alpha_foxtrot = db.execute(tx)
        tx = alpha_alpha.t.delete()
        self.assertRaises(RuntimeError, db.execute, tx)

    def test_unassign_or_cascade(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaEcho.t.create(alpha_or_bravo=alpha_alpha)
        alpha_echo = db.execute(tx)
        tx = alpha_alpha.t.delete()
        db.execute(tx)
        assert alpha_echo.alpha_or_bravo is UNASSIGNED
        alpha_alpha, alpha_bravo = self._alpha_and_bravo()
        tx = db.AlphaEcho.t.create(alpha_or_bravo=alpha_bravo)
        alpha_echo = db.execute(tx)
        tx = alpha_alpha.t.delete()
        db.execute(tx)
        assert alpha_bravo not in db.AlphaBravo
        assert alpha_echo not in db.AlphaEcho


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
