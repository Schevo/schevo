"""Unit tests for module remembering/forgetting.

For copyright, license, and warranty, see bottom of file.
"""

import sys

from schevo.lib import module


MODULE_SRC = """
x = 123

class Foo(object):

    @classmethod
    def bar(cls):
        return SomeClass

class SomeClass(object):
    pass
"""


def test_module():
    m = module.from_string(MODULE_SRC, 'some_module')
    assert m.x == 123
    assert m.__name__ == 'some_module'

def test_two_modules():
    m1 = module.from_string(MODULE_SRC, 'some_module')
    m2 = module.from_string(MODULE_SRC, 'some_module')
    assert m1.Foo.bar() is m1.SomeClass
    assert m1.Foo.bar() is not m2.SomeClass
    assert m2.Foo.bar() is m2.SomeClass
    assert m2.Foo.bar() is not m1.SomeClass

def test_remember_forget():
    m = module.from_string(MODULE_SRC, 'some_module')
    module.remember(m)
    assert m.__name__ in sys.modules
    module.forget(m)
    assert m.__name__ not in sys.modules


# Copyright (C) 2001-2006 Orbtech, L.L.C.
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
