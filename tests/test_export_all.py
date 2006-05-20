"""Tests for _export_all.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema


class TestExportAll(CreatesSchema):

    body = '''

    _import('Schevo', 'icon', 1)
    '''

    def test_existence(self):
        assert db.extent_names() == ['SchevoIcon']
        assert not db.SchevoIcon.hidden


class TestExportAllHidden(CreatesSchema):

    body = '''

    _import('Schevo', 'icon', 1, hidden=True)
    '''

    def test_existence(self):
        assert db.SchevoIcon.hidden


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
