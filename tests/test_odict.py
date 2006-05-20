"""Test for Ordered Dictionary.

For copyright, license, and warranty, see bottom of file.
"""

import unittest
import copy

from schevo.lib.odict import odict
from schevo.test import BaseTest


VALUES = range(1, 21)
KEYS = [str(v) for v in VALUES]
ITEMS = zip(KEYS, VALUES)
REPR = '{' + ', '.join(['%r: %r' % item for item in ITEMS]) + '}'


class TestOdict(BaseTest):

    def test_init(self):
        od = odict()
        assert od.keys() == []
        assert od.values() == []
        assert od.items() == []

    def test_init_seq(self):
        od = odict(ITEMS)
        assert od.keys() == KEYS
        assert od.values() == VALUES
        assert od.items() == ITEMS

    def test_init_dups(self):
        items_with_dups = [('1', 1), ('2', 2)] + ITEMS
        od = odict(items_with_dups)
        assert od.keys() == KEYS
        assert od.values() == VALUES
        assert od.items() == ITEMS

    def test_append(self):
        od = odict()
        od.update(odict(ITEMS))
        key = 'somekey'
        value = 'somevalue'
        od.append(key, value)
        assert od[key] == value
        assert od.keys() == KEYS + [key]
        assert od.values() == VALUES + [value]
        assert od.items() == ITEMS + [(key, value)]
        self.assertRaises(KeyError, od.append, key, value)

    def test_clear(self):
        od = odict(ITEMS)
        od.clear()
        assert od.keys() == []

    def test_copy(self):
        od = odict(ITEMS)
        od_copy = od.copy()
        assert od_copy.keys() == KEYS
        assert od_copy.values() == VALUES
        assert od_copy.items() == ITEMS
        assert od_copy._keys is not od._keys

    def test_copy_copy(self):
        od = odict(ITEMS)
        od_copy = copy.copy(od)
        assert od_copy.keys() == KEYS
        assert od_copy.values() == VALUES
        assert od_copy.items() == ITEMS
        # This is a shallow copy so the keys are the same object.
        assert od_copy._keys is od._keys

    def test_copy_deepcopy(self):
        od = odict(ITEMS)
        od_copy = copy.deepcopy(od)
        assert od_copy.keys() == KEYS
        assert od_copy.values() == VALUES
        assert od_copy.items() == ITEMS
        assert od_copy._keys is not od._keys

    def test_delitem(self):
        od = odict(ITEMS)
        key = '5'
        value = 5
        del od[key]
        keys = [k for k in KEYS if k != key]
        values = [v for v in VALUES if v != value]
        items = zip(keys, values)
        assert od.keys() == keys
        assert od.values() == values
        assert od.items() == items

    def test_fromkeys(self):
        od = odict.fromkeys(KEYS)
        assert isinstance(od, odict)
        assert od.keys() == KEYS

    def test_get(self):
        od = odict(ITEMS)
        assert od.get('5') == 5
        assert od.get('99') is None
        assert od.get('99', 'foo') == 'foo'

    def test_has_key(self):
        od = odict(ITEMS)
        assert od.has_key('5') is True
        assert od.has_key('99') is False

    def test_insert(self):
        od = odict()
        od.update(odict(ITEMS))
        key = 'somekey'
        value = 'somevalue'
        od.insert(0, key, value)
        assert od[key] == value
        assert od.keys() == [key] + KEYS
        assert od.values() == [value] + VALUES
        assert od.items() == [(key, value)] + ITEMS
        self.assertRaises(KeyError, od.insert, 0, key, value)
        key2 = 'otherkey'
        value2 = 'othervalue'
        od.insert(1, key2, value2)
        assert od.keys() == [key, key2] + KEYS
        assert od.values() == [value, value2] + VALUES
        assert od.items() == [(key, value), (key2, value2)] + ITEMS

    def test_iter(self):
        od = odict(ITEMS)
        keys = [k for k in od]
        assert keys == KEYS

    def test_iteritems(self):
        od = odict(ITEMS)
        items = [item for item in od.iteritems()]
        assert items == ITEMS

    def test_iterkeys(self):
        od = odict(ITEMS)
        keys = [k for k in od.iterkeys()]
        assert keys == KEYS

    def test_itervalues(self):
        od = odict(ITEMS)
        values = [v for v in od.itervalues()]
        assert values == VALUES

    def test_keys(self):
        od = odict(ITEMS)
        keys = od.keys()
        assert keys == KEYS
        # Make sure we get a copy, not a reference to the original.
        assert keys is not od._keys

    def test_pop(self):
        od = odict(ITEMS)
        key = '5'
        value = 5
        v = od.pop(key)
        assert v == value
        keys = [k for k in KEYS if k != key]
        values = [v for v in VALUES if v != value]
        items = zip(keys, values)
        assert od.keys() == keys
        assert od.values() == values
        assert od.items() == items

    def test_popitem(self):
        od = odict(ITEMS)
        k, v = od.popitem()
        assert (k, v) == ('20', 20)
        k, v = od.popitem()
        assert (k, v) == ('19', 19)
        k, v = od.popitem()
        assert (k, v) == ('18', 18)

    def test_popitem_empty(self):
        od = odict()
        self.assertRaises(KeyError, od.popitem)
        try:
            od.popitem()
        except KeyError, err:
            assert err.args == ('popitem(): dictionary is empty',)

    def test_repr(self):
        od = odict()
        assert repr(od) == repr({})
        od = odict(ITEMS)
        assert repr(od) == REPR

    def test_setdefault(self):
        od = odict()
        key = 'foo'
        value = 'bar'
        v = od.setdefault(key, value)
        assert v == value
        v = od.setdefault(key, 'baz')
        # Should still get the original value.
        assert v == value
        assert od.keys() == [key]

    def test_setitem_existing(self):
        # Setting the value of an existing item should not change its
        # order.
        od = odict(ITEMS)
        key = '5'
        value = 42
        od[key] = value
        assert od.keys() == KEYS
        values = []
        for v in VALUES:
            if v == 5:
                v = value
            values.append(v)
        assert od.values() == values
        items = zip(KEYS, values)
        assert od.items() == items

    def test_setitem_new(self):
        # Setting the value of a new item should put it at the end.
        od = odict(ITEMS)
        key = '99'
        value = 42
        od[key] = value
        assert od.keys()[-1] == key
        assert od.values()[-1] == value
        assert od.items()[-1] == (key, value)

    def test_str(self):
        od = odict()
        assert str(od) == str({})
        od = odict(ITEMS)
        assert str(od) == str(REPR)

    def test_update(self):
        od = odict()
        od.update(odict(ITEMS))
        assert od.keys() == KEYS
        assert od.values() == VALUES
        assert od.items() == ITEMS

    def test_update_reorder(self):
        # By passing reorder=True to odict's update, any time an
        # existing key is updated, the key is added to the end of the
        # key sequence, rather than keeping its existing position.
        od = odict()
        od[3] = '3'
        od[2] = '2'
        od[1] = '1'
        od2 = odict()
        od2[2] = 'two'
        od2[3] = 'three'
        od.update(od2, reorder=True)
        assert od.keys() == [1, 2, 3]
        assert od.values() == ['1', 'two', 'three']

    def test_update_fail(self):
        od = odict()
        self.assertRaises(ValueError, od.update, dict(ITEMS))


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
