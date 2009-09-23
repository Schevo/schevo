"""Entity/extent unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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

        name = f.string()

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


    # ----------------------------------------------------------------


    class Bam(E.Entity):
        """Bam and Bat circularly reference eachother.

        The relationships created upon a creation of a Bam entity
        can be visualized as follows::

                        .---------------.
                        | Bam[1]        |<----.
                        |               |     |
                  .-------.bat = Bat[1] |     | RESTRICT
                  |     `---------------`     |
         RESTRICT |                           |
                  |     .---------------.     |
                  `---->| Bat[1]        |     |
                        |               |     |
                        | .bam = Bam[1]-------`
                        `---------------`
        """

        bat = f.entity('Bat')

        class _Create(T.Create):

            def _setup(self):
                # We assign this internally.
                del self.f.bat

            def _after_execute(self, db, bam):
                create = db.Bat.t.create
                # Every bam has one bat.
                bat = db.execute(create(bam=bam))
                db.execute(bam.t.update(bat=bat))


    class Bat(E.Entity):

        bam = f.entity('Bam')


    # ----------------------------------------------------------------


    class Bamc(E.Entity):
        """Bamc and Batc circularly reference eachother.

        The relationships created upon a creation of a Bamc entity
        can be visualized as follows::

                        .-----------------.
                        | Bamc[1]         |<----.
                        |                 |     |
                  .-------.batc = Batc[1] |     | CASCADE
                  |     `-----------------`     |
         RESTRICT |                             |
                  |     .-----------------.     |
                  `---->| Batc[1]         |     |
                        |                 |     |
                        | .bamc = Bamc[1]-------`
                        `-----------------`
        """

        batc = f.entity('Batc')

        class _Create(T.Create):

            def _setup(self):
                # We assign this internally.
                del self.f.batc

            def _after_execute(self, db, bamc):
                create = db.Batc.t.create
                # Every bamc has one batc.
                batc = db.execute(create(bamc=bamc))
                db.execute(bamc.t.update(batc=batc))


    class Batc(E.Entity):

        bamc = f.entity('Bamc', on_delete=CASCADE)


    # ----------------------------------------------------------------


    class Bamm(E.Entity):

        batt = f.entity('Batt', required=False)

        class _Create(T.Create):

            def _after_execute(self, db, bamm):
                batt = db.execute(db.Batt.t.create())
                bobb = db.execute(db.Bobb.t.create(bamm=bamm))
                db.execute(batt.t.update(bobb=bobb))
                db.execute(bamm.t.update(batt=batt))


    class Batt(E.Entity):

        bobb = f.entity('Bobb', required=False)


    class Bobb(E.Entity):

        bamm = f.entity('Bamm', required=False)


    # ----------------------------------------------------------------


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
                        `---------------`       |           |
                                                |CASCADE    |
                        .---------------.       |           |
                        | Bar[1]        |       |           |
                    .-> |               |       |           |CASCADE
                    |   | .boo = Boo[1]---------`           |
                    |   | .baz = Baz[1]---------.           |
                    |   `---------------`       |           |
                    |                           |           |
            RESTRICT|   .---------------.       |RESTRICT   |
                    |   | Baz[1]        |       |           |
                    |   |               | <-----`           |
                    |   | .boo = Boo[1]---------------------`
                    `-----.bar = Bar[1] |
                        `---------------`
        """

        name = f.string()

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


    # ----------------------------------------------------------------


    class Foo(E.Entity):
        """We want cascades to succeed in a deep hierarchy as well.

        The relationships created upon a creation of a Foo entity
        can be visualized as follows::

                                   .---------------.
                                   | Foo[1]        | <----------------.
                                   |               | <-----.          |
                                   | .name = 'FOO' |       |          |
                                   `---------------`       |          |
                                                           |CASCADE   |
                                   .---------------.       |          |
                                   | Far[1]        |       |          |
                    .------------> |               |       |          |CASCADE
                    |              | .foo = Foo[1]---------`          |
                    |              `---------------`                  |
                    |                                                 |
                    |              .---------------.                  |
            RESTRICT|              | Faz[1]        |                  |
                    |          .-> |               |                  |
                    |          |   | .foo = Foo[1]--------------------`
                    |          |   `---------------`
                    |   CASCADE|
                    |          |   .---------------.
                    |          |   | Fee[1]        |
                    |          |   |               |
                    |          `-----.faz = Faz[1] |
                    `----------------.far = Far[1] |
                                   `---------------`
        """

        name = f.string()

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


    # ----------------------------------------------------------------


    class Moo(E.Entity):
        """We want cascades to succeed in a deep hierarchy as well.

        The relationships created upon a creation of a Moo entity
        can be visualized as follows::

                       .---------------.
                       | Moo[1]        | <-----------------.
                       |               | <-----.           |
                       | .name = 'MOO' |       |           |
                       `---------------`       |           |
                                               |CASCADE    |
                       .---------------.       |           |
                       | Mar[1]        |       |           |
                   .-> |               |       |           |CASCADE
                   |   | .moo = Moo[1]---------|           |
                   |   `---------------`                   |
                   |                                       |
            CASCADE|   .---------------.                   |
                   |   | Maz[1]        |                   |
                   |   |               |                   |
                   |-----.mar = Mar[1] |                   |
                       | .moo = Moo[1]---------------------|
                       `---------------`
        """

        name = f.string()

        class _Create(T.Create):

            def _after_execute(self, db, moo):
                mar = db.execute(db.Mar.t.create(moo=moo))
                maz = db.execute(db.Maz.t.create(mar=mar, moo=moo))


    class Mar(E.Entity):

        moo = f.entity(('Moo', CASCADE))


    class Maz(E.Entity):

        mar = f.entity(('Mar', CASCADE))
        moo = f.entity(('Moo', CASCADE))

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

    def test_cascade_bamc(self):
        bamc = db.execute(db.Bamc.t.create())
        tx = bamc.t.delete()
        db.execute(tx)
        assert bamc not in db.Bamc

    def test_restrict_bam(self):
        bam = db.execute(db.Bam.t.create())
        tx = bam.t.delete()
        try:
            db.execute(tx)
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (db.Bam[1], db.Bat[1], 'bam')
                ])

    def test_restrict_bamm(self):
        bamm = db.execute(db.Bamm.t.create())
        tx = bamm.t.delete()
        try:
            db.execute(tx)
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (db.Bamm[1], db.Bobb[1], 'bamm'),
                ])

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
        assert boo.s.count() == 2
        assert bar.s.count() == 1
        assert baz.s.count() == 1
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

    def test_cascade_complex_hierarchy_foo(self):
        foo = db.execute(db.Foo.t.create(name='FOO'))
        assert len(db.Foo) == 1
        assert len(db.Far) == 1
        assert len(db.Faz) == 1
        assert len(db.Fee) == 1
        db.execute(foo.t.delete())
        assert len(db.Foo) == 0
        assert len(db.Far) == 0
        assert len(db.Faz) == 0
        assert len(db.Fee) == 0

    def test_cascade_complex_hierarchy_moo(self):
        moo = db.execute(db.Moo.t.create(name='MOO'))
        assert len(db.Moo) == 1
        assert len(db.Mar) == 1
        assert len(db.Maz) == 1
        db.execute(moo.t.delete())
        assert len(db.Moo) == 0
        assert len(db.Mar) == 0
        assert len(db.Maz) == 0

    def test_restrict(self):
        alpha_alpha = self._alpha_alpha()
        tx = db.AlphaCharlie.t.create(alpha_alpha=alpha_alpha)
        alpha_charlie = db.execute(tx)
        tx = alpha_alpha.t.delete()
        try:
            db.execute(tx)
        except error.DeleteRestricted, e:
            assert e.restrictions == set([
                (alpha_alpha, alpha_charlie, 'alpha_alpha'),
                ])

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


# class TestOnDelete1(BaseOnDelete):

#     include = True

#     format = 1

#     def internal_cascade_complex_1(self):
#         root = db._root
#         schevo = root['SCHEVO']
#         extent_name_id = schevo['extent_name_id']
#         extents = schevo['extents']
#         Boo_extent_id = extent_name_id['Boo']
#         Bar_extent_id = extent_name_id['Bar']
#         Baz_extent_id = extent_name_id['Baz']
#         Boo_extent = extents[Boo_extent_id]
#         Bar_extent = extents[Bar_extent_id]
#         Baz_extent = extents[Baz_extent_id]
#         Boo_field_name_id = Boo_extent['field_name_id']
#         Bar_field_name_id = Bar_extent['field_name_id']
#         Baz_field_name_id = Baz_extent['field_name_id']
#         assert len(Boo_extent['entities']) == 1
#         assert len(Bar_extent['entities']) == 1
#         assert len(Baz_extent['entities']) == 1
#         # Check for Boo[1] having backlinks to Bar[1].boo and Baz[1].boo
#         Boo1 = Boo_extent['entities'][1]
#         assert Boo1['link_count'] == 2
#         Bar_boo_field_id = Bar_field_name_id['boo']
#         Baz_boo_field_id = Baz_field_name_id['boo']
#         Boo1_links_keys = set(Boo1['links'].keys())
#         expected_Boo1_links_keys = set([
#             (Bar_extent_id, Bar_boo_field_id),
#             (Baz_extent_id, Baz_boo_field_id),
#             ])
#         assert Boo1_links_keys == expected_Boo1_links_keys
#         assert list(
#             Boo1['links'][(Bar_extent_id, Bar_boo_field_id)].keys()) == [1]
#         assert list(
#             Boo1['links'][(Baz_extent_id, Baz_boo_field_id)].keys()) == [1]
#         # Check for Bar[1] having backlink to Baz[1].bar
#         Bar1 = Bar_extent['entities'][1]
#         assert Bar1['link_count'] == 1
#         Baz_bar_field_id = Baz_field_name_id['bar']
#         Bar1_links_keys = set(Bar1['links'].keys())
#         expected_Bar1_links_keys = set([
#             (Baz_extent_id, Baz_bar_field_id),
#             ])
#         assert Bar1_links_keys == expected_Bar1_links_keys
#         assert list(
#             Bar1['links'][(Baz_extent_id, Baz_bar_field_id)].keys()) == [1]
#         # Check for Baz[1] having backlink to Bar[1].bar
#         Baz1 = Baz_extent['entities'][1]
#         assert Baz1['link_count'] == 1
#         Bar_baz_field_id = Bar_field_name_id['baz']
#         Baz1_links_keys = set(Baz1['links'].keys())
#         expected_Baz1_links_keys = set([
#             (Bar_extent_id, Bar_baz_field_id),
#             ])
#         assert Baz1_links_keys == expected_Baz1_links_keys
#         assert list(
#             Baz1['links'][(Bar_extent_id, Bar_baz_field_id)].keys()) == [1]
#         # Check for Bar[1].boo and Bar[1].baz having correct related entity
#         # structures.
#         Bar1_fields = Bar1['fields']
#         Bar_boo_field_id = Bar_field_name_id['boo']
#         Bar1_boo = Bar1_fields[Bar_boo_field_id]
#         assert Bar1_boo == (Boo_extent_id, 1)
#         Bar_baz_field_id = Bar_field_name_id['baz']
#         Bar1_baz = Bar1_fields[Bar_baz_field_id]
#         assert Bar1_baz == (Baz_extent_id, 1)

#     def internal_cascade_complex_2(self):
#         root = db._root
#         schevo = root['SCHEVO']
#         extent_name_id = schevo['extent_name_id']
#         extents = schevo['extents']
#         Boo_extent_id = extent_name_id['Boo']
#         Bar_extent_id = extent_name_id['Bar']
#         Baz_extent_id = extent_name_id['Baz']
#         Boo_extent = extents[Boo_extent_id]
#         Bar_extent = extents[Bar_extent_id]
#         Baz_extent = extents[Baz_extent_id]
#         assert len(Boo_extent['entities']) == 0
#         assert len(Bar_extent['entities']) == 0
#         assert len(Baz_extent['entities']) == 0


class TestOnDelete2(BaseOnDelete):

    include = True

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
        assert list(
            Boo1['links'][(Bar_extent_id, Bar_boo_field_id)].keys()) == [1]
        assert list(
            Boo1['links'][(Baz_extent_id, Baz_boo_field_id)].keys()) == [1]
        # Check for Bar[1] having backlink to Baz[1].bar
        Bar1 = Bar_extent['entities'][1]
        assert Bar1['link_count'] == 1
        Baz_bar_field_id = Baz_field_name_id['bar']
        Bar1_links_keys = set(Bar1['links'].keys())
        expected_Bar1_links_keys = set([
            (Baz_extent_id, Baz_bar_field_id),
            ])
        assert Bar1_links_keys == expected_Bar1_links_keys
        assert list(
            Bar1['links'][(Baz_extent_id, Baz_bar_field_id)].keys()) == [1]
        # Check for Baz[1] having backlink to Bar[1].bar
        Baz1 = Baz_extent['entities'][1]
        assert Baz1['link_count'] == 1
        Bar_baz_field_id = Bar_field_name_id['baz']
        Baz1_links_keys = set(Baz1['links'].keys())
        expected_Baz1_links_keys = set([
            (Bar_extent_id, Bar_baz_field_id),
            ])
        assert Baz1_links_keys == expected_Baz1_links_keys
        assert list(
            Baz1['links'][(Bar_extent_id, Bar_baz_field_id)].keys()) == [1]
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


# --------------------------------------------------------------------


class BaseOnDeleteKeyRelax(CreatesSchema):

    body = """

    class Foo(E.Entity):

        bar = f.entity('Bar', on_delete=CASCADE)
        baz = f.entity('Baz', on_delete=CASCADE)

        _key(baz)

        _sample_unittest = [
            ((1,), ((1,), 1)),
            ((1,), ((1,), 2)),
            ((2,), ((2,), 1)),
            ((2,), ((2,), 2)),
            ]


    class Bar(E.Entity):

        number = f.integer()

        _key(number)

        _sample_unittest = [
            (1,),
            (2,),
            ]


    class Baz(E.Entity):

        bar = f.entity('Bar', on_delete=CASCADE)
        number = f.integer()

        _key(bar, number)

        _sample_unittest = [
            ((1,), 1),
            ((1,), 2),
            ((2,), 1),
            ((2,), 2),
            ]

    """

    def test_delete_bar(self):
        assert len(db.Foo) == 4
        assert len(db.Bar) == 2
        assert len(db.Baz) == 4
        bar1 = db.Bar.findone(number=1)
        ex(bar1.t.delete())
        assert len(db.Foo) == 2
        assert len(db.Bar) == 1
        assert len(db.Baz) == 2


# class TestOnDeleteKeyRelax1(BaseOnDeleteKeyRelax):

#     include = True

#     format = 1


class TestOnDeleteKeyRelax2(BaseOnDeleteKeyRelax):

    include = True

    format = 2


# --------------------------------------------------------------------


class BaseOnDeleteEntityListRemove(CreatesSchema):

    body = """

    class Foo(E.Entity):

        name = f.string()
        bars = f.entity_list(('Bar', REMOVE), min_size=1)

        _key(name)

        _sample_unittest_priority = 1

        @staticmethod
        def _sample_unittest(db):
            bar1 = db.Bar.findone(name=u'bar 1')
            bar2 = db.Bar.findone(name=u'bar 2')
            foo = db.execute(db.Foo.t.create(name=u'foo 1', bars=[bar1, bar2]))


    class Fob(E.Entity):

        name = f.string()
        bars = f.entity_list(('Bar', REMOVE), min_size=0)

        _key(name)

        _sample_unittest_priority = 1

        @staticmethod
        def _sample_unittest(db):
            bar3 = db.Bar.findone(name=u'bar 3')
            fob = db.execute(db.Fob.t.create(name=u'fob 1', bars=[bar3]))


    class Bar(E.Entity):

        name = f.string()

        _key(name)

        _sample_unittest_priority = 2

        _sample_unittest = [
            (u'bar 1', ),
            (u'bar 2', ),
            (u'bar 3', ),
            ]
    """

    def test_sample_data(self):
        bar1 = db.Bar.findone(name=u'bar 1')
        bar2 = db.Bar.findone(name=u'bar 2')
        foo1 = db.Foo.findone(name=u'foo 1')
        assert list(foo1.bars) == [bar1, bar2]

    def test_remove_min_one(self):
        bar1 = db.Bar.findone(name=u'bar 1')
        bar2 = db.Bar.findone(name=u'bar 2')
        foo1 = db.Foo.findone(name=u'foo 1')
        db.execute(bar1.t.delete())
        assert list(foo1.bars) == [bar2]
        # Deleting bar2 should fail due to foo1.bars becoming an empty
        # list, which is not allowed.
        call = db.execute, bar2.t.delete()
        assert raises(ValueError, *call)

    def test_remove_min_zero(self):
        bar3 = db.Bar.findone(name=u'bar 3')
        fob1 = db.Fob.findone(name=u'fob 1')
        db.execute(bar3.t.delete())
        assert list(fob1.bars) == []


# Not supported with format 1 databases.


class TestOnDeleteEntityListRemove2(BaseOnDeleteEntityListRemove):

    include = True

    format = 2


# --------------------------------------------------------------------


class BaseOnDeleteUnassignReadonlyField(CreatesSchema):

    body = """

    class Foo(E.Entity):

        name = f.string()
        bar = f.entity('Bar', required=False, on_delete=UNASSIGN)

        _key(name)

        _sample_unittest = [
            (u'foo 1', (u'bar 1', )),
            ]

        class _Update(T.Update):

            bar = f.entity('Bar', required=False, readonly=True)

    class Bar(E.Entity):

        name = f.string()

        _key(name)

        _sample_unittest = [
            (u'bar 1', ),
            ]
    """

    def test_readonly_on_update(self):
        foo = db.Foo.findone(name=u'foo 1')
        tx = foo.t.update()
        call = setattr, tx, 'bar', UNASSIGNED
        assert raises(AttributeError, *call)

    def test_unassigns_on_delete(self):
        foo = db.Foo.findone(name=u'foo 1')
        bar = foo.bar
        db.execute(bar.t.delete())
        assert foo.bar is UNASSIGNED


# class TestOnDeleteUnassignReadonlyField1(BaseOnDeleteUnassignReadonlyField):

#     include = True

#     format = 1


class TestOnDeleteUnassignReadonlyField2(BaseOnDeleteUnassignReadonlyField):

    include = True

    format = 2


# --------------------------------------------------------------------


class BaseOnDeleteUnassignEntityList(CreatesSchema):

    body = """

    class Foo(E.Entity):

        name = f.string()
        bar_list = f.entity_list('Bar', on_delete=UNASSIGN,
                                 allow_unassigned=True)

        _key(name)


    class Fee(E.Entity):

        name = f.string()
        bar_list = f.entity_list('Bar', on_delete=UNASSIGN)

        _key(name)


    class Fum(E.Entity):

        name = f.string()
        bar_list = f.entity_list('Bar', on_delete=UNASSIGN,
                                 allow_unassigned=True,
                                 allow_duplicates=False)

        _key(name)


    class Bar(E.Entity):

        name = f.string()

        _key(name)

        _sample_unittest = [
            (u'bar 1', ),
            (u'bar 2', ),
            (u'bar 3', ),
            (u'bar 4', ),
            (u'bar 5', ),
            ]
    """

    def test_unassign_when_unassigned_allowed(self):
        bar1, bar2, bar3, bar4, bar5 = db.Bar.by('name')
        foo = ex(db.Foo.t.create(
            name='foo',
            bar_list=[bar1, bar2, bar3, bar4, bar5, bar4, bar3],
            ))
        assert list(foo.bar_list) == [bar1, bar2, bar3, bar4, bar5, bar4, bar3]
        ex(bar4.t.delete())
        UA = UNASSIGNED
        assert list(foo.bar_list) == [bar1, bar2, bar3, UA, bar5, UA, bar3]

    def test_unassign_when_unassigned_allowed_no_duplicates(self):
        bar1, bar2, bar3, bar4, bar5 = db.Bar.by('name')
        fum = ex(db.Fum.t.create(
            name='fum',
            bar_list=[bar1, bar2, bar3, bar4, bar5],
            ))
        assert list(fum.bar_list) == [bar1, bar2, bar3, bar4, bar5]
        ex(bar4.t.delete())
        assert list(fum.bar_list) == [bar1, bar2, bar3, UNASSIGNED, bar5]
        # Deleting one more will not be allowed since it would cause
        # duplication.
        call = ex, bar3.t.delete()
        assert raises(ValueError, *call)

    def test_unassign_when_unassigned_disallowed(self):
        bar1, bar2, bar3, bar4, bar5 = db.Bar.by('name')
        fee = ex(db.Fee.t.create(
            name='fee',
            bar_list=[bar1, bar2, bar3, bar4, bar5, bar4, bar3],
            ))
        assert list(fee.bar_list) == [bar1, bar2, bar3, bar4, bar5, bar4, bar3]
        call = ex, bar4.t.delete()
        assert raises(ValueError, *call)


# Not supported with format 1 databases.


class TestOnDeleteUnassignEntityList2(BaseOnDeleteUnassignEntityList):

    include = True

    format = 2
