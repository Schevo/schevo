"""PyDispatcher signals."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.constant import _GLOBAL


class TransactionExecuted(object):
    """Signal sent using PyDispatcher to indicate that a transaction
    was successfully executed."""
    __metaclass__ = _GLOBAL
