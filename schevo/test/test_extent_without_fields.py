"""Extents without fields tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from textwrap import dedent

from schevo.test import CreatesSchema, PREAMBLE


class BaseExtentWithoutFields(CreatesSchema):

    body = '''

    class NoFieldsAtAll(E.Entity):
        def __unicode__(self):
            return unicode(self.s.oid)

    class OneCalculatedField(E.Entity):
        @f.integer()
        def calc(self):
            return self.s.oid

    class ExpensiveCalculatedField(E.Entity):
        @f.integer(expensive=True)
        def calc(self):
            return self.s.oid

    class Subclassed(E.OneCalculatedField):
        pass
    '''

    def test_entity_f_namespace(self):
        exe = db.execute
        entity = exe(db.NoFieldsAtAll.t.create())
        assert list(entity.f) == []
        entity = exe(db.OneCalculatedField.t.create())
        assert list(entity.f) == ['calc']
        entity = exe(db.ExpensiveCalculatedField.t.create())
        assert list(entity.f) == ['calc']
        entity = exe(db.Subclassed.t.create())
        assert list(entity.f) == ['calc']

    def test_entity_get_calc_using_property(self):
        exe = db.execute
        entity = exe(db.OneCalculatedField.t.create())
        assert entity.calc == entity.s.oid
        entity = exe(db.ExpensiveCalculatedField.t.create())
        assert entity.calc == entity.s.oid
        entity = exe(db.Subclassed.t.create())
        assert entity.calc == entity.s.oid


# class TestExtentWithoutFields1(BaseExtentWithoutFields):

#     include = True

#     format = 1


class TestExtentWithoutFields2(BaseExtentWithoutFields):

    include = True

    format = 2
