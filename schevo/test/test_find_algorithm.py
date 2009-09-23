"""db.find algorithm unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
        assert db.Foo.find(db.Foo.f.baz == 'abc') == []


# class TestFindAlgorithm1(BaseFindAlgorithm):

#     include = True

#     format = 1


class TestFindAlgorithm2(BaseFindAlgorithm):

    include = True

    format = 2
