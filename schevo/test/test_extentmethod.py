"""Extentmethod unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
            return self.s.oid
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


# class TestExtentMethod1(BaseExtentMethod):

#     include = True

#     format = 1


class TestExtentMethod2(BaseExtentMethod):

    include = True

    format = 2
