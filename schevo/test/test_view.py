"""View unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.label import label
from schevo.test import CreatesSchema


class BaseView(CreatesSchema):

    body = '''

    class EchoAlpha(E.Entity):
        """A plain extent that has a default view like any other."""

        unicode = f.string(required=False)
        integer = f.integer(required=False)
        float = f.float(required=False)

        _sample_unittest = [
            (u'unicode', 5, 2.2),
            (u'yoonicode', 6, 3.3),
            ]


    class EchoBravo(E.Entity):
        """An extent that has its default view hidden."""

        unicode = f.string(required=False)

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
                self.f.single_text = f.string()
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


# class TestView1(BaseView):

#     include = True

#     format = 1


class TestView2(BaseView):

    include = True

    format = 2
