"""Namespace extention unit tests.

For copyright, license, and warranty, see bottom of file.
"""

import unittest

from schevo.namespace import NamespaceExtension
from schevo.test import BaseTest, raises


class NeWithProperty(NamespaceExtension):

    __slots__ = NamespaceExtension.__slots__

    @property
    def foobar(self):
        return 'foobar'


class TestNamespaceExtension(BaseTest):

    def test_getattr(self):
        ne = NamespaceExtension('n', None)
        ne._set('foo', 'bar')
        ne._set('baz', 'bof')
        assert ne.foo == 'bar'
        assert ne.baz == 'bof'
##         # Private attributes can be accessed as attributes.
##         ne._xyz = 123
##         assert ne._xyz == 123

    def test_getitem(self):
        ne = NamespaceExtension('n', None)
        ne._set('foo', 'bar')
        ne._set('baz', 'bof')
        assert ne['foo'] == 'bar'
        assert ne['baz'] == 'bof'
##         # Private attributes cannot be accessed as items.
##         ne._xyz = 123
##         assert raises(KeyError, lambda: ne['_xyz'])

    def test_iter(self):
        ne = NamespaceExtension('n', None)
        ne._set('foo', 'bar')
        ne._set('baz', 'bof')
        L = sorted(ne)
        assert L == ['baz', 'foo']
##         # Private attributes are not included.
##         ne._xyz = 123
        L = sorted(ne)
        assert L == ['baz', 'foo']

    def test_len(self):
        ne = NamespaceExtension('n', None)
        ne._set('foo', 'bar')
        ne._set('baz', 'bof')
        assert len(ne) == 2
##         # Private attributes are not included.
##         ne._xyz = 123
        assert len(ne) == 2

    def test_setattr_restricted(self):
        # Public attributes cannot be set directly.
        ne = NamespaceExtension('n', None)
        assert raises(AttributeError, setattr, ne, 'foo', 'bar')

##     def test_set_restricted(self):
##         # _set cannot be used to set private attributes.
##         ne = NamespaceExtension()
##         assert raises(KeyError, ne._set, '_foo', 'bar')

    def test_property(self):
        ne = NeWithProperty('n', None)
        assert ne.foobar == 'foobar'


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
