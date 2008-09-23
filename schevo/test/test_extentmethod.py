"""Extentmethod unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.introspect import isextentmethod
from schevo.test import CreatesSchema


class BaseExtentMethod(CreatesSchema):

    body = '''

    class Hotel(E.Entity):

        @extentmethod
        def x_return_extent_name(extent):
            return extent.name

        @extentclassmethod
        def x_return_class(cls):
            return cls

        def x_return_oid(self):
            return self.sys.oid
    '''

    def test_extentmethod_is_passed_extent(self):
        extent_name = 'Hotel'
        result = db.Hotel.x.return_extent_name()
        assert result == extent_name

    def test_extentclassmethod_is_passed_entity_class(self):
        entity_class = db.schema.E['Hotel']
        result = db.Hotel.x.return_class()
        assert result == entity_class

    def test_extentmethod_detection(self):
        assert isextentmethod(db.Hotel.x.return_extent_name)
        assert isextentmethod(db.schema.E['Hotel'].x_return_extent_name)
        assert isextentmethod(db.Hotel.x.return_class)
        assert isextentmethod(db.schema.E['Hotel'].x_return_class)
        hotel = db.execute(db.Hotel.t.create())
        assert not isextentmethod(hotel.x.return_oid)
        assert not isextentmethod(db.schema.E['Hotel'].x_return_oid)

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
