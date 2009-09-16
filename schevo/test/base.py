"""Test base classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import inspect
import os
import sys

from schevo import database
from schevo.lib import module
import schevo.schema
import schevo.trace
from schevo.script.path import package_path
from schevo.url import make_url

from textwrap import dedent
from StringIO import StringIO


PREAMBLE = """\
from schevo.schema import *
schevo.schema.prep(locals())
"""

DEFAULT_BACKEND_URL = 'schevostore:///:memory:'
DEFAULT_FORMAT = 2


def raises(exc_type, fn, *args, **kw):
    """Raise an `AssertionError` if the call doesn't raise the
    expected error.

    - `exc_type`: The type of exception that the call is expected to
      raise.
    - `fn(*args, **kw)`: The call to test.
    """
    try:
        fn(*args, **kw)
    except Exception, e:
        if not isinstance(e, exc_type):
            raise AssertionError(
                'expected %r, got %r %r %s' % (exc_type, type(e), e, e))
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


class BaseTest(object):
    """Base class for all tests.

    Previously used to provide *py.test* compatibility.  We now use
    only *nose* for testing, but we keep this class around in case we
    wish to extend all test classes in the future.
    """


class CreatesDatabase(BaseTest):
    """Provides database creation, opening, and closing for each test
    case in the class.

    Expects the backend specified in `backend_name` to have a
    `TestMethods_CreatesDatabase` attribute that contains the
    following callables:

    - `backend_base_open(test_object, suffix, schema_source, schema_version)`
    - `backend_close(test_object, suffix='')`
    - `backend_reopen_finish(test_object, suffix)`
    - `backend_reopen_save_state(test_object, suffix)`
    - `backend_convert_format(test_object, suffix, format)`
    """

    backend_url = DEFAULT_BACKEND_URL
    format = DEFAULT_FORMAT

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

    @property
    def backend_class(self):
        """Return the appropriate backend class for this type of test."""
        return make_url(
            self.backend_url).backend_class().TestMethods_CreatesDatabase

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
        """Close the database.

        - `suffix`: The suffix to append to the name of variables; for
          testing multiple databases open at once.
        """
        db_name = 'db' + suffix
        self.backend_class.backend_close(self, suffix)
        delattr(self, db_name)
        # Also delete the global set in the class's module.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        if hasattr(mod, db_name):
            delattr(mod, db_name)
        self.suffixes.remove(suffix)

    def evolve(self, schema_source, version):
        """Evolve the database to a new schema source and version."""
        db = self.reopen()
        database.evolve(db, schema_source, version)

    def _base_open(self, suffix='', schema_source=None, schema_version=None):
        """Open and return the database, setting `self.db` if no
        suffix is given.

        May be called more than once in a series of `open`/`close`
        calls.
        """
        # Create database.
        db = self.backend_class.backend_base_open(
            self, suffix, schema_source, schema_version)
        db_name = 'db' + suffix
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

        - `suffix`: The suffix to append to the name of variables; for
          testing multiple databases open at once.
        - `format`: The format to convert to before reopening.
        """
        db = getattr(self, 'db' + suffix)
        self.backend_class.backend_reopen_save_state(self, suffix)
        self.close(suffix)
        if format is not None:
            self.backend_class.backend_convert_format(self, suffix, format)
        db = self._open(suffix)
        self.backend_class.backend_reopen_finish(self, suffix)
        return db

    def sync(self, schema_source):
        db = self.reopen()
        db._sync(schema_source)


class CreatesSchema(CreatesDatabase):
    """Much like `CreatesDatabase`, but automatically synchronizes the
    database with a schema.

    This is the most common base class for Schevo tests.

    By associating a fixed schema with a test class, it also
    facilitates the use of a cache to speed up the execution of unit
    tests.

    Expects the backend specified in `backend_name` to have a
    `TestMethods_CreatesDatabase` attribute that contains the
    following callables:

    - `backend_base_open(test_object, suffix, schema_source, schema_version)`
    - `backend_close(test_object, suffix='')`
    - `backend_convert_format(test_object, suffix, format)`
    - `backend_reopen_finish(test_object, suffix)`
    - `backend_reopen_save_state(test_object, suffix)`
    - `backend_open(test_object, suffix, schema)`
    """

    # If non-empty, use this as the schema body, and prepend the standard
    # schema preamble to it.
    body = ''

    # If body is not empty, use this as the entire schema body, unchanged.
    schema = ''

    # True if database caching should be used to speed up unit tests that use
    # the same schema. False if a completely new database should be created for
    # each test case.
    _use_db_cache = True

    @property
    def backend_class(self):
        return make_url(
            self.backend_url).backend_class().TestMethods_CreatesSchema

    def _open(self, suffix=''):
        format = self.format
        body_name = 'body' + suffix
        body = getattr(self, body_name, '')
        schema_name = 'schema' + suffix
        schema = getattr(self, schema_name, '')
        if body:
            schema = PREAMBLE + dedent(body)
            setattr(self, schema_name, schema)
        db_name = 'db' + suffix
        ex_name = 'ex' + suffix
        db = self.backend_class.backend_open(self, suffix, schema)
        # Also set the module-level global.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        setattr(mod, db_name, db)
        setattr(mod, ex_name, db.execute)
        self.suffixes.add(suffix)
        return db

    def open(self, suffix=''):
        db = self._open(suffix)
        db.populate('unittest')
        return db


class EvolvesSchemata(CreatesDatabase):
    """Much like `CreatesSchema`, but automatically evolves a database
    to a specific schema version out of several available schemata.

    Expects the backend specified in `backend_name` to have a
    `TestMethods_CreatesDatabase` attribute that contains the
    following callables:

    - `backend_base_open(test_object, suffix, schema_source, schema_version)`
    - `backend_close(test_object, suffix='')`
    - `backend_convert_format(test_object, suffix, format)`
    - `backend_reopen_finish(test_object, suffix)`
    - `backend_reopen_save_state(test_object, suffix)`
    - `backend_open(test_object)`
    """

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
        CreatesDatabase.__init__(self)
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

    @property
    def backend_class(self):
        return make_url(
            self.backend_url).backend_class().TestMethods_EvolvesSchemata

    def _open(self):
        db = self.backend_class.backend_open(self)
        # Also set the module-level global.
        modname = self.__class__.__module__
        mod = sys.modules[modname]
        mod.db = db
        mod.ex = db.execute
        self.suffixes.add('')
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
    """Doctest-helping test class with intra-version evolution support
    only.  Uses the schevostore backend.

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

    Use the `schema` argument along with the `schevo.schema` tools to
    read a schema from disk::

      >>> from schevo.schema import read
      >>> schema = read('schevo.test.testschema_prefix_good', 1)
      >>> t = DocTest(schema=schema)
      >>> t.db.extent_names()
      ['Bar']
      >>> t.done()
    """

    body = ''

    def __init__(self, body=None, schema=None, format=None):
        CreatesSchema.__init__(self)
        if not (body or schema):
            body = self.body
            schema = self.schema
        if body:
            self.body = body
            self.schema = None
        elif schema:
            self.body = None
            self.schema = schema
        else:
            raise ValueError("Either 'body' or 'schema' must be specified.")
        self.format = format
        self.setUp()

    def done(self):
        """Test case is done; free up resources."""
        self.tearDown()

    def update(self, body=None, schema=None):
        """Update database with new schema, keeping same schema version."""
        if body:
            self.body = body
            self.schema = PREAMBLE + dedent(body)
        elif filename:
            self.schema = schema
            self.body = schema.replace(PREAMBLE, '')
        else:
            raise ValueError("Either 'body' or 'filename' must be specified.")
        self.sync(self.schema)


class DocTestEvolve(EvolvesSchemata):
    """Doctest-helping test class with inter-version evolution support.
    Uses the schevostore backend.

    Specify a location to read schemata from, a version to start from,
    and optionally whether or not to skip evolution (default is True).

    Note that for these doctests, we use the `schevo.test.test_evolve`
    schema, since it has a deliberate design flaw that allows us to
    detect whether or not evolution from version 1 was used.

    ::

      >>> t = DocTestEvolve('schevo.test.testschema_evolve', 2)
      >>> sorted(foo.name for foo in t.db.Foo)
      [u'four', u'one', u'three', u'two']
      >>> t.done()

    Another example, loading version 1::

      >>> t = DocTestEvolve('schevo.test.testschema_evolve', 1)
      >>> sorted(foo.name for foo in t.db.Foo)
      [u'one', u'three', u'two']
      >>> t.done()

    An example, loading version 2 by evolving from version 1::

      >>> t = DocTestEvolve('schevo.test.testschema_evolve', 2, False)
      >>> sorted(foo.name for foo in t.db.Foo)
      [u'five', u'one', u'three', u'two']
      >>> t.done()
    """

    def __init__(self, schemata, version, skip_evolution=True):
        self.schemata = schemata
        self.schema_version = version
        self.skip_evolution = skip_evolution
        EvolvesSchemata.__init__(self)
        self.setUp()

    def done(self):
        """Test case is done; free up resources."""
        self.tearDown()


class ComparesDatabases(object):
    """Database evolution equivalence tester.

    To use, add a test class in your app's unit test suite that
    inherits from `ComparesDatabases`.  Then set the three class-level
    attributes `schemata`, `max_version` (optional), and
    `expected_failure` (optional, rarely used).

    The test makes sure that evolving from version N-1 to N results in
    a database that is functionally equivalent to a database created
    directly at version N.

    It does this for all database versions N starting from version 2
    and ending at the latest version, or `max_version` if specified.

    See Schevo's test_equivalence.py for example usage.
    """

    # The package name of the database schema to use when comparing.
    schemata = ''

    # Maximum version that should be tested, or None to use the
    # maximum version available.
    max_version = None

    # Whether or not to expect at least one comparison to fail.
    expected_failure = False

    def test(self):
        location = self.schemata
        # Keep track of lack of failures.
        failed = False
        # Get the maximum schema version.
        final_version = max(
            schevo.schema.latest_version(location), self.max_version)
        # For schema version N from 2 to maximum,
        for N in xrange(2, final_version + 1):
            # Read schema version N.
            schema_N = schevo.schema.read(location, N)
            # Create a database directly at version N.
            db_direct = database.create(
                'schevostore:///:memory:',
                schema_source=schema_N,
                schema_version=N,
                )
            # Read schema version N - 1.
            schema_N1 = schevo.schema.read(location, N - 1)
            # Create a database at version N - 1.
            db_evolved = database.create(
                'schevostore:///:memory:',
                schema_source=schema_N1,
                schema_version=N - 1,
                )
            # Evolve database to version N.
            database.evolve(db_evolved, schema_N, N)
            # Compare the databases.
            is_equivalent = database.equivalent(db_direct, db_evolved)
            # If failure,
            if not is_equivalent:
                if self.expected_failure:
                    # If failure expected, keep track of failure.
                    failed = True
                else:
                    # If failure not expected, raise an exception.
                    raise Exception(
                        'Database created directly at version %i is not '
                        'the same as database created at version %i then '
                        'evolved to version %i.'
                        % (N, N - 1, N)
                        )
            db_direct.close()
            db_evolved.close()
        # If failure expected, but no failures,
        if self.expected_failure and not failed:
            # Raise an exception.
            raise Exception(
                'Expected databases to be unequal at some point, but '
                'they are all functionally equivalent.'
                )
