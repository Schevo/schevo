"""Database unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo import error
from schevo.test import CreatesDatabase, raises


class TestDatabase(CreatesDatabase):
    """Subclass and set self.db to the database instance to test."""

    def test_schevo_key_in_root(self):
        """A Durus database has a `SCHEVO` key in its root."""
        assert 'SCHEVO' in self.connection.get_root()

    def test_format_1(self):
        """A newly-created database will be in database format version
        1."""
        assert self.db.format == 1

    def test_empty(self):
        """A database should start out with very little."""
        assert self.db.version == 0
        assert raises(AttributeError, setattr, self.db, 'version', 2)
        assert len(self.db.extent_names()) == 0

    def test_create_extent(self):
        """Create an extent by giving it a unique name, a sequence of
        field names that may be stored for each entity in the extent,
        a sequence of field names whose values are references to other
        entities, and an optional alternate key specification that is
        a sequence of tuples of field names."""
        db = self.db
        db._create_extent(
            'Some_Extent',
            ['name', 'age', 'other'],
            ['other'],
            [('name', )],
            )
        assert db.extent_names() == ['Some_Extent']

    def test_create_extent_twice(self):
        """You cannot create an extent twice."""
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        assert raises(error.ExtentExists, db._create_extent,
                      'Some_Extent', ['name', 'age'], [])

    def test_delete_extent(self):
        """An extent can be removed."""
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        db._create_extent('An_Extent', ['something', 'else'], [])
        assert db.extent_names() == ['An_Extent', 'Some_Extent']
        db._delete_extent('An_Extent')
        assert db.extent_names() == ['Some_Extent']

    def test_delete_nonexistent_extent(self):
        """A non-existent extent cannot be removed."""
        db = self.db
        assert raises(error.ExtentDoesNotExist, db._delete_extent, 'Foo')

    def test_extent_begins_empty(self):
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        # An extent starts out containing no entities.
        assert db._extent_len('Some_Extent') == 0

    def test_create_entity(self):
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        fields = dict(name='Foo', age=33)
        oid = db._create_entity('Some_Extent', fields)
        db._commit()
        # OID starts out at 1 and rev starts out as 0.
        assert oid == 1
        assert db._entity_rev('Some_Extent', oid) == 0
        # Extent's length is incremented.
        assert db._extent_len('Some_Extent') == 1
        # Fields are stored for the entity.
        assert db._entity_field('Some_Extent', oid, 'name') == 'Foo'
        assert db._entity_field('Some_Extent', oid, 'age') == 33
        assert db._entity_fields('Some_Extent', oid) == fields

    def test_update_entity(self):
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        fields = dict(name='Foo', age=33)
        oid = db._create_entity('Some_Extent', fields)
        db._commit()
        fields = dict(name='Bar')
        db._update_entity('Some_Extent', oid, fields)
        db._commit()
        # Rev increments.
        assert db._entity_rev('Some_Extent', oid) == 1
        # Extent's length goes unchanged.
        assert db._extent_len('Some_Extent') == 1
        # Fields are updated for the entity.
        assert db._entity_field('Some_Extent', oid, 'name') == 'Bar'
        assert db._entity_field('Some_Extent', oid, 'age') == 33

    def test_delete_entity(self):
        db = self.db
        db._create_extent('Some_Extent', ['name', 'age'], [])
        fields = dict(name='Foo', age=33)
        oid = db._create_entity('Some_Extent', fields)
        db._commit()
        db._delete_entity('Some_Extent', oid)
        db._commit()
        # Entity no longer exists.
        assert raises(error.EntityDoesNotExist,
                      db._entity_fields, 'Some_Extent', oid)
        # Extent's length decrements
        assert db._extent_len('Some_Extent') == 0
        # Creating a new entity never uses a deleted oid.
        fields = dict(name='Foo', age=33)
        oid2 = db._create_entity('Some_Extent', fields)
        db._commit()
        assert oid2 == oid + 1


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
