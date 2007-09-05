"""Schema evolution tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.test import CreatesDatabase, EvolvesSchemata, raises


# Make sure we can import the testschema_evolve1 package.
import os
import sys
tests_path = os.path.dirname(os.path.abspath(__file__))
if tests_path not in sys.path:
    sys.path.insert(0, tests_path)


BOILERPLATE = """
from schevo.schema import *
schevo.schema.prep(locals())
"""


def fix(schema):
    """Reformat schema source and prepend boilerplate."""
    return BOILERPLATE + dedent(schema)


class BaseEvolveIntraVersion(CreatesDatabase):
    """Test evolution of schema within the same version, as occurs
    during app development."""

    def test_same_schema(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = schema1
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        self.sync(schema2)
        assert db.Foo[foo_oid].bar == 'baz'

    def test_same_schema_initial(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _initial = [
                ('baz', ),
                ]
        """)
        schema2 = schema1
        self.sync(schema1)
        assert len(db.Foo) == 1
        self.sync(schema2)
        assert len(db.Foo) == 1
        assert db.Foo.findone(bar='baz')

    def test_add_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        self.sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        assert foo.baz is UNASSIGNED
        tx = foo.t.update(baz=5)
        db.execute(tx)
        assert foo.baz == 5

    def test_add_entity_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            name = f.unicode()
        """)
        schema2 = fix("""
        class Bar(E.Entity):
            name = f.unicode()
        class Foo(E.Entity):
            name = f.unicode()
            bar = f.entity('Bar')
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(name=u'baz'))
        foo_oid = foo.sys.oid
        self.sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.name == u'baz'
        assert foo.bar is UNASSIGNED
        bar = db.execute(db.Bar.t.create(name=u'bof'))
        tx = foo.t.update(bar=bar)
        db.execute(tx)
        assert foo.bar == bar

    def test_remove_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=12))
        foo_oid = foo.sys.oid
        self.sync(schema2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        raises(AttributeError, getattr, foo, 'baz')
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.bar = 'bof'
        db.execute(tx)
        assert foo.bar == 'bof'

    def test_remove_entity_field_then_readd(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema3 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        self.sync(schema1)
        bar = db.execute(db.Bar.t.create(bof='fob'))
        foo = db.execute(db.Foo.t.create(bar=bar, baz=12))
        foo_oid = foo.sys.oid
        bar_oid = bar.sys.oid
        assert bar.sys.count() == 1
        # Evolve.
        self.sync(schema2)
        foo = db.Foo[foo_oid]
        bar = db.Bar[bar_oid]
        assert foo.baz == 12
        raises(AttributeError, getattr, foo, 'bar')
        assert bar.sys.count() == 0
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.baz = 5
        db.execute(tx)
        assert foo.baz == 5
        # Evolve.
        self.sync(schema3)
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
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        self.sync(schema2)
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        self.sync(schema2)
        assert db.extent_names() == ['Foo']

    def test_remove_extent_restricted(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bof(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        raises(error.ExtentDoesNotExist, self.sync, schema2)
        assert db.schema_source == schema1
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent_readd_extent(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema3 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        bar = db.execute(db.Bar.t.create(baz=5))
        foo = db.execute(db.Foo.t.create(bar=bar))
        assert bar.sys.count() == 1
        bar_oid = bar.sys.oid
        self.sync(schema2)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        self.sync(schema3)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        assert len(db.Foo) == 0

    def test_add_key(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        self.sync(schema2)
        tx = db.Foo.t.create(bar='baz')
        raises(error.KeyCollision, db.execute, tx)

    def test_add_key_duplicates_exist(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo = db.execute(db.Foo.t.create(bar='baz'))
        raises(error.KeyCollision, self.sync, schema2)
        assert db.schema_source == schema1

    def test_remove_key(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(bar)
            _key(baz)
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(baz)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=5))
        self.sync(schema2)
        # The (bar) key no longer exists, so we can now dupliate
        # values on that field.
        foo = db.execute(db.Foo.t.create(bar='baz', baz=3))
        assert len(db.Foo) == 2
        # The (baz) key still exists.
        tx = db.Foo.t.create(bar='foo', baz=3)
        raises(error.KeyCollision, db.execute, tx)

    def test_key_to_index(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _index(bar)
        """)
        self.sync(schema1)
        db.execute(db.Foo.t.create(bar='baz'))
        raises(error.KeyCollision, db.execute, db.Foo.t.create(bar='baz'))
        self.sync(schema2)
        db.execute(db.Foo.t.create(bar='baz'))


class BaseEvolveInterVersion(CreatesDatabase):
    """Test evolution of schema from version to version, as occurs
    with upgrading deployed production apps."""

    def test_wrong_version(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = schema1
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        raises(error.DatabaseVersionMismatch, self.evolve, schema2, version=3)
        assert db.version == 1

    def test_same_schema(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        schema2 = schema1
        self.evolve(schema2, version=2)
        assert db.version == 2
        assert db.Foo[foo_oid].bar == 'baz'
        schema3 = schema1
        self.evolve(schema3, version=3)
        assert db.version == 3
        assert db.Foo[foo_oid].bar == 'baz'
        schema4 = schema1
        self.evolve(schema4, version=4)
        assert db.version == 4
        assert db.Foo[foo_oid].bar == 'baz'

    def test_same_schema_initial(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _initial = [
                ('baz', ),
                ]
        """)
        schema2 = schema1
        self.sync(schema1)
        assert len(db.Foo) == 1
        self.evolve(schema2, version=2)
        assert db.version == 2
        assert len(db.Foo) == 1
        assert db.Foo.findone(bar='baz')

    def test_add_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo_oid = foo.sys.oid
        self.evolve(schema2, version=2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        assert foo.baz is UNASSIGNED
        tx = foo.t.update(baz=5)
        db.execute(tx)
        assert foo.baz == 5

    def test_add_entity_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            name = f.unicode()
        """)
        schema2 = fix("""
        class Bar(E.Entity):
            name = f.unicode()
        class Foo(E.Entity):
            name = f.unicode()
            bar = f.entity('Bar')
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(name=u'baz'))
        foo_oid = foo.sys.oid
        self.evolve(schema2, version=2)
        foo = db.Foo[foo_oid]
        assert foo.name == u'baz'
        assert foo.bar is UNASSIGNED
        bar = db.execute(db.Bar.t.create(name=u'bof'))
        tx = foo.t.update(bar=bar)
        db.execute(tx)
        assert foo.bar == bar

    def test_remove_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=12))
        foo_oid = foo.sys.oid
        self.evolve(schema2, version=2)
        foo = db.Foo[foo_oid]
        assert foo.bar == 'baz'
        raises(AttributeError, getattr, foo, 'baz')
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.bar = 'bof'
        db.execute(tx)
        assert foo.bar == 'bof'

    def test_remove_entity_field_then_readd(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        schema3 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
            baz = f.integer()
        class Bar(E.Entity):
            bof = f.string()
        """)
        self.sync(schema1)
        bar = db.execute(db.Bar.t.create(bof='fob'))
        foo = db.execute(db.Foo.t.create(bar=bar, baz=12))
        foo_oid = foo.sys.oid
        bar_oid = bar.sys.oid
        assert bar.sys.count() == 1
        # Evolve.
        self.evolve(schema2, version=2)
        foo = db.Foo[foo_oid]
        bar = db.Bar[bar_oid]
        assert foo.baz == 12
        raises(AttributeError, getattr, foo, 'bar')
        assert bar.sys.count() == 0
        # Attempt to update the entity.
        tx = foo.t.update()
        tx.baz = 5
        db.execute(tx)
        assert foo.baz == 5
        # Evolve.
        self.evolve(schema3, version=3)
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
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        self.evolve(schema2, version=2)
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        self.evolve(schema2, version=2)
        assert db.extent_names() == ['Foo']

    def test_remove_extent_restricted(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.entity(allow='Bar')
        class Bof(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        raises(error.ExtentDoesNotExist,
                          self.evolve, schema2, version=2)
        assert db.schema_source == schema1
        assert db.extent_names() == ['Bar', 'Foo']

    def test_remove_extent_readd_extent(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema2 = fix("""
        class Bar(E.Entity):
            baz = f.integer()
        """)
        schema3 = fix("""
        class Foo(E.Entity):
            bar = f.entity('Bar')
        class Bar(E.Entity):
            baz = f.integer()
        """)
        self.sync(schema1)
        bar = db.execute(db.Bar.t.create(baz=5))
        foo = db.execute(db.Foo.t.create(bar=bar))
        assert bar.sys.count() == 1
        bar_oid = bar.sys.oid
        self.evolve(schema2, version=2)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        self.evolve(schema3, version=3)
        bar = db.Bar[bar_oid]
        assert bar.sys.count() == 0
        assert len(db.Foo) == 0

    def test_add_key(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        self.evolve(schema2, version=2)
        tx = db.Foo.t.create(bar='baz')
        raises(error.KeyCollision, db.execute, tx)

    def test_add_key_duplicates_exist(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            _key(bar)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz'))
        foo = db.execute(db.Foo.t.create(bar='baz'))
        raises(error.KeyCollision, self.evolve, schema2, version=2)
        assert db.schema_source == schema1

    def test_remove_key(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(bar)
            _key(baz)
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            _key(baz)
        """)
        self.sync(schema1)
        foo = db.execute(db.Foo.t.create(bar='baz', baz=5))
        self.evolve(schema2, version=2)
        # The (bar) key no longer exists, so we can now dupliate
        # values on that field.
        foo = db.execute(db.Foo.t.create(bar='baz', baz=3))
        assert len(db.Foo) == 2
        # The (baz) key still exists.
        tx = db.Foo.t.create(bar='foo', baz=3)
        raises(error.KeyCollision, db.execute, tx)

    def test_rename_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            baz = f.string(was='bar')
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        self.evolve(schema2, version=2)
        e1 = db.Foo[e1_oid]
        e2 = db.Foo[e2_oid]
        assert e1.baz == 'abc'
        assert e2.baz == 'def'

    def test_rename_field_broken(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            baz = f.string(was='bof')
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        raises(error.FieldDoesNotExist, self.evolve, schema2, version=2)

    def test_rename_field_evolve_only(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            baz = f.string()

        class Foo(E.Foo):
            _evolve_only = True
            baz = f.string(was='bar')
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        self.evolve(schema2, version=2)
        e1 = db.Foo[e1_oid]
        e2 = db.Foo[e2_oid]
        assert e1.baz == 'abc'
        assert e2.baz == 'def'

    def test_rename_field_reused(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.integer()
            baz = f.string(was='bar')
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        self.evolve(schema2, version=2)
        e1 = db.Foo[e1_oid]
        e2 = db.Foo[e2_oid]
        assert e1.baz == 'abc'
        assert e2.baz == 'def'

    def test_rename_extent(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Baz(E.Entity):
            bar = f.string()
            _was = 'Foo'
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        self.evolve(schema2, version=2)
        e1 = db.Baz[e1_oid]
        e2 = db.Baz[e2_oid]
        assert e1.bar == 'abc'
        assert e2.bar == 'def'
        assert db.extent_names() == ['Baz']

    def test_rename_extent_broken(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Baz(E.Entity):
            bar = f.string()
            _was = 'Bof'
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='abc'))
        e2 = db.execute(db.Foo.t.create(bar='def'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        raises(error.ExtentDoesNotExist, self.evolve, schema2, version=2)

    def test_convert_field(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.integer(required=False)
        class Foo(E.Foo):
            _evolve_only = True
            old_bar = f.string(was='bar')
        def during_evolve(db):
            for foo in db.Foo:
                tx = foo.t.update()
                try:
                    tx.bar = int(tx.old_bar)
                except ValueError:
                    continue
                db.execute(tx)
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='123'))
        e2 = db.execute(db.Foo.t.create(bar='456'))
        e3 = db.execute(db.Foo.t.create(bar='abc'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        e3_oid = e3.sys.oid
        self.evolve(schema2, version=2)
        e1 = db.Foo[e1_oid]
        e2 = db.Foo[e2_oid]
        e3 = db.Foo[e3_oid]
        assert e1.bar == 123
        assert e2.bar == 456
        assert e3.bar is UNASSIGNED
        assert 'old_bar' not in db.Foo.field_spec

    def test_no_commit_on_error(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.integer(required=False)
        # -- Evolution --
        class Foo(E.Foo):
            _evolve_only = True
            old_bar = f.string(was='bar')
        def during_evolve(db):
            for foo in db.Foo:
                tx = foo.t.update()
                tx.bar = int(tx.old_bar)
                db.execute(tx)
        """)
        self.sync(schema1)
        e1 = db.execute(db.Foo.t.create(bar='123'))
        e2 = db.execute(db.Foo.t.create(bar='456'))
        e3 = db.execute(db.Foo.t.create(bar='abc'))
        e1_oid = e1.sys.oid
        e2_oid = e2.sys.oid
        e3_oid = e3.sys.oid
        raises(ValueError, self.evolve, schema2, version=2)
        # Database must be reopened after failed evolution.
        self.reopen()
        assert db.version == 1
        e1 = db.Foo[e1_oid]
        e2 = db.Foo[e2_oid]
        e3 = db.Foo[e3_oid]
        assert e1.bar == '123'
        assert e2.bar == '456'
        assert e3.bar == 'abc'
        assert 'old_bar' not in db.Foo.field_spec

    def test_denormalize(self):
        schema1 = fix("""
        class Person(E.Entity):
            name = f.string()
        class PersonPhoneNumber(E.Entity):
            person = f.entity('Person')
            phone_number = f.entity('PhoneNumber')
        class PhoneNumber(E.Entity):
            number = f.string()
        """)
        self.sync(schema1)
        P, PPN, PN = db.extents()
        p1 = db.execute(P.t.create(name='Joe'))
        p2 = db.execute(P.t.create(name='Jane'))
        p1_oid = p1.sys.oid
        p2_oid = p2.sys.oid
        pn1 = db.execute(PN.t.create(number='555-1234'))
        pn2 = db.execute(PN.t.create(number='555-9876'))
        ppn1 = db.execute(PPN.t.create(person=p1, phone_number=pn1))
        # Person p2 is associated with both phone numbers.
        ppn2 = db.execute(PPN.t.create(person=p2, phone_number=pn1))
        ppn3 = db.execute(PPN.t.create(person=p2, phone_number=pn2))
        # Evolve the database, denormalizing three extents into two.
        schema2 = fix("""
        class Person(E.Entity):
            name = f.string()
        class PhoneNumber(E.Entity):
            person = f.entity('Person')
            number = f.string()
        # -- Evolution --
        class OldPhoneNumber(E.Entity):
            number = f.string()
            _evolve_only = True
            _was = 'PhoneNumber'
        class PersonPhoneNumber(E.Entity):
            person = f.entity('Person')
            phone_number = f.entity('OldPhoneNumber')
            _evolve_only = True
        def during_evolve(db):
            for opn in db.OldPhoneNumber:
                ppns = opn.m.person_phone_numbers()
                for ppn in ppns:
                    db.execute(
                        db.PhoneNumber.t.create(
                            person=ppn.person, number=ppn.phone_number.number))
        """)
        self.evolve(schema2, version=2)
        assert db.extent_names() == ['Person', 'PhoneNumber']
        p1 = db.Person[p1_oid]
        p2 = db.Person[p2_oid]
        # Person 1 should only have one phone number.
        pns = p1.m.phone_numbers()
        assert len(pns) == 1
        assert pns[0].number == '555-1234'
        # Person 2 should have both numbers.
        pns = p2.m.phone_numbers()
        assert len(pns) == 2
        numbers = sorted([pn.number for pn in pns])
        assert numbers == ['555-1234', '555-9876']

    def test_before_during_after(self):
        schema1 = fix("""
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        schema2 = fix("""
        class Foo(E.Entity):
            bar = f.string(required=False)
        class Foo(E.Entity):
            _evolve_only = True
            bar = f.string()
            baz = f.integer(required=False)
        def before_evolve(db):
            assert list(db.Foo.field_spec) == ['bar', 'baz']
            assert db.Foo.field_spec['bar'].required
            assert db.Foo.field_spec['baz'].required
        def during_evolve(db):
            assert list(db.Foo.field_spec) == ['bar', 'baz']
            assert db.Foo.field_spec['bar'].required
            assert not db.Foo.field_spec['baz'].required
        def after_evolve(db):
            assert list(db.Foo.field_spec) == ['bar']
            assert not db.Foo.field_spec['bar'].required
        """)
        self.sync(schema1)
        self.evolve(schema2, version=2)

    def test_on_open(self):
        schema1 = fix("""
        from schevo.lib.optimize import do_not_optimize
        BAR = UNASSIGNED
        @do_not_optimize
        def x_get_bar():
            return BAR
        def on_open(db):
            global BAR
            BAR = 42
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
            bam = f.float()
        """)
        schema2 = fix("""
        from schevo.lib.optimize import do_not_optimize
        BAR = UNASSIGNED
        @do_not_optimize
        def x_get_bar():
            return BAR
        def on_open(db):
            global BAR
            BAR = 43
        class Foo(E.Entity):
            bar = f.string()
            baz = f.integer()
        """)
        schema3 = fix("""
        from schevo.lib.optimize import do_not_optimize
        BAR = UNASSIGNED
        @do_not_optimize
        def x_get_bar():
            return BAR
        def on_open(db):
            global BAR
            BAR = 44
        class Foo(E.Entity):
            bar = f.string()
        """)
        self.sync(schema1)
        # Database must be reopened to trigger on_open() call.
        self.reopen()
        assert db.x.get_bar() == 42
        self.evolve(schema2, version=2)
        assert db.x.get_bar() == 43
        self.evolve(schema3, version=3)
        assert db.x.get_bar() == 44


class BaseEvolvesSchemataNoSkip(EvolvesSchemata):

    schemata = 'testschema_evolve'

    schema_version = 2

    sample_data = '''
        E.Foo._sample_unittest = [
            (u'fob', ),
            ]
        '''

    skip_evolution = False

    def test(self):
        assert db.version == 2
        names = set(foo.name for foo in db.Foo)
        expected = set([u'one', u'two', u'three', u'five', u'fob'])
        assert names == expected


class BaseEvolvesSchemataSkip(EvolvesSchemata):

    schemata = 'testschema_evolve'

    schema_version = 2

    sample_data = '''
        E.Foo._sample_unittest = [
            (u'fob', ),
            ]
        '''

    skip_evolution = True

    def test(self):
        assert db.version == 2
        names = set(foo.name for foo in db.Foo)
        expected = set([u'one', u'two', u'three', u'four', u'fob'])
        assert names == expected


class TestEvolveIntraVersion1(BaseEvolveIntraVersion):

    include = True

    format = 1


class TestEvolveIntraVersion2(BaseEvolveIntraVersion):

    include = True

    format = 2


class TestEvolveInterVersion1(BaseEvolveInterVersion):

    include = True

    format = 1


class TestEvolveInterVersion2(BaseEvolveInterVersion):

    include = True

    format = 2


class TestEvolvesSchemataNoSkip1(BaseEvolvesSchemataNoSkip):

    include = True

    format = 1


class TestEvolvesSchemataNoSkip2(BaseEvolvesSchemataNoSkip):

    include = True

    format = 2


class TestEvolvesSchemataSkip1(BaseEvolvesSchemataSkip):

    include = True

    format = 1


class TestEvolvesSchemataSkip2(BaseEvolvesSchemataSkip):

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
