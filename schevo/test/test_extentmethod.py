"""Extentmethod unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema


class BaseExtentMethod(CreatesSchema):

    body = '''

    class Hotel(E.Entity):

        @extentmethod
        def x_return_extent_name(extent):
            return extent.name
    '''

    def test_extentmethod_is_passed_extent(self):
        extent_name = 'Hotel'
        result = db.Hotel.x.return_extent_name()
        assert result == extent_name


class TestExtentMethod1(BaseExtentMethod):

    include = True

    format = 1


class TestExtentMethod2(BaseExtentMethod):

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
