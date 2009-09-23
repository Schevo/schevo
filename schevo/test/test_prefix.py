"""Schema prefix tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo import error
from schevo.schema import schema_filename_prefix
from schevo.test import BaseTest, EvolvesSchemata, raises


# Make sure we can import the testschema_prefix_* packages.
import os
import sys
tests_path = os.path.dirname(os.path.abspath(__file__))
if tests_path not in sys.path:
    sys.path.insert(0, tests_path)


class BaseAlternatePrefixGood(EvolvesSchemata):

    schemata = 'testschema_prefix_good'

    schema_version = 1

    def test(self):
        assert db.extent_names() == ['Bar']


# class TestAlternatePrefixGood1(BaseAlternatePrefixGood):

#     include = True

#     format = 1


class TestAlternatePrefixGood2(BaseAlternatePrefixGood):

    include = True

    format = 2


class TestSchemaFilenamePrefix(BaseTest):

    def test_good(self):
        expected = 'foo'
        prefix = schema_filename_prefix('testschema_prefix_good')
        assert prefix == expected

    def test_bad1(self):
        expected_error = error.SchemaFileIOError
        call = schema_filename_prefix, 'testschema_prefix_bad1'
        assert raises(expected_error, *call)

    def test_bad2(self):
        expected_error = error.SchemaFileIOError
        call = schema_filename_prefix, 'testschema_prefix_bad2'
        assert raises(expected_error, *call)
