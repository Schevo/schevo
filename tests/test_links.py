"""Entity/extent unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.test import CreatesSchema


class TestLinks(CreatesSchema):

    # XXX: Todo: test_links

    body = '''

    class FoxtrotAlpha(E.Entity):
        """Used for testing ``links`` and ``count``."""

        beta = f.integer()
        foxtrot_bravo = f.entity('FoxtrotBravo', required=False)
        foxtrot_any = f.entity('FoxtrotAlpha', 'FoxtrotBravo', 'FoxtrotCharlie',
                               required=False)

        _key(beta)

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
    '''

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
            assert entity.sys.count(*call_args) == expected_count

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
