"""Entity/extent unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.placeholder import Placeholder
from schevo.test import CreatesSchema, raises


class BaseOnDelete(CreatesSchema):

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
        alpha_foo = f.entity('AlphaFoo')

        class _Update(T.Update):

            def _before_execute(self, db, entity):
                raise RuntimeError("Update should not be used directly.")


    class AlphaFoo(E.Entity):
        """A reference to AlphaFoo is maintained by AlphaBravo."""

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


    class Boo(E.Entity):
        """The parent of two children, one of which references the
        other.  We want the cascade to succeed on both children in
        spite of the field reference that has the default RESTRICT.

        The relationships created upon a creation of a Boo entity
        can be visualized as follows::

                        .---------------.
                        | Boo[1]        | <-----------------.
                        |               | <-----.           |
                        | .name = 'BOO' |       |           |
                        '---------------'       |           |
                                                |CASCADE    |
                        .---------------.       |           |
                        | Bar[1]        |       |           |
                    .-> |               |       |           |CASCADE
                    |   | .boo = Boo[1]---------'           |
                    |   | .baz = Baz[1]---------.           |
                    |   '---------------'       |           |
                    |                           |           |
            RESTRICT|   .---------------.       |RESTRICT   |
                    |   | Baz[1]        |       |           |
                    |   |               | <-----'           |
                    |   | .boo = Boo[1]---------------------'
                    '-----.bar = Bar[1] |
                        '---------------'
        """

        name = f.unicode()

        class _Create(T.Create):

            def _after_execute(self, db, boo):
                bar = db.execute(db.Bar.t.create(boo=boo))
                baz = db.execute(db.Baz.t.create(boo=boo, bar=bar))
                db.execute(bar.t.update(baz=baz))


    class Bar(E.Entity):
        """We want this entity to be able to be cascade deleted even
        though a reference from a Baz (via the bar field) might block
        it.  Because the delete of the Baz is part of the same cascade
        transaction its bar field should not prevent the delete of
        this Bar."""

        boo = f.entity(('Boo', CASCADE))
        baz = f.entity('Baz', required=False)


    class Baz(E.Entity):
        """The bar field is required and has the default of RESTRICT."""

        boo = f.entity(('Boo', CASCADE))
        bar = f.entity('Bar')


    class Foo(E.Entity):
        """We want cascades to succeed in a deep hierarchy as well."""

        name = f.unicode()

        class _Create(T.Create):

            def _after_execute(self, db, foo):
                far = db.execute(db.Far.t.create(foo=foo))
                faz = db.execute(db.Faz.t.create(foo=foo))
                fee = db.execute(db.Fee.t.create(faz=faz, far=far))


    class Far(E.Entity):
        """We want this entity to be able to be cascade deleted even
        though a reference from a Fee (via the far field) might block
        it.  Because the delete of the Fee is part of the same cascade
        transaction its far field should not prevent the delete of
        this Far."""

        foo = f.entity(('Foo', CASCADE))


    class Faz(E.Entity):

        foo = f.entity(('Foo', CASCADE))


    class Fee(E.Entity):
        """The far field is required and has the default of RESTRICT."""

        faz = f.entity(('Faz', CASCADE))
        far = f.entity('Far')

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
        tx = db.AlphaFoo.t.create(name='AlphaFoo')
        alpha_foo = db.execute(tx)
        tx = db.AlphaBravo.t.create(alpha_alpha=aa, alpha_foo=alpha_foo)
        ab = db.execute(tx)
        return (aa, ab)

    def test_cascade(self):
        alpha_alpha, alpha_bravo = self._alpha_and_bravo()
        tx = alpha_alpha.t.delete()
        db.execute(tx)
        assert alpha_bravo not in db.AlphaBravo

    def test_cascade_complex(self):
        # Create the complex structure.
        boo = db.execute(db.Boo.t.create(name='BOO'))
        assert len(db.Boo) == 1
        assert len(db.Bar) == 1
        assert len(db.Baz) == 1
        bar = db.Bar[1]
        baz = db.Baz[1]
        assert bar.boo == boo
        assert bar.baz == baz
        assert baz.boo == boo
        assert baz.bar == bar
        assert bar.m.bazs() == [baz]
        assert baz.m.bars() == [bar]
        assert boo.m.bars() == [bar]
        assert boo.m.bazs() == [baz]
        assert boo.sys.count() == 2
        assert bar.sys.count() == 1
        assert baz.sys.count() == 1
        self.internal_cascade_complex_1()
        # Delete it.
        db.execute(boo.t.delete())
        assert len(db.Boo) == 0
        assert len(db.Bar) == 0
        assert len(db.Baz) == 0
        self.internal_cascade_complex_2()

    def internal_cascade_complex_1(self):
        raise NotImplementedError()

    def internal_cascade_complex_2(self):
        raise NotImplementedError()

##     def test_cascade_complex_hierarchy(self):
##         foo = db.execute(db.Foo.t.create(name='FOO'))
##         assert len(db.Foo) == 1
##         assert len(db.Far) == 1
##         assert len(db.Faz) == 1
##         assert len(db.Fee) == 1
##         db.execute(foo.t.delete())
##         assert len(db.Foo) == 0
##         assert len(db.Far) == 0
##         assert len(db.Faz) == 0
##         assert len(db.Fee) == 0

    def test_restrict(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaCharlie.t.create(alpha_alpha=alpha_alpha)
        alpha_charlie = db.execute(tx)
        tx = alpha_alpha.t.delete()
        assert raises(error.DeleteRestricted, db.execute, tx)

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
        assert raises(RuntimeError, db.execute, tx)

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


class TestOnDelete1(BaseOnDelete):

    format = 1

    def internal_cascade_complex_1(self):
        root = db._root
        schevo = root['SCHEVO']
        extent_name_id = schevo['extent_name_id']
        extents = schevo['extents']
        Boo_extent_id = extent_name_id['Boo']
        Bar_extent_id = extent_name_id['Bar']
        Baz_extent_id = extent_name_id['Baz']
        Boo_extent = extents[Boo_extent_id]
        Bar_extent = extents[Bar_extent_id]
        Baz_extent = extents[Baz_extent_id]
        Boo_field_name_id = Boo_extent['field_name_id']
        Bar_field_name_id = Bar_extent['field_name_id']
        Baz_field_name_id = Baz_extent['field_name_id']
        assert len(Boo_extent['entities']) == 1
        assert len(Bar_extent['entities']) == 1
        assert len(Baz_extent['entities']) == 1
        # Check for Boo[1] having backlinks to Bar[1].boo and Baz[1].boo
        Boo1 = Boo_extent['entities'][1]
        assert Boo1['link_count'] == 2
        Bar_boo_field_id = Bar_field_name_id['boo']
        Baz_boo_field_id = Baz_field_name_id['boo']
        Boo1_links_keys = set(Boo1['links'].keys())
        expected_Boo1_links_keys = set([
            (Bar_extent_id, Bar_boo_field_id),
            (Baz_extent_id, Baz_boo_field_id),
            ])
        assert Boo1_links_keys == expected_Boo1_links_keys
        assert Boo1['links'][(Bar_extent_id, Bar_boo_field_id)].keys() == [1]
        assert Boo1['links'][(Baz_extent_id, Baz_boo_field_id)].keys() == [1]
        # Check for Bar[1] having backlink to Baz[1].bar
        Bar1 = Bar_extent['entities'][1]
        assert Bar1['link_count'] == 1
        Baz_bar_field_id = Baz_field_name_id['bar']
        Bar1_links_keys = set(Bar1['links'].keys())
        expected_Bar1_links_keys = set([
            (Baz_extent_id, Baz_bar_field_id),
            ])
        assert Bar1_links_keys == expected_Bar1_links_keys
        assert Bar1['links'][(Baz_extent_id, Baz_bar_field_id)].keys() == [1]
        # Check for Baz[1] having backlink to Bar[1].bar
        Baz1 = Baz_extent['entities'][1]
        assert Baz1['link_count'] == 1
        Bar_baz_field_id = Bar_field_name_id['baz']
        Baz1_links_keys = set(Baz1['links'].keys())
        expected_Baz1_links_keys = set([
            (Bar_extent_id, Bar_baz_field_id),
            ])
        assert Baz1_links_keys == expected_Baz1_links_keys
        assert Baz1['links'][(Bar_extent_id, Bar_baz_field_id)].keys() == [1]
        # Check for Bar[1].boo and Bar[1].baz having correct related entity
        # structures.
        Bar1_fields = Bar1['fields']
        Bar_boo_field_id = Bar_field_name_id['boo']
        Bar1_boo = Bar1_fields[Bar_boo_field_id]
        assert Bar1_boo == (Boo_extent_id, 1)
        Bar_baz_field_id = Bar_field_name_id['baz']
        Bar1_baz = Bar1_fields[Bar_baz_field_id]
        assert Bar1_baz == (Baz_extent_id, 1)

    def internal_cascade_complex_2(self):
        root = db._root
        schevo = root['SCHEVO']
        extent_name_id = schevo['extent_name_id']
        extents = schevo['extents']
        Boo_extent_id = extent_name_id['Boo']
        Bar_extent_id = extent_name_id['Bar']
        Baz_extent_id = extent_name_id['Baz']
        Boo_extent = extents[Boo_extent_id]
        Bar_extent = extents[Bar_extent_id]
        Baz_extent = extents[Baz_extent_id]
        assert len(Boo_extent['entities']) == 0
        assert len(Bar_extent['entities']) == 0
        assert len(Baz_extent['entities']) == 0


class TestOnDelete2(BaseOnDelete):

    format = 2

    def internal_cascade_complex_1(self):
        root = db._root
        schevo = root['SCHEVO']
        extent_name_id = schevo['extent_name_id']
        extents = schevo['extents']
        Boo_extent_id = extent_name_id['Boo']
        Bar_extent_id = extent_name_id['Bar']
        Baz_extent_id = extent_name_id['Baz']
        Boo_extent = extents[Boo_extent_id]
        Bar_extent = extents[Bar_extent_id]
        Baz_extent = extents[Baz_extent_id]
        Boo_field_name_id = Boo_extent['field_name_id']
        Bar_field_name_id = Bar_extent['field_name_id']
        Baz_field_name_id = Baz_extent['field_name_id']
        assert len(Boo_extent['entities']) == 1
        assert len(Bar_extent['entities']) == 1
        assert len(Baz_extent['entities']) == 1
        # Check for Boo[1] having backlinks to Bar[1].boo and Baz[1].boo
        Boo1 = Boo_extent['entities'][1]
        assert Boo1['link_count'] == 2
        Bar_boo_field_id = Bar_field_name_id['boo']
        Baz_boo_field_id = Baz_field_name_id['boo']
        Boo1_links_keys = set(Boo1['links'].keys())
        expected_Boo1_links_keys = set([
            (Bar_extent_id, Bar_boo_field_id),
            (Baz_extent_id, Baz_boo_field_id),
            ])
        assert Boo1_links_keys == expected_Boo1_links_keys
        assert Boo1['links'][(Bar_extent_id, Bar_boo_field_id)].keys() == [1]
        assert Boo1['links'][(Baz_extent_id, Baz_boo_field_id)].keys() == [1]
        # Check for Bar[1] having backlink to Baz[1].bar
        Bar1 = Bar_extent['entities'][1]
        assert Bar1['link_count'] == 1
        Baz_bar_field_id = Baz_field_name_id['bar']
        Bar1_links_keys = set(Bar1['links'].keys())
        expected_Bar1_links_keys = set([
            (Baz_extent_id, Baz_bar_field_id),
            ])
        assert Bar1_links_keys == expected_Bar1_links_keys
        assert Bar1['links'][(Baz_extent_id, Baz_bar_field_id)].keys() == [1]
        # Check for Baz[1] having backlink to Bar[1].bar
        Baz1 = Baz_extent['entities'][1]
        assert Baz1['link_count'] == 1
        Bar_baz_field_id = Bar_field_name_id['baz']
        Baz1_links_keys = set(Baz1['links'].keys())
        expected_Baz1_links_keys = set([
            (Bar_extent_id, Bar_baz_field_id),
            ])
        assert Baz1_links_keys == expected_Baz1_links_keys
        assert Baz1['links'][(Bar_extent_id, Bar_baz_field_id)].keys() == [1]
        # Check for Bar[1].boo and Bar[1].baz having correct related entity
        # structures.
        Bar1_related_entities = Bar1['related_entities']
        Bar_boo_field_id = Bar_field_name_id['boo']
        Bar1_related_boos = Bar1_related_entities[Bar_boo_field_id]
        expected_Bar1_related_boos = frozenset([Placeholder(db.Boo[1])])
        assert Bar1_related_boos == expected_Bar1_related_boos
        Bar_baz_field_id = Bar_field_name_id['baz']
        Bar1_related_bazs = Bar1_related_entities[Bar_baz_field_id]
        expected_Bar1_related_bazs = frozenset([Placeholder(db.Baz[1])])
        assert Bar1_related_bazs == expected_Bar1_related_bazs

    def internal_cascade_complex_2(self):
        root = db._root
        schevo = root['SCHEVO']
        extent_name_id = schevo['extent_name_id']
        extents = schevo['extents']
        Boo_extent_id = extent_name_id['Boo']
        Bar_extent_id = extent_name_id['Bar']
        Baz_extent_id = extent_name_id['Baz']
        Boo_extent = extents[Boo_extent_id]
        Bar_extent = extents[Bar_extent_id]
        Baz_extent = extents[Baz_extent_id]
        assert len(Boo_extent['entities']) == 0
        assert len(Bar_extent['entities']) == 0
        assert len(Baz_extent['entities']) == 0


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
