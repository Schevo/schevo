"""Schema prefix tests.

For copyright, license, and warranty, see bottom of file.
"""

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


class TestAlternatePrefixGood1(BaseAlternatePrefixGood):

    include = True

    format = 1


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
