"""Method decorators for Schevo.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize


class extentmethod(object):
    """Mark a method of an `Entity` class as an extent method.

    When a function `fn` is decorated as an `extentmethod`,
    `isextentmethod(fn) -> True`, and when the method is called as
    `method(*args, **kw)`, the function is called as `fn(extent,
    *args, **kw)`.
    """

    def __init__(self, fn):
        self.fn = fn
        fn._extentmethod = True
        self._label = getattr(fn, '_label', None)

    def __get__(self, instance, owner=None):
        if owner is None:
            owner = type(instance)
        return _extentmethodcallable(self, owner, owner._extent)


class extentclassmethod(extentmethod):
    """Mark a method of an `Entity` class as an extent method that is
    called as an entity classmethod.

    When a function `fn` is decorated as an `extentclassmethod`,
    `isextentmethod(fn) -> True`, and when the method is called as
    `method(*args, **kw)`, the function is called as `fn(entity_class,
    *args, **kw)`.
    """

    def __get__(self, instance, owner=None):
        if owner is None:
            owner = type(instance)
        return _extentmethodcallable(self, owner, owner)


class _extentmethodcallable(object):

    _extentmethod = True

    def __init__(self, extentmethod, owner, firstarg):
        self.extentmethod = extentmethod
        self.owner = owner
        self.firstarg = firstarg

    def __call__(self, *args, **kw):
        return self.extentmethod.fn(self.firstarg, *args, **kw)

    def __repr__(self):
        return '<extent method %s.%s at 0x%x>' % (
            self.owner.__name__,
            self.extentmethod.fn.__name__,
            id(self),
            )

    def _get_label(self):
        return self.extentmethod._label

    def _set_label(self, value):
        self.extentmethod._label = value

    _label = property(_get_label, _set_label)


def isextentmethod(fn):
    return getattr(fn, '_extentmethod', False)


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
