"""Schema counter singleton.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize


class schema_counter(object):
    """Schema counter singleton.

    This is a class instead of a global, because globals won't work
    because of the binding done by optimize.bind_all.
    """

    _current = 0

    @classmethod
    def next(cls):
        c = cls._current
        cls._current += 1
        return c

    @classmethod
    def next_schema_name(cls):
        return 'schevo-db-schema-%i' % cls.next()


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
