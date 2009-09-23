"""Field maps, field spec maps, and filtering them.

TODO:

- Test field map implementations for views, queries, and transactions,
  as they all have a slightly unique implementation of .s.field_map"""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import CreatesSchema

from schevo.field import not_expensive, not_fget, not_hidden


class BaseFieldMaps(CreatesSchema):

    body = '''

    class Foo(E.Entity):

        aaa = f.string()
        bbb = f.string(hidden=True)
        @f.string(hidden=True)
        def ccc(self):
            return 'abc'
        @f.string(expensive=True)
        def ddd(self):
            return 'def'
    '''

    def test_entity_sys_field_map(self):
        tx = db.Foo.t.create()
        tx.aaa = 'a'
        tx.bbb = 'b'
        entity = db.execute(tx)
        def fkeys(*filters):
            return tuple(entity.s.field_map(*filters).keys())
        # No filters.
        expected = 'aaa', 'bbb', 'ccc', 'ddd',
        keys = fkeys()
        assert expected == keys
        # not_expensive
        expected = 'aaa', 'bbb', 'ccc',
        keys = fkeys(not_expensive)
        assert expected == keys
        # not_fget
        expected = 'aaa', 'bbb',
        keys = fkeys(not_fget)
        assert expected == keys
        # not_hidden
        expected = 'aaa', 'ddd',
        keys = fkeys(not_hidden)
        assert expected == keys
        # not_expensive, not_hidden
        expected = 'aaa',
        keys = fkeys(not_expensive, not_hidden)
        print keys
        assert expected == keys
        # not_fget, not_hidden
        expected = 'aaa',
        keys = fkeys(not_fget, not_hidden)
        assert expected == keys

    def test_extent_field_spec(self):
        extent = db.Foo
        def fkeys(*filters):
            return tuple(extent.field_spec(*filters).keys())
        # No filters.
        expected = 'aaa', 'bbb', 'ccc', 'ddd',
        keys = fkeys()
        assert expected == keys
        # not_expensive
        expected = 'aaa', 'bbb', 'ccc',
        keys = fkeys(not_expensive)
        assert expected == keys
        # not_fget
        expected = 'aaa', 'bbb',
        keys = fkeys(not_fget)
        assert expected == keys
        # not_hidden
        expected = 'aaa', 'ddd',
        keys = fkeys(not_hidden)
        assert expected == keys
        # not_expensive, not_hidden
        expected = 'aaa',
        keys = fkeys(not_expensive, not_hidden)
        print keys
        assert expected == keys
        # not_fget, not_hidden
        expected = 'aaa',
        keys = fkeys(not_fget, not_hidden)
        assert expected == keys


# class TestFieldMaps1(BaseFieldMaps):

#     include = True

#     format = 1


class TestFieldMaps2(BaseFieldMaps):

    include = True

    format = 2
