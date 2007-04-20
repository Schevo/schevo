"""Test base classes.

For copyright, license, and warranty, see bottom of file.
"""

import os
import sys

from schevo import database
from schevo.lib import module
import schevo.schema
import schevo.trace
from schevo.script.path import package_path

from textwrap import dedent
from StringIO import StringIO


PREAMBLE = """\
from schevo.schema import *
schevo.schema.prep(locals())
"""


def raises(exc_type, fn, *args, **kw):
    try:
        fn(*args, **kw)
    except Exception, e:
        assert isinstance(e, exc_type)
        return True
    else:
        raise AssertionError('Call did not raise an exception')


def tron(monitor_level=3):
    """Turn trace monitoring on.

    Automatically injected into global namespace of tests when run.
    """
    schevo.trace.monitor_level = monitor_level


def troff():
    """Turn trace monitoring off.

    Automatically injected into global namespace of tests when run.
    """
    schevo.trace.monitor_level = 0


_db_cache = {
    # (format, version, evolve_skipped, schema_source, suffix): 
    #   (db, fp, connection),
    }
_cached_dbs = set(
    # db,
    )


class BaseTest(object):

    # XXX py.test support

    def setup_method(self, method):
        return self.setUp()

    def teardown_method(self, method):
        return self.tearDown()

    def assertRaises(self, *args, **kw):
        return raises(*args, **kw)

    # /XXX

    def setUp(self):
        pass

    def tearDown(self):
        pass


class CreatesDatabase(BaseTest):
    """A mixin to provide test directory and Durus database creation
    and deletion per-method."""

    format = None

    def setUp(self):
        self.suffixes = set()
        self.open()
        # Also set the global 'tron' and 'troff' variables in our
        # class's module namespace for convenience.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        mod.tron = tron
        mod.troff = troff

    def tearDown(self):
        for suffix in list(self.suffixes):
            self.close(suffix)

    def check_entities(self, extent):
        """Check string, unicode, and programmer representations of entities
        for blank strings or uncaught exceptions.

        - `extent`: The extent in which to check each entity.

        NOTE: This uses brute force to do so, and will be time consuming with
        large extents.
        """
        for entity in extent:
            assert repr(entity)
            assert str(entity)
            assert unicode(entity)

    def close(self, suffix=''):
        """Close the database."""
        db_name = 'db' + suffix
        db = getattr(self, db_name)
        if db not in _cached_dbs:
            db.close()
        delattr(self, db_name)
        delattr(self, 'fp' + suffix)
        delattr(self, 'connection' + suffix)
        # Also delete the global set in the class's module.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        delattr(mod, db_name)
        self.suffixes.remove(suffix)

    def convert_format(self, suffix, format):
        # Get the contents of the database from the fpv attribute.
        contents = self.db_contents(suffix)
        # Turn it into a fresh StringIO.
        fp = StringIO(contents)
        # Convert it to the requested format.
        database.convert_format(fp, format)
        # Turn it back into a fpv attribute.
        setattr(self, 'fpv' + suffix, fp.getvalue())

    def db_contents(self, suffix=''):
        value = ''
        if hasattr(self, 'fpv' + suffix):
            value = getattr(self, 'fpv' + suffix)
        return value

    def evolve(self, schema_source, version):
        db = self.reopen()
        database.evolve(db, schema_source, version)

    def _base_open(self, suffix='', schema_source=None, schema_version=None):
        """Open and return the database, setting self.db if no suffix
        is given.

        May be called more than once in a series of open/close calls.
        """
        # Create database.
        contents = self.db_contents(suffix)
        fp = StringIO(contents)
        db = database.open(
            fp=fp, schema_source=schema_source, schema_version=schema_version,
            format_for_new=self.format)
        db_name = 'db' + suffix
        setattr(self, db_name, db)
        setattr(self, 'fp' + suffix, fp)
        setattr(self, 'connection' + suffix, db.connection)
        self.suffixes.add(suffix)
        # Also set the global 'db...' and 'ex' variables in our
        # class's module namespace for convenience.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        setattr(mod, db_name, db)
        setattr(mod, 'ex', db.execute)
        return db

    def _open(self, suffix='', schema_source=None):
        return self._base_open(suffix, schema_source)

    def open(self):
        """Open the database and perform first-time operations, and
        return the database.

        Must be called only once per test method.
        """
        return self._open()

    def reopen(self, suffix='', format=None):
        """Close and reopen self.db and return its new incarnation.

        - `suffix`: The suffix to append to the name of variables; for testing
          multiple databases open at once.
        - `format`: The format to convert to before reopening.
        """
        setattr(self, 'fpv' + suffix, getattr(self, 'fp' + suffix).getvalue())
        self.close(suffix)
        if format is not None:
            self.convert_format(suffix, format)
        db = self._open(suffix)
        delattr(self, 'fpv' + suffix)
        return db

    def sync(self, schema_source):
        db = self.reopen()
        db._sync(schema_source)


class CreatesSchema(CreatesDatabase):
    """A mixin to provide test dir, Durus database, and schema
    creation/deletion per-method."""

    # If non-empty, use this as the schema body, and prepend the standard
    # schema preamble to it.
    body = ''

    # If body is not empty, use this as the entire schema body, unchanged.
    schema = ''

    # True if database caching should be used to speed up unit tests that use
    # the same schema. False if a completely new database should be created for
    # each test case.
    _use_db_cache = True

    def _open(self, suffix=''):
        format = self.format
        if self.body:
            schema = self.schema = PREAMBLE + dedent(self.body)
        else:
            schema = self.schema
        use_db_cache = self._use_db_cache
        db_name = 'db' + suffix
        ex_name = 'ex' + suffix
        fpv_name = 'fpv' + suffix
        cache_key = (format, 1, None, schema, suffix)
        if (use_db_cache
            and cache_key in _db_cache
            and not hasattr(self, fpv_name)
            ):
            db, fp, connection = _db_cache[cache_key]
            setattr(self, 'fp' + suffix, fp)
            setattr(self, 'connection' + suffix, connection)
            if not hasattr(self, db_name):
                db._reset_all()
            setattr(self, db_name, db)
        else:
            # Forget existing modules.
            for m in module.MODULES:
                module.forget(m)
            db = self._base_open(suffix, self.schema)
            if use_db_cache:
                fp = getattr(self, 'fp' + suffix)
                connection = getattr(self, 'connection' + suffix)
                cache_key = (format, 1, None, schema, suffix)
                db_info = (db, fp, connection)
                _db_cache[cache_key] = db_info
                _cached_dbs.add(db)
        # Also set the module-level global.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        setattr(mod, db_name, db)
        setattr(mod, ex_name, db.execute)
        self.suffixes.add(suffix)
        return db

    def open(self):
        db = self._open()
        db.populate('unittest')
        return db


class EvolvesSchemata(CreatesDatabase):

    # List of schema source strings, or a string containing the name of a
    # package to load schemata from.  Must be explicitly set.
    schemata = []

    # Version number of schema to evolve to, or to open from if skip_evolution
    # is True.  Must be explicitly set.
    schema_version = None

    # Sample data declarations to append to the last schema.
    sample_data = ''

    # False if database should start at version 1; True if database should
    # start at the most recent version in self.schemata.  Please remember to
    # include an evolution comparison test in your application's test suite
    # ensure that evolving from version 1 to version X results in the same
    # database as starting directly at version X.
    skip_evolution = True

    # True if database caching should be used to speed up unit tests that use
    # the same schema. False if a completely new database should be created for
    # each test case.
    _use_db_cache = True

    def __init__(self):
        super(EvolvesSchemata, self).__init__()
        schema_version = self.schema_version
        if schema_version is None:
            raise ValueError('schema_version must be set.')
        schemata = self.schemata
        if isinstance(schemata, str):
            # Load schemata source from a package.
            schemata = self.schemata_from_package(schemata, schema_version)
        else:
            # Make a copy so we don't munge the original.
            schemata = schemata[:]
        # Trim to desired version.
        schemata = schemata[:schema_version]
        if len(schemata) != schema_version:
            raise ValueError(
                'schema_version exceeds maximum version available.')
        # Append sample data to end of last version, adding a newline in case
        # the schema doesn't end in one.
        schemata[-1] += '\n' + dedent(self.sample_data)
        # Attach the new schemata list to the instance.
        self.schemata = schemata

    def _open(self, suffix=''):
        format = self.format
        use_db_cache = self._use_db_cache
        db_name = 'db' + suffix
        ex_name = 'ex' + suffix
        fpv_name = 'fpv' + suffix
        schema = self.schemata[-1]
        version = self.schema_version
        skip_evolution = self.skip_evolution
        cache_key = (format, version, skip_evolution, schema, suffix)
        if (use_db_cache
            and cache_key in _db_cache
            and not hasattr(self, fpv_name)
            ):
            db, fp, connection = _db_cache[cache_key]
            setattr(self, 'fp' + suffix, fp)
            setattr(self, 'connection' + suffix, connection)
            if not hasattr(self, db_name):
                db._reset_all()
            setattr(self, db_name, db)
        else:
            # Forget existing modules.
            for m in module.MODULES:
                module.forget(m)
            if not skip_evolution:
                # Open database with version 1.
                db = self._base_open(suffix, self.schemata[0])
                # Evolve to latest.
                for i in xrange(1, len(self.schemata)):
                    schema_source = self.schemata[i]
                    database.evolve(db, schema_source, version=i+1)
            else:
                # Open database with target version.
                db = self._base_open(suffix, schema, schema_version=version)
            if use_db_cache:
                fp = getattr(self, 'fp' + suffix)
                connection = getattr(self, 'connection' + suffix)
                _db_cache[cache_key] = (db, fp, connection)
                _cached_dbs.add(db)
        # Also set the module-level global.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        setattr(mod, db_name, db)
        setattr(mod, ex_name, db.execute)
        self.suffixes.add(suffix)
        return db

    def open(self):
        db = self._open()
        db.populate('unittest')
        return db

    @staticmethod
    def schemata_from_package(pkg_name, final_version):
        schemata = []
        schema_path = package_path(pkg_name)
        version = 0
        while True:
            if version == final_version:
                break
            version += 1
            source = schevo.schema.read(schema_path, version=version)
            schemata.append(source)
        return schemata


class DocTest(CreatesSchema):
    """Doctest-helping test class.

    Call directly to override body for one test::

      >>> from schevo.test import DocTest
      >>> t = DocTest('''
      ...     class Foo(E.Entity):
      ...         bar = f.integer()
      ...     ''')
      >>> t.db.extent_names()
      ['Foo']

    Call `done` method at end of test case::

      >>> t.done()

    Subclass to override body for several tests::

      >>> class test(DocTest):
      ...     body = '''
      ...     class Foo(E.Entity):
      ...         bar = f.integer()
      ...     '''
      >>> t = test()
      >>> t.db.extent_names()
      ['Foo']
      >>> t.done()
    """

    body = ''

    def __init__(self, body=None, format=None):
        super(DocTest, self).__init__()
        if body:
            self.body = body
        self.format = format
        self.setUp()

    def done(self):
        """Test case is done; free up resources."""
        self.tearDown()

    def update(self, body):
        """Update database with new schema, keeping same schema version."""
        self.body = body
        schema_source = PREAMBLE + dedent(self.body)
        self.sync(schema_source)


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
