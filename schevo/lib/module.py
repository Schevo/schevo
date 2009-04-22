"""Module remembering/forgetting."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import imp
import sys

try:
    # Py-lib offers a fancy `compile` that allows source code
    # introspection, etc. but py-lib is not always available in
    # scenarios such as Py2exe.
    from py.code import compile
except ImportError:
    pass


MODULES = [] # List of modules remembered.


def forget(module):
    """Remove module from sys.modules"""
    name = module.__name__
    if name in sys.modules:
        del sys.modules[name]
    if name in MODULES:
        MODULES.remove(module)


def from_string(source, name=''):
    """Return a named Python module containing source."""
    # Strip source to get rid of any trailing whitespace, then make
    # sure it ends with a newline.
    source = source.strip() + '\n'
    module = imp.new_module(name)
    code = compile(source, name, 'exec')
    exec code in module.__dict__
    return module


def remember(module, complain=True):
    """Add a module to sys.modules.

    If module has a callable called _remember_hook(), it will call it,
    passing this function as an argument.  This hook can be used to
    remember dependencies.
    """
    name = module.__name__
    if name in sys.modules.keys() and complain:
        raise ValueError, 'module conflicts with an existing one'
    sys.modules[name] = module
    MODULES.append(module)
