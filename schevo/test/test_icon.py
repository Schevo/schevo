"""Schevo filesystem icon loader tests.

For copyright, license, and warranty, see bottom of file.
"""

import os
import unittest

from schevo.test import CreatesSchema
from schevo.icon import DEFAULT_PNG
import schevo.icon

testpath = os.path.dirname(__file__)
iconpath = os.path.dirname(testpath)

TEST_ICONS = os.path.join(testpath, 'icons')
USER_PNG = file(os.path.join(TEST_ICONS, 'db.User.png'), 'rb').read()
SPROCKET_PNG = file(os.path.join(TEST_ICONS, 'db.Sprocket.png'), 'rb').read()
CONFIGURE_PNG = file(os.path.join(TEST_ICONS, 'configure.png'), 'rb').read()


class BaseFsIconMap(CreatesSchema):

    body = '''

    class SchevoIcon(E.Entity):

        _hidden = True

        name = f.string()
        data = f.image()

        _key(name)
    '''

    def setUp(self):
        CreatesSchema.setUp(self)
        # Install the filesystem icon plugin to the database.
        schevo.icon.install(self.db, TEST_ICONS)

    def test_icon_by_name(self):
        configure_png = db._icon('configure')
        assert configure_png == CONFIGURE_PNG

    def test_file_does_not_exist(self):
        loopsegment_png = db._icon('db.LoopSegment')
        assert loopsegment_png == DEFAULT_PNG


class TestFsIconMap1(BaseFsIconMap):

    include = True

    format = 1


class TestFsIconMap2(BaseFsIconMap):

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
