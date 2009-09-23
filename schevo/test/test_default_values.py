"""Default value unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.constant import DEFAULT, UNASSIGNED
from schevo import error
from schevo.test import CreatesSchema


class BaseDefaultValues(CreatesSchema):

    body = '''

    class Charlie(E.Entity):
        """Fields have default values for create transactions."""

        beta = f.string(default='foo')      # Non-callable default value.
        gamma = f.integer(default=lambda : 42) # Callable default value.

        _sample_unittest = [
            ('bar', 12),                    # No defaults are used.
            (DEFAULT, 12),                  # Default is used for beta.
            ('bar', DEFAULT),               # Default is used for gamma.
            (DEFAULT, DEFAULT),             # Defaults used for beta and gamma.
            ]
    '''

    def test_populate_defaults(self):
        charlies = db.Charlie.find()
        assert len(charlies) == 4
        expected = [
            ('bar', 12),
            ('foo', 12),
            ('bar', 42),
            ('foo', 42),
            ]
        for charlie, (beta, gamma) in zip(charlies, expected):
            assert charlie.beta == beta
            assert charlie.gamma == gamma


# class TestDefaultValues1(BaseDefaultValues):

#     include = True

#     format = 1


class TestDefaultValues2(BaseDefaultValues):

    include = True

    format = 2
