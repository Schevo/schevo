"""Object that acts like a MROW lock, but doesn't actually perform any locking."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize


class dummy_lock(object):
    """Dummy class for read_lock and write_lock objects in a database,
    so that code can be written to be multi-thread-ready but still be
    run in cases where the schevo.mt plugin is not installed."""

    def release(self):
        pass


optimize.bind_all(sys.modules[__name__])  # Last line of module.
