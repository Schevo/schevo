"""Object that acts like a MROW lock, but doesn't actually perform any locking.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize


class dummy_lock(object):
    """Dummy class for read_lock and write_lock objects in a database,
    so that code can be written to be multi-thread-ready but still be
    run in cases where the schevo.mt plugin is not installed."""

    def release(self):
        pass


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
