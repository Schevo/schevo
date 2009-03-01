"""Field namespace classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevo.namespace import NamespaceExtension


class FieldExtenders(NamespaceExtension):
    """A namespace of extra attributes."""

    __slots__ = NamespaceExtension.__slots__

    _readonly = False


optimize.bind_all(sys.modules[__name__])  # Last line of module.
