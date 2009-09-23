"""Entity/extent unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.label import label, plural
from schevo.test import CreatesSchema


class BaseLinks(CreatesSchema):

    # XXX: Todo: test_links

    body = r'''

    class _FoxtrotAlphaBase(E.Entity):
        """Silly base class to make sure hidden base classes do not show
        up in extent `relationships` attributes, since they do not get
        turned into extents."""

        beta = f.integer()
        foxtrot_bravo = f.entity('FoxtrotBravo', required=False)
        foxtrot_any = f.entity('FoxtrotAlpha', 'FoxtrotBravo', 'FoxtrotCharlie',
                               required=False)

        _key(beta)


    class FoxtrotAlpha(_FoxtrotAlphaBase):
        """Used for testing ``links`` and ``count``."""

        _sample_unittest = [
            (1, DEFAULT, DEFAULT),
            (2, DEFAULT, ('FoxtrotAlpha', (1, ))),
            (3, (1, ), DEFAULT),
            (4, (1, ), ('FoxtrotBravo', (1, ))),
            (5, DEFAULT, ('FoxtrotCharlie', (2, ))),
            ]


    class FoxtrotBravo(E.Entity):

        gamma = f.integer()
        foxtrot_charlie = f.entity('FoxtrotCharlie', required=False)

        _key(gamma)

        _sample_unittest = [
            (1, DEFAULT),
            (2, (1, )),
            (3, DEFAULT),
            (4, (2, )),
            (5, (2, )),
            ]


    class FoxtrotCharlie(E.Entity):

        epsilon = f.integer()

        _key(epsilon)

        _sample_unittest = [
            (1, ),
            (2, ),
            (3, ),
            (4, ),
            (5, ),
            ]


    class FoxtrotDelta(E.Entity):

        zeta = f.integer()
        foxtrot_bravo = f.entity('FoxtrotBravo', required=False)

        _key(zeta)

        _sample_unittest = [
            (1, (1, )),
            (2, DEFAULT),
            (3, DEFAULT),
            (4, DEFAULT),
            (5, DEFAULT),
            ]


    class Goauld(E.Entity):
        """Fictional characters from a TV series, to test plural usage
        on entity m namespace."""

        something = f.entity('Something')

        _label = u"Goa\u2032uld"
        _plural = u"Goa\u2032ulds"


    class Something(E.Entity):
        pass

    '''

    def test_many(self):
        charlie = db.FoxtrotCharlie.findone(epsilon=1)
        bravos = charlie.m.foxtrot_bravos('foxtrot_charlie')
        assert len(bravos) == 1
        assert db.FoxtrotBravo[2] in bravos
        bravos = charlie.m.foxtrot_bravos()
        assert len(bravos) == 1
        assert db.FoxtrotBravo[2] in bravos
        charlie = db.FoxtrotCharlie.findone(epsilon=2)
        bravos = charlie.m.foxtrot_bravos()
        assert len(bravos) == 2
        assert db.FoxtrotBravo[4] in bravos
        assert db.FoxtrotBravo[5] in bravos
        bravo = db.FoxtrotBravo[1]
        deltas = bravo.m.foxtrot_deltas()
        assert len(deltas) == 1
        assert db.FoxtrotDelta[1] in deltas
        alphas = bravo.m.foxtrot_alphas()
        assert len(alphas) == 2
        assert db.FoxtrotAlpha[3] in alphas
        assert db.FoxtrotAlpha[4] in alphas
        alphas = bravo.m.foxtrot_alphas('foxtrot_any')
        assert len(alphas) == 1
        assert db.FoxtrotAlpha[4] in alphas

    def test_many_pluralization(self):
        assert label(db.Goauld) == u"Goa\u2032uld"
        assert plural(db.Goauld) == u"Goa\u2032ulds"
        ex = db.execute
        something = ex(db.Something.t.create())
        goauld1 = ex(db.Goauld.t.create(something=something))
        goauld2 = ex(db.Goauld.t.create(something=something))
        goaulds = something.m.goaulds()
        assert len(goaulds) == 2
        assert goauld1 in goaulds
        assert goauld2 in goaulds

    def test_count(self):
        # Shortcuts for Foxtrot* extents.
        fa = db.FoxtrotAlpha
        fb = db.FoxtrotBravo
        fc = db.FoxtrotCharlie
        fd = db.FoxtrotDelta
        # Expected results.
        expected = [
            (1, fa[1]),
            (1, fa[1], 'FoxtrotAlpha'),
            (1, fa[1], 'FoxtrotAlpha', 'foxtrot_any'),
            (0, fa[2]),
            (0, fa[3]),
            (0, fa[4]),
            (0, fa[5]),
            (4, fb[1]),
            (3, fb[1], 'FoxtrotAlpha'),
            (2, fb[1], 'FoxtrotAlpha', 'foxtrot_bravo'),
            (1, fb[1], 'FoxtrotAlpha', 'foxtrot_any'),
            (0, fb[2]),
            (0, fb[3]),
            (0, fb[4]),
            (0, fb[5]),
            (1, fc[1]),
            (1, fc[1], 'FoxtrotBravo'),
            (1, fc[1], 'FoxtrotBravo', 'foxtrot_charlie'),
            (3, fc[2]),
            (1, fc[2], 'FoxtrotAlpha'),
            (1, fc[2], 'FoxtrotAlpha', 'foxtrot_any'),
            (2, fc[2], 'FoxtrotBravo'),
            (2, fc[2], 'FoxtrotBravo', 'foxtrot_charlie'),
            (0, fc[3]),
            (0, fc[4]),
            (0, fc[5]),
            ]
        for row in expected:
            expected_count = row[0]
            entity = row[1]
            call_args = row[2:]
            assert entity.s.count(*call_args) == expected_count

    def test_relationships(self):
        expected = {
            # db.Extent: [relationship, ...],
            db.FoxtrotAlpha: [('FoxtrotAlpha', 'foxtrot_any'),
                              ],
            db.FoxtrotBravo: [('FoxtrotAlpha', 'foxtrot_bravo'),
                              ('FoxtrotAlpha', 'foxtrot_any'),
                              ('FoxtrotDelta', 'foxtrot_bravo'),
                              ],
            db.FoxtrotCharlie: [('FoxtrotAlpha', 'foxtrot_any'),
                                ('FoxtrotBravo', 'foxtrot_charlie'),
                                ],
            db.FoxtrotDelta: [],
            }
        for extent, expected_relationships in expected.iteritems():
            rset = set(extent.relationships)
            eset = set(expected_relationships)
            assert rset == eset


# class TestLinks1(BaseLinks):

#     include = True

#     format = 1


class TestLinks2(BaseLinks):

    include = True

    format = 2
