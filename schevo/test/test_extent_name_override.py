"""Test for extent name overriding, which is useful for exporting
entity class definitions from a schema."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema


class BaseOverride(CreatesSchema):

    body = '''

    class Base(E.Entity):
        name = f.string()

    class Base2(E.Base):
        _actual_name = "BaseTwo"

    class BaseThree(E.BaseTwo):
        pass
    '''

    def test_extents_in_db(self):
        expected = ['Base', 'BaseThree', 'BaseTwo']
        result = db.extent_names()
        assert result == expected


# class TestOverride1(BaseOverride):

#     include = True

#     format = 1


class TestOverride2(BaseOverride):

    include = True

    format = 2
