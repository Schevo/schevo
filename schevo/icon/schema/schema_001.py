"""Schevo icon schemata, for storing icons in a database and
associating them with Schevo objects.

Usage inside a schema::

  schevo.icon.schema.use()

For copyright, license, and warranty, see bottom of file.
"""


# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


def _export(namespace, **kw):
    _export_all(namespace, globals(), **kw)


class SchevoIcon(E.Entity):

    name = f.unicode()
    data = f.image()

    _key(name)


# XXX: Backwards-compatibility.
import textwrap
preamble = textwrap.dedent(
    """
    from warnings import warn as _warn
    _warn('See http://schevo.org/lists/archives/schevo-devel/'
    '2006-March/000568.html', DeprecationWarning)
    _import('Schevo', 'icon', 1)
    """
    )
# /XXX


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
