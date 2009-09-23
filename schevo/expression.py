"""Utilities for forming search expressions based on field classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from operator import and_, eq, or_

from schevo.base import Field


class Expression(object):

    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __and__(left, right):
        return Expression(left, and_, right)

    def __or__(left, right):
        return Expression(left, or_, right)

    def single_extent_field_equality_criteria(self):
        if (isinstance(self.left, type)
            and issubclass(self.left, Field)
            and self.op == eq
            and not isinstance(self.right, (Expression, Field))
            ):
            return {self.left: self.right}
        elif (isinstance(self.left, Expression)
            and self.op == and_
            and isinstance(self.right, Expression)
            ):
            criteria = self.left.single_extent_field_equality_criteria()
            criteria.update(self.right.single_extent_field_equality_criteria())
            if len(frozenset(key._extent for key in criteria)) > 1:
                raise ValueError(
                    'Not a single-extent field equality intersection criteria.')
            return criteria
        else:
            raise ValueError(
                'Not a single-extent field equality intersection criteria.')


optimize.bind_all(sys.modules[__name__])  # Last line of module.
