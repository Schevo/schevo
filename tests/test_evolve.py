"""Schema evolution tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.constant import UNASSIGNED
from schevo import error
from schevo import test


BOILERPLATE = """
from schevo.schema import *
schevo.schema.prep(locals())
"""


def fix(schema):
    """Reformat schema source and prepend boilerplate."""
    return BOILERPLATE + dedent(schema)


class TestEvolveSameVersion(test.CreatesDatabase):
    """Test evolution of schema within the same version, as occurs
    during app development."""

    def test_same_schema(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = schema1
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        self.reopen()
        db._sync(schema2)
        assert db.Foo[foo_oid].bar == 'baz'

    def test_same_schema_initial(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            _initial = [
                ('baz', ),
                ]
        """)
        schema2 = schema1
        db._sync(schema1)
        assert len(db.Foo) == 1
        self.reopen()
        db._sync(schema2)
        assert len(db.Foo) == 1
        assert db.Foo.findone(bar='baz')

    def test_add_field(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        self.reopen()
        db._sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        assert foo.baz is UNASSIGNED
        tx = foo.t.update(baz=5)
        db.execute(tx)
        assert foo.baz == 5

    def test_add_entity_field(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            name = f.unicode()
        """)
        schema2 = fix("""\
        class Bar(E.Entity):
            name = f.unicode()
        class Foo(E.Entity):
            name = f.unicode()
            bar = f.entity('Bar')
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(name=u'baz'))
        foo_oid = foo.sys.oid
        self.reopen()
        db._sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.name == u'baz'
        assert foo.bar is UNASSIGNED
        bar = db.execute(db.Bar.t.create(name=u'bof'))
        tx = foo.t.update(bar=bar)
        db.execute(tx)
        assert foo.bar == bar

    def test_remove_field(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=12))
        foo_oid = foo.sys.oid
        self.reopen()
        db._sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        self.assertRaises(AttributeError, getattr, foo, 'baz')
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.bar = 'bof'
        db.execute(tx)
        assert foo.bar == 'bof'

    def test_remove_entity_field_then_readd(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema3 = fix("""\
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        db._sync(schema1)
        bar = db.execute(db.Bar.t.create(bof='fob'))
        foo = db.execute(db.Foo.t.create(bar=bar, baz=12))
        foo_oid = foo.sys.oid
        bar_oid = bar.sys.oid
        assert bar.sys.count() == 1
        # Evolve.
        self.reopen()
        db._sync(schema2)
        foo = db.Foo[foo_oid]
        bar = db.Bar[bar_oid]
        assert foo.baz == 12
        self.assertRaises(AttributeError, getattr, foo, 'bar')
        assert bar.sys.count() == 0
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.baz = 5
        db.execute(tx)
        assert foo.baz == 5
        # Evolve.
        self.reopen()
        db._sync(schema3)
        foo = db.Foo[foo_oid]
        bar = db.Bar[bar_oid]
        assert foo.bar is UNASSIGNED
        assert foo.baz == 5
        tx = foo.t.update()
        tx.bar = bar
        db.execute(tx)
        assert foo.bar == bar
        assert bar.sys.count() == 1

    def test_add_extent(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        db._sync(schema1)
        self.reopen()
        db._sync(schema2)
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        db._sync(schema1)
        self.reopen()
        db._sync(schema2)
        assert db.extent_names() == ['Foo']

    def test_remove_extent_restricted(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bof(E.Entity):
            baz = f.integer()
        """)
        db._sync(schema1)
        self.reopen()
        self.assertRaises(error.ExtentDoesNotExist, db._sync, schema2)
        assert db.schema_source == schema1
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent_readd_extent(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""\
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema3 = fix("""\
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        db._sync(schema1)
        bar = db.execute(db.Bar.t.create(baz=5))
        foo = db.execute(db.Foo.t.create(bar=bar))
        assert bar.sys.count() == 1
        bar_oid = bar.sys.oid
        self.reopen()
        db._sync(schema2)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        self.reopen()
        db._sync(schema3)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        assert len(db.Foo) == 0

    def test_add_key(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        self.reopen()
        db._sync(schema2)
        tx = db.Foo.t.create(bar='baz')
        self.assertRaises(error.KeyCollision, db.execute, tx)

    def test_add_key_duplicates_exist(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo = db.execute(db.Foo.t.create(bar='baz'))
        self.reopen()
        self.assertRaises(error.KeyCollision, db._sync, schema2)
        assert db.schema_source == schema1

    def test_remove_key(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(bar)
            _key(baz)
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(baz)
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=5))
        self.reopen()
        db._sync(schema2)
        # The (bar) key no longer exists, so we can now dupliate
        # values on that field.
        foo = db.execute(db.Foo.t.create(bar='baz', baz=3))
        assert len(db.Foo) == 2
        # The (baz) key still exists.
        tx = db.Foo.t.create(bar='foo', baz=3)
        self.assertRaises(error.KeyCollision, db.execute, tx)

    def test_change_field_type(self):
        schema1 = fix("""\
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""\
        class Foo(E.Entity):
            bar = f.integer()
        """)
        db._sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo2 = db.execute(db.Foo.t.create(bar='12'))
        ## skip('How should we handle this?')
        return


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
