"""Index spec unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.test import CreatesSchema, PREAMBLE


class BaseIndexSpecs(CreatesSchema):

    bodies = [
        '''
        class Foo(E.Entity):
            bar = f.datetime(required=False)
            baz = f.datetime(required=False)
        ''',
        '''
        class Foo(E.Entity):
            bar = f.datetime(required=False)
            baz = f.datetime(required=False)
            _index(bar)
        ''',
        '''
        class Foo(E.Entity):
            bar = f.datetime(required=False)
            baz = f.datetime(required=False)
            _index(bar, baz)
        ''',
        ]

    body = bodies[0]

    def test_no_key_collisions(self):
        # Create several items.
        foo1 = ex(db.Foo.t.create())
        foo2 = ex(db.Foo.t.create())
        foo3 = ex(db.Foo.t.create())
        # Evolve to schema 2.
        self.evolve(PREAMBLE + dedent(self.bodies[1]), 2)
        # Evolve to schema 3.
        # --> This is where problems happen <--
        self.evolve(PREAMBLE + dedent(self.bodies[2]), 3)


class TestIndexSpecs1(BaseIndexSpecs):

    include = True

    format = 1


class TestIndexSpecs2(BaseIndexSpecs):

    include = True

    format = 2


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
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
