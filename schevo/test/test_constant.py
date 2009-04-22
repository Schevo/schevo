"""Schevo constants unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import unittest

from schevo.constant import UNASSIGNED
from schevo.label import label
from schevo.test import BaseTest, raises


class TestConstant(BaseTest):

    def test_UNASSIGNED(self):
        assert label(UNASSIGNED) == '<UNASSIGNED>'
        assert len(UNASSIGNED) == 0
        assert str(UNASSIGNED) == ''
        assert raises(TypeError, UNASSIGNED)
