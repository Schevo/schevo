"""Test for extent name overriding, which is useful for exporting
entity class definitions from a schema.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.test import CreatesSchema


class TestOverride(CreatesSchema):

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


# Copyright (C) 2001-2006 Orbtech, L.L.C. and contributors.
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
