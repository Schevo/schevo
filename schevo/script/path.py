"""Path-handling functions for Schevo script commands.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import os


def package_path(pkg_or_path):
    """If pkg_or_path is a module, return its path; otherwise,
    return pkg_or_path."""
    from_list = pkg_or_path.split('.')[:1]
    try:
        pkg = __import__(pkg_or_path, {}, {}, from_list)
    except ImportError:
        return os.path.abspath(pkg_or_path)
    if '__init__.py' in pkg.__file__:
        # Package was specified; return the dir it's in.
        return os.path.abspath(os.path.dirname(pkg.__file__))
    else:
        # Module was specified; return its filename.
        return os.path.abspath(pkg.__file__)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


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
