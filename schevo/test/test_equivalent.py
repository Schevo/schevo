"""Database equivalence tests.

NOTE: These do not test against the format 1 database engine, as
schevo.database.equivalent is engine-agnostic and some of these tests
depend on field types that may only be used in format 2 databases."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from textwrap import dedent

from schevo.backend import backends
from schevo.database import equivalent
from schevo.test import CreatesSchema, ComparesDatabases


# Make sure we can import the testschema_equivalent_* packages.
import os
import sys
tests_path = os.path.dirname(os.path.abspath(__file__))
if tests_path not in sys.path:
    sys.path.insert(0, tests_path)


class TestAllEquivalenceGood(ComparesDatabases):

    schemata = 'testschema_equivalent_good'


class TestAllEquivalenceBad(ComparesDatabases):

    schemata = 'testschema_equivalent_bad'
    expected_failure = True


class TestIsEquivalent(CreatesSchema):

    body = '''
        class Foo(E.Entity):
            """Unicode field, with key."""

            name = f.string()

            _key(name)

            _initial_priority = 100

            _initial = [
                (u'one', ),
                (u'two', ),
                (u'three', ),
                ]


        class Far(E.Entity):
            """Integer field, no keys."""

            number = f.integer()

            _initial_priority = 100

            _initial = [
                (1, ),
                (2, ),
                (3, ),
                (3, ),
                (3, ),
                ]


        class Faz(E.Entity):
            """Entity field, no keys."""

            foo = f.entity('Foo')

            _key(foo)

            _initial_priority = 90

            _initial = [
                ((u'one', ), ),
                ((u'two', ), ),
                ((u'three', ), ),
                ]


        class Fiz(E.Entity):
            """Entity list field, no key."""

            fazs = f.entity_list('Faz')

            _initial_priority = 80

            @extentmethod
            def _initial(extent, db):
                db.execute(extent.t.create(fazs=[
                    db.Faz.findone(foo=db.Foo.findone(name=u'three')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'two')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'one')),
                    ]))
                db.execute(extent.t.create(fazs=[
                    db.Faz.findone(foo=db.Foo.findone(name=u'one')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'two')),
                    ]))


        class FobOne(E.Entity):
            """Entity, recursing with FobTwo."""

            fob_two = f.entity('FobTwo', required=False)

            @extentmethod
            def _initial(extent, db):
                fob_one = db.execute(extent.t.create())
                fob_two = db.execute(db.FobTwo.t.create(fob_one=fob_one))
                db.execute(fob_one.t.update(fob_two=fob_two))


        class FobTwo(E.Entity):
            """See FobOne."""

            fob_one = f.entity('FobOne')


        class EveryField(E.Entity):
            """Every built-in non-may_store_entities field."""

            string = f.string(required=False)
            bytes = f.bytes(required=False)
            integer = f.integer(required=False)
            float = f.float(required=False)
            money = f.money(required=False)
            date = f.date(required=False)
            datetime = f.datetime(required=False)
            boolean = f.boolean(required=False)

            _initial = [
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (u'string',
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 'bytes',
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 42,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 42.424242,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 42.42,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 '2005-04-03',
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 '2005-04-03 02:01:00',
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 True,
                 ),
                ]
        '''

    body2 = '''
        class Foo(E.Entity):
            """Unicode field, with key."""

            name = f.string()

            _key(name)

            _initial_priority = 100

            _initial = [
                (u'three', ),
                (u'two', ),
                (u'one', ),
                ]


        class Far(E.Entity):
            """Integer field, no keys."""

            number = f.integer()

            _initial_priority = 100

            _initial = [
                (3, ),
                (3, ),
                (3, ),
                (1, ),
                (2, ),
                ]


        class Faz(E.Entity):
            """Entity field, with key."""

            foo = f.entity('Foo')

            _key(foo)

            _initial_priority = 90

            _initial = [
                ((u'two', ), ),
                ((u'one', ), ),
                ((u'three', ), ),
                ]


        class Fiz(E.Entity):
            """Entity list field, no key."""

            fazs = f.entity_list('Faz')

            _initial_priority = 80

            @extentmethod
            def _initial(extent, db):
                db.execute(extent.t.create(fazs=[
                    db.Faz.findone(foo=db.Foo.findone(name=u'one')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'two')),
                    ]))
                db.execute(extent.t.create(fazs=[
                    db.Faz.findone(foo=db.Foo.findone(name=u'three')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'two')),
                    db.Faz.findone(foo=db.Foo.findone(name=u'one')),
                    ]))


        class FobOne(E.Entity):
            """Entity, recursing with FobTwo."""

            fob_two = f.entity('FobTwo', required=False)

            @extentmethod
            def _initial(extent, db):
                fob_one = db.execute(extent.t.create())
                fob_two = db.execute(db.FobTwo.t.create(fob_one=fob_one))
                db.execute(fob_one.t.update(fob_two=fob_two))


        class FobTwo(E.Entity):
            """See FobOne."""

            fob_one = f.entity('FobOne')


        class EveryField(E.Entity):
            """Every built-in non-may_store_entities field."""

            string = f.string(required=False)
            bytes = f.bytes(required=False)
            integer = f.integer(required=False)
            float = f.float(required=False)
            money = f.money(required=False)
            date = f.date(required=False)
            datetime = f.datetime(required=False)
            boolean = f.boolean(required=False)

            _initial = [
                (u'string',
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 42,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 42.424242,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 'bytes',
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 '2005-04-03 02:01:00',
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 True,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 42.42,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                (UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 UNASSIGNED,
                 '2005-04-03',
                 UNASSIGNED,
                 UNASSIGNED,
                 ),
                ]
        '''

    def test_properly_opened(self):
        self.open('2')
        assert db.schema_source != db2.schema_source

    def test_identical_schema_source_not_required(self):
        self.open('2')
        assert equivalent(db, db2, require_identical_schema_source=False)

    def test_identical_schema_source_required(self):
        self.open('2')
        assert not equivalent(db, db2)


class BaseDataNotEquivalent(CreatesSchema):

    def test(self):
        self.open('2')
        assert not equivalent(db, db2, require_identical_schema_source=False)


class TestDataNotEquivalentString(BaseDataNotEquivalent):

    body = '''
        class Foo(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('one', ),
                ('two', ),
                ('three', ),
                ]
        '''

    body2 = '''
        class Foo(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                ('four', ),
                ('two', ),
                ('one', ),
                ]
        '''


class TestDataNotEquivalentBytes(BaseDataNotEquivalent):

    body = '''
        class Foo(E.Entity):

            thing = f.bytes()

            _key(thing)

            _initial = [
                ('one', ),
                ('two', ),
                ('three', ),
                ]
        '''

    body2 = '''
        class Foo(E.Entity):

            thing = f.bytes()

            _key(thing)

            _initial = [
                ('four', ),
                ('two', ),
                ('one', ),
                ]
        '''


class TestDataNotEquivalentInteger(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):
            """Integer field, no keys."""

            number = f.integer()

            _initial = [
                (1, ),
                (2, ),
                (3, ),
                (3, ),
                (3, ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):
            """Integer field, no keys."""

            number = f.integer()

            _initial = [
                (1, ),
                (2, ),
                (3, ),
                (3, ),
                (4, ),
                ]
        '''


class TestDataNotEquivalentFloat(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):

            number = f.float()

            _initial = [
                (1.1, ),
                (2.2, ),
                (3.3, ),
                (3.3, ),
                (3.3, ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            number = f.float()

            _initial = [
                (1.1, ),
                (2.2, ),
                (3.3, ),
                (3.3, ),
                (4.4, ),
                ]
        '''


class TestDataNotEquivalentMoney(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):

            amount = f.money()

            _initial = [
                (1.11, ),
                (2.22, ),
                (3.33, ),
                (3.33, ),
                (3.33, ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            amount = f.money()

            _initial = [
                (1.11, ),
                (2.22, ),
                (3.33, ),
                (3.33, ),
                (4.44, ),
                ]
        '''


class TestDataNotEquivalentDate(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):
            """Integer field, no keys."""

            date = f.date()

            _initial = [
                ('2001-01-01', ),
                ('2002-02-02', ),
                ('2003-03-03', ),
                ('2003-03-03', ),
                ('2003-03-03', ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            date = f.date()

            _initial = [
                ('2001-01-01', ),
                ('2002-02-02', ),
                ('2003-03-03', ),
                ('2003-03-03', ),
                ('2004-04-04', ),
                ]
        '''


class TestDataNotEquivalentDatetime(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):

            datetime = f.datetime()

            _initial = [
                ('2001-01-01 01:11:11', ),
                ('2002-02-02 02:22:22', ),
                ('2003-03-03 03:33:33', ),
                ('2003-03-03 03:33:33', ),
                ('2003-03-03 03:33:33', ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            datetime = f.datetime()

            _initial = [
                ('2001-01-01 01:11:11', ),
                ('2002-02-02 02:22:22', ),
                ('2003-03-03 03:33:33', ),
                ('2003-03-03 03:33:33', ),
                ('2003-04-04 04:44:44', ),
                ]
        '''


class TestDataNotEquivalentBoolean(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):

            flag = f.boolean()

            _initial = [
                (True, ),
                (False, ),
                (True, ),
                (False, ),
                (True, ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            flag = f.boolean()

            _initial = [
                (True, ),
                (False, ),
                (True, ),
                (False, ),
                (False, ),
                ]
        '''


class TestDataNotEquivalentEntity(BaseDataNotEquivalent):

    body = '''
        class Far(E.Entity):

            faz = f.entity('Faz')

            _initial = [
                ((u"Faz1", ), ),
                ((u"Faz2", ), ),
                ((u"Faz3", ), ),
                ((u"Faz3", ), ),
                ((u"Faz3", ), ),
                ]


        class Faz(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                (u"Faz1", ),
                (u"Faz2", ),
                (u"Faz3", ),
                ]
        '''

    body2 = '''
        class Far(E.Entity):

            faz = f.entity('Faz')

            _initial = [
                ((u"Faz1", ), ),
                ((u"Faz2", ), ),
                ((u"Faz3", ), ),
                ((u"Faz3", ), ),
                ((u"Faz2", ), ),
                ]


        class Faz(E.Entity):

            name = f.string()

            _key(name)

            _initial = [
                (u"Faz2", ),
                (u"Faz3", ),
                (u"Faz1", ),
                ]
        '''
