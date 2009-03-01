"""schevo.icon constants."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.icon._default_png import DEFAULT_PNG
from schevo.icon.plugin import install

__all__ = [
    'DEFAULT_PNG',
    'install',
    ]

# Needs to be imported right away.
import schevo.entity
