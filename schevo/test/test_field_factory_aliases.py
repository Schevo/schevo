"""Field factory deprecated name tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import warnings

from schevo.test import BaseTest, DocTest


class TestFieldFactoryDeprecatedNames(BaseTest):

    def test_warnings(self):
        # Create a schema that has a custom field class, and uses it
        # with both styles of field factory names:
        body = """
            class SomeStringThing(F.String):
                pass
            class Foo(E.Entity):
                name = f.some_string_thing()       # Preferred.
                code = f.someStringThing()         # Deprecated.
            """
        # When using the schema, a deprecation warning is given for
        # the field definition that used the camelCase version of the
        # name, which is now deprecated. The line number that the
        # warning is on appears to be line eight above, but since a
        # two-line header is prepended to the body during unit
        # testing, it's actually line 10 where the warning occurs:
        with warnings.catch_warnings(record=True) as w:
            t = DocTest(body)
            assert len(w) == 1
            assert w[-1].category is DeprecationWarning
            assert w[-1].lineno == 8
            assert (
                "'someStringThing' is a deprecated field definition name."
                in str(w[-1].message)
                )
