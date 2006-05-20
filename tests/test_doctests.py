"""Test doctests.

For copyright, license, and warranty, see bottom of file.
"""

import glob
import os

from schevo import test
from schevo import trace


DOCPATH = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                       'doc')

IGNORE = [
    'test_gears-wiki',
    'test_object-relational-divide',
    ]


PREVIOUS_TRACE_LEVEL = 0


def setup(self):
    global PREVIOUS_TRACE_LEVEL
    PREVIOUS_TRACE_LEVEL = trace.monitor_level
    trace.monitor_level = 0

def teardown(self):
    trace.monitor_level = PREVIOUS_TRACE_LEVEL


def use_doc(name):
    path = os.path.join(DOCPATH, name)
    try:
        docstring = file(path, 'rU').read()
    except:
        docstring = ''
    def decorate(fn):
        fn.__doc__ = docstring
        return fn
    return decorate


for filename in glob.glob(os.path.join(DOCPATH, '*.txt')):
    name = 'test_%s' % os.path.splitext(os.path.basename(filename))[0]
    if name in IGNORE:
        continue
    @use_doc(filename)
    def dummy():
        pass
    globals()[name] = dummy


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
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
