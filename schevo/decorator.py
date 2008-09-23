"""Method decorators for Schevo.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize


# ----------------------------------------------------------------------
# Decoration.


class _labelable_classmethod(object):

    _label = None
    _marker = None

    def __init__(self, fn):
        self.fn = fn
        setattr(fn, self.marker, True)
        self._label = getattr(fn, '_label', None)

    def first_arg(self, instance, owner):
        return None

    def __get__(self, instance, owner):
        return self.labelable_callable(
            self, owner, self.first_arg(instance, owner))

    class labelable_callable(object):

        def __init__(self, decorator, owner, firstarg):
            self.decorator = decorator
            self.owner = owner
            self.firstarg = firstarg

        def __call__(self, *args, **kw):
            return self.decorator.fn(self.firstarg, *args, **kw)

        def __repr__(self):
            return '<%s method %s.%s at 0x%x>' % (
                self.owner.__name__,
                self.decorator.fn.__name__,
                id(self),
                )

        # _label

        def _get_label(self):
            return self.decorator._label

        def _set_label(self, value):
            self.decorator._label = value

        _label = property(_get_label, _set_label)


class extentmethod(_labelable_classmethod):
    """Mark a method of an `Entity` class as an extent method.

    When a function `fn` is decorated as an `extentmethod`,
    `isextentmethod(fn) -> True`, and when the method is called as
    `method(*args, **kw)`, the function is called as `fn(extent,
    *args, **kw)`.
    """

    marker = '_extentmethod'

    class labelable_callable(_labelable_classmethod.labelable_callable):
        _extentmethod = True

    def first_arg(self, instance, owner):
        return owner._extent


class extentclassmethod(extentmethod):
    """Mark a method of an `Entity` class as an extent method that is
    called as an entity classmethod.

    When a function `fn` is decorated as an `extentclassmethod`,
    `isextentmethod(fn) -> True`, and when the method is called as
    `method(*args, **kw)`, the function is called as `fn(entity_class,
    *args, **kw)`.
    """

    def first_arg(self, instance, owner):
        return owner


class selectionmethod(_labelable_classmethod):

    marker = '_selectionmethod'

    class labelable_callable(_labelable_classmethod.labelable_callable):
        _selectionmethod = True

    def first_arg(self, instance, owner):
        return owner


def with_label(label, plural=None):
    """Return a decorator that assigns a label and an optional plural
    label to a function."""
    def label_decorator(fn):
        fn._label = unicode(label)
        if plural is not None:
            fn._plural = unicode(plural)
        return fn
    return label_decorator


# ----------------------------------------------------------------------
# Introspection.


@optimize.do_not_optimize
def isclassmethod(fn):
    return type(fn.im_class) == type(fn.im_self)


@optimize.do_not_optimize
def isextentmethod(fn):
    return getattr(fn, '_extentmethod', False)


@optimize.do_not_optimize
def isselectionmethod(fn):
    return getattr(fn, '_selectionmethod', False)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


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
