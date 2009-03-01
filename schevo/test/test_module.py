"""Unit tests for module remembering/forgetting."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
