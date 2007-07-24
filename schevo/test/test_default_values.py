"""Default value unit tests.

For copyright, license, and warranty, see bottom of file.
"""

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


class TestDefaultValues1(BaseDefaultValues):

    format = 1


class TestDefaultValues2(BaseDefaultValues):

    format = 2


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
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
