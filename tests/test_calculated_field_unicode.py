"""Calculated field unicode representation tests.

For copyright, license, and warranty, see bottom of file.
"""

from textwrap import dedent

from schevo.test import CreatesSchema, PREAMBLE


class TestQuery(CreatesSchema):

    body = '''
    
    class Thing(E.Entity):
        image = f.image()
        password = f.password()
        @f.image()
        def calc_image(self):
            return self.image
        @f.password()
        def calc_password(self):
            return self.password
    '''

    def test_representations(self):
        thing = db.execute(db.Thing.t.create(
            image = 'some-image-data',
            password = 'some-password',
            ))
        # Unicode reprs of fields on thing itself.
        assert unicode(thing.f.image) == u'(Binary data)'
        assert unicode(thing.f.password) == u'(Hidden)'
        assert unicode(thing.f.calc_image) == u'(Binary data)'
        assert unicode(thing.f.calc_password) == u'(Hidden)'
        # Unicode reprs of fields on thing's default view.
        thing_view = thing.v.default()
        assert unicode(thing_view.f.image) == u'(Binary data)'
        assert unicode(thing_view.f.password) == u'(Hidden)'
        assert unicode(thing_view.f.calc_image) == u'(Binary data)'
        assert unicode(thing_view.f.calc_password) == u'(Hidden)'


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
