"""Field namespace classes.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.namespace import NamespaceExtension


class FieldExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2009 ElevenCraft Inc.
#
# Schevo
# http://schevo.org/
#
# ElevenCraft Inc.
# Bellingham, WA
# http://11craft.com/
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
