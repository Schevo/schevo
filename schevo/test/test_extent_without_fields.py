"""Extents without fields tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.test import CreatesSchema, PREAMBLE


class BaseExtentWithoutFields(CreatesSchema):

    body = '''

    class NoFieldsAtAll(E.Entity):
        def __unicode__(self):
            return unicode(self.sys.oid)

    class OneCalculatedField(E.Entity):
        @f.integer()
        def calc(self):
            return self.sys.oid

    class ExpensiveCalculatedField(E.Entity):
        @f.integer(expensive=True)
        def calc(self):
            return self.sys.oid

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
        assert entity.calc == entity.sys.oid
        entity = exe(db.ExpensiveCalculatedField.t.create())
        assert entity.calc == entity.sys.oid
        entity = exe(db.Subclassed.t.create())
        assert entity.calc == entity.sys.oid


class TestExtentWithoutFields1(BaseExtentWithoutFields):

    include = True

    format = 1


class TestExtentWithoutFields2(BaseExtentWithoutFields):

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
