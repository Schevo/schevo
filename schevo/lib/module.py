"""Module remembering/forgetting.

For copyright, license, and warranty, see bottom of file.
"""

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
