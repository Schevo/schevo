"""Visual progress indicator.

For copyright, license, and warranty, see bottom of file.
"""

import sys

write = sys.stdout.write
flush = sys.stdout.flush


TWIRLY_CHARS = '-\\|/'
TWIRLY_COUNT = len(TWIRLY_CHARS)


class Indicator(object):

    def __init__(self, total):
        self.total = total
        self.step = (total / 10000) or 1  # Cannot be zero.
        self.processed = 0
        self.twirly_sequence = 0

    def update(self, current):
        percentage = current * 100 / self.total
        self.processed += 1
        if self.processed % self.step == 0:
            next_char = TWIRLY_CHARS[self.twirly_sequence]
            output = '%3i%% %s\r' % (percentage, next_char)
            write(output)
            flush()
            self.twirly_sequence = (self.twirly_sequence + 1) % TWIRLY_COUNT

    def finish(self):
        write('100%  \n')
        flush()


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
