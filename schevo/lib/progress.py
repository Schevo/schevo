"""Visual progress indicator."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
