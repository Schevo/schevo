"""Schema counter singleton."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
