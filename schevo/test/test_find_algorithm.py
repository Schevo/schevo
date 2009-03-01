"""db.find algorithm unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.test import EvolvesSchemata


class BaseFindAlgorithm(EvolvesSchemata):

    schemata = [
        dedent("""
        from schevo.schema import *
        schevo.schema.prep(locals())

        class Foo(E.Entity):

            bar = f.integer()

            _key(bar)

            _initial = [
                (1, ),
                ]
        """),
        dedent("""
        from schevo.schema import *
        schevo.schema.prep(locals())

        class Foo(E.Entity):

            bar = f.integer()

            # All of the 'baz' field values, since they are not
            # indexed and have not been set, are not actually stored
            # in the database and thus are treated as UNASSIGNED.
            baz = f.string()

            _key(bar)
        """),
        ]

    schema_version = 2

    skip_evolution = False

    def test_find_brute_force_treats_missing_field_values_as_UNASSIGNED(self):
        # This will fail if the database engine doesn't treat missing
        # field values as UNASSIGNED.
        assert db.Foo.find(baz='abc') == []


class TestFindAlgorithm1(BaseFindAlgorithm):

    include = True

    format = 1


class TestFindAlgorithm2(BaseFindAlgorithm):

    include = True

    format = 2


# Copyright (C) 2001-2009 ElevenCraft Inc.
#
# Schevo
# http://schevo.org/
#
# ElevenCraft Inc.
# Bellingham, WA
# http://11craft.com/
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
