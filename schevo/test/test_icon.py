"""Schevo filesystem icon loader tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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


# class TestFsIconMap1(BaseFsIconMap):

#     include = True

#     format = 1


class TestFsIconMap2(BaseFsIconMap):

    include = True

    format = 2
