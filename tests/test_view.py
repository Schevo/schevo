"""View unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.label import label
from schevo.test import CreatesSchema


class BaseView(CreatesSchema):

    body = '''

    class EchoAlpha(E.Entity):
        """A plain extent that has a default view like any other."""

        unicode = f.unicode(required=False)
        integer = f.integer(required=False)
        float = f.float(required=False)

        _sample_unittest = [
            (u'unicode', 5, 2.2),
            (u'yoonicode', 6, 3.3),
            ]


    class EchoBravo(E.Entity):
        """An extent that has its default view hidden."""

        unicode = f.unicode(required=False)

        _hide('v_default')

        _sample_unittest = [
            (u'string', ),
            (u'strang', ),
            ]


    class EchoCharlie(E.Entity):
        """An extent that has an overridden default view."""

        single = f.integer()

        @with_label(u'Custom View')
        def v_custom(self):
            return self._CustomView(self)

        class _CustomView(V.View):

            _label = u'Custom View'

            def _setup(self, entity):
                # Create a new integer field called 'double'.
                self.f.double = f.integer()
                # Assign a value to 'double' based on the entity this view
                # is for.
                self.double = entity.single * 2
                # Do the same, creating a unicode field.
                self.f.single_text = f.unicode()
                self.single_text = unicode(entity.single)

        class _DefaultView(V.View):

            def _setup(self, entity):
                # Create a new integer field called 'double'.
                self.f.double = f.integer()
                # Assign a value to 'double' based on the entity this view
                # is for.
                self.double = self.single * 2

        _sample_unittest = [
            (1, ),
            (2, ),
            ]
    '''

    def test_v_namespace(self):
        # All entities have a 'default' view.
        assert list(db.EchoAlpha[1].v) == ['default']
        # An entity class may have hidden the 'default' view.
        assert list(db.EchoBravo[1].v) == []
        # An entity class may have specified additional views.
        assert list(sorted(db.EchoCharlie[1].v)) == ['custom', 'default']

    def test_view_labels(self):
        assert label(db.EchoAlpha[1].v.default) == u'View'
        assert label(db.EchoCharlie[1].v.custom) == u'Custom View'
        assert label(db.EchoAlpha[1].v.default()) == u'View'
        assert label(db.EchoCharlie[1].v.custom()) == u'Custom View'

    def test_default_views(self):
        ea = db.EchoAlpha[1]
        ea_view = ea.v.default()
        assert ea.unicode == ea_view.unicode
        assert ea.integer == ea_view.integer
        assert ea.float == ea_view.float

    def test_default_view_is_readonly(self):
        ea = db.EchoAlpha[1]
        ea_view = ea.v.default()
        assert ea_view.f.unicode.readonly
        assert ea_view.f.integer.readonly
        assert ea_view.f.float.readonly


class TestView1(BaseView):

    format = 1


class TestView2(BaseView):

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
