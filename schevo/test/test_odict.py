"""

Initialization::

  >>> from schevo.lib.odict import odict
  >>> VALUES = range(1, 21)
  >>> KEYS = [str(v) for v in VALUES]
  >>> ITEMS = zip(KEYS, VALUES)
  >>> REPR = '{' + ', '.join(['%r: %r' % item for item in ITEMS]) + '}'


Create an odict from keys::

  >>> od = odict.fromkeys(KEYS)
  >>> assert isinstance(od, odict)
  >>> assert od.keys() == KEYS
  >>> assert od.values() == [None] * len(KEYS)

  >>> od = odict.fromkeys(KEYS, 123)
  >>> assert isinstance(od, odict)
  >>> assert od.keys() == KEYS
  >>> assert od.values() == [123] * len(KEYS)

Get an item from the odict, falling back to a default value::

  >>> od = odict(ITEMS)
  >>> assert od.get('5') == 5
  >>> assert od.get('99') is None
  >>> assert od.get('99', 'foo') == 'foo'

Determine if an odict has a key::

  >>> od = odict(ITEMS)
  >>> assert od.has_key('5')
  >>> assert not od.has_key('99')

Create an empty odict::

  >>> od = odict()
  >>> assert od.keys() == []
  >>> assert od.values() == []
  >>> assert od.items() == []

Create an odict based on a list::

  >>> od = odict(ITEMS)
  >>> assert od.keys() == KEYS
  >>> assert od.values() == VALUES
  >>> assert od.items() == ITEMS

Create an odict based on a generator::

  >>> g = (i for i in ITEMS)
  >>> od = odict(g)
  >>> assert od.keys() == KEYS
  >>> assert od.values() == VALUES
  >>> assert od.items() == ITEMS

Create an odict with duplicate items::

  >>> items_with_dups = [('1', 1), ('2', 2)] + ITEMS
  >>> od = odict(items_with_dups)
  >>> assert od.keys() == KEYS
  >>> assert od.values() == VALUES
  >>> assert od.items() == ITEMS

x.__delitem__(y) <==> del x[y]

::
  >>> od = odict(ITEMS)
  >>> key = '5'
  >>> value = 5
  >>> del od[key]
  >>> keys = [k for k in KEYS if k != key]
  >>> values = [v for v in VALUES if v != value]
  >>> items = zip(keys, values)
  >>> assert od.keys() == keys
  >>> assert od.values() == values
  >>> assert od.items() == items

x.__iter__() <==> iter(x)

::
  >>> od = odict(ITEMS)
  >>> keys = [k for k in od]
  >>> assert keys == KEYS

x.__repr__() <==> repr(x)

::
  >>> od = odict()
  >>> assert repr(od) == repr({})
  >>> assert str(od) == str({})
  >>> od = odict(ITEMS)
  >>> assert repr(od) == REPR
  >>> assert str(od) == str(REPR)

x.__setitem__(i, y) <==> x[i]=y

Setting the value of an existing item does not change its
order::

  >>> od = odict(ITEMS)
  >>> key = '5'
  >>> value = 42
  >>> od[key] = value
  >>> assert od.keys() == KEYS
  >>> values = []
  >>> for v in VALUES:
  ...   if v == 5:
  ...       v = value
  ...   values.append(v)
  >>> assert od.values() == values
  >>> items = zip(KEYS, values)
  >>> assert od.items() == items

Setting the value of a new item places it at the end::

  >>> od = odict(ITEMS)
  >>> key = '99'
  >>> value = 42
  >>> od[key] = value
  >>> assert od.keys()[-1] == key
  >>> assert od.values()[-1] == value
  >>> assert od.items()[-1] == (key, value)

append(self, key, item)

::
  >>> od = odict(ITEMS)
  >>> key = 'somekey'
  >>> value = 'somevalue'
  >>> od.append(key, value)
  >>> assert od[key] == value
  >>> assert od.keys() == KEYS + [key]
  >>> assert od.values() == VALUES + [value]
  >>> assert od.items() == ITEMS + [(key, value)]
  >>> od.append(key, value)
  Traceback (most recent call last):
      ...
  KeyError: "append(): key 'somekey' already in dictionary"

D.clear() -> None.  Remove all items from D.

::
  >>> od = odict(ITEMS)
  >>> od.clear()
  >>> od.keys()
  []

D.copy() -> a shallow copy of D

Shallow copy with `copy` method::

  >>> od = odict(ITEMS)
  >>> od_copy = od.copy()
  >>> assert od_copy.keys() == KEYS
  >>> assert od_copy.values() == VALUES
  >>> assert od_copy.items() == ITEMS
  >>> assert od_copy._keys is not od._keys

Shallow copy using `copy` module::

  >>> import copy
  >>> od = odict(ITEMS)
  >>> od_copy = copy.copy(od)
  >>> assert od_copy.keys() == KEYS
  >>> assert od_copy.values() == VALUES
  >>> assert od_copy.items() == ITEMS

Note: When using `copy.copy`, it creates a shallower copy than
the `copy` method, so the keys are the same object::

  >>> assert od_copy._keys is od._keys

Deep copy using `copy` module::

  >>> od = odict(ITEMS)
  >>> od_copy = copy.deepcopy(od)
  >>> assert od_copy.keys() == KEYS
  >>> assert od_copy.values() == VALUES
  >>> assert od_copy.items() == ITEMS
  >>> assert od_copy._keys is not od._keys

insert(self, index, key, item)

::
  >>> od = odict(ITEMS)
  >>> key = 'somekey'
  >>> value = 'somevalue'
  >>> od.insert(0, key, value)
  >>> assert od[key] == value
  >>> assert od.keys() == [key] + KEYS
  >>> assert od.values() == [value] + VALUES
  >>> assert od.items() == [(key, value)] + ITEMS
  >>> od.insert(0, key, value)
  Traceback (most recent call last):
      ...
  KeyError: "insert(): key 'somekey' already in dictionary"
  >>> key2 = 'otherkey'
  >>> value2 = 'othervalue'
  >>> od.insert(1, key2, value2)
  >>> assert od.keys() == [key, key2] + KEYS
  >>> assert od.values() == [value, value2] + VALUES
  >>> assert od.items() == [(key, value), (key2, value2)] + ITEMS

D.iterkeys() -> an iterator over the keys of D

::
  >>> od = odict(ITEMS)
  >>> keys = [k for k in od.iterkeys()]
  >>> assert keys == KEYS

D.iteritems() -> an iterator over the (key, value) items of D

::
  >>> od = odict(ITEMS)
  >>> items = [item for item in od.iteritems()]
  >>> assert items == ITEMS

D.itervalues() -> an iterator over the values of D

::
  >>> od = odict(ITEMS)
  >>> values = [v for v in od.itervalues()]
  >>> assert values == VALUES

D.keys() -> list of D's keys

::
  >>> od = odict(ITEMS)
  >>> keys = od.keys()
  >>> assert keys == KEYS

Make sure we get a copy, not a reference to the original::

  >>> assert keys is not od._keys

D.pop(k[,d]) -> v, remove specified key and return the
corresponding value

If key is not found, d is returned if given, otherwise
KeyError is raised

::
  >>> od = odict(ITEMS)
  >>> key = '5'
  >>> value = 5
  >>> v = od.pop(key)
  >>> assert v == value
  >>> keys = [k for k in KEYS if k != key]
  >>> values = [v for v in VALUES if v != value]
  >>> items = zip(keys, values)
  >>> assert od.keys() == keys
  >>> assert od.values() == values
  >>> assert od.items() == items
  >>> assert od.pop('999', None) is None
  >>> assert od.pop('999', 'foo') == 'foo'
  >>> od.pop('999')
  Traceback (most recent call last):
      ...
  KeyError: '999'

D.popitem() -> (k, v), remove and return last (key, value)
pair as a 2-tuple; but raise KeyError if D is empty

::
  >>> od = odict(ITEMS)
  >>> k, v = od.popitem()
  >>> assert (k, v) == ('20', 20)
  >>> k, v = od.popitem()
  >>> assert (k, v) == ('19', 19)
  >>> k, v = od.popitem()
  >>> assert (k, v) == ('18', 18)
  >>> od = odict()
  >>> od.popitem()
  Traceback (most recent call last):
      ...
  KeyError: 'popitem(): dictionary is empty'

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

::
  >>> od = odict()
  >>> key = 'foo'
  >>> value = 'bar'
  >>> v = od.setdefault(key, value)
  >>> assert v == value
  >>> v = od.setdefault(key, 'baz')
  >>> assert v == value   # This key was already set.
  >>> assert od.keys() == [key]

update(self, other, reorder=False)

::
  >>> od = odict()
  >>> od.update(odict(ITEMS))
  >>> assert od.keys() == KEYS
  >>> assert od.values() == VALUES
  >>> assert od.items() == ITEMS

Pass `reorder=True` to `update` to add to the end of the key sequence
any time an existing key is updated, rather than keeping its original
position::

  >>> od = odict()
  >>> od[3] = '3'
  >>> od[2] = '2'
  >>> od[1] = '1'
  >>> od2 = odict()
  >>> od2[2] = 'two'
  >>> od2[3] = 'three'
  >>> od.update(od2, reorder=True)
  >>> assert od.keys() == [1, 2, 3]
  >>> assert od.values() == ['1', 'two', 'three']

`other` must be an odict::

  >>> od = odict()
  >>> od.update(dict(ITEMS))
  Traceback (most recent call last):
      ...
  ValueError: other must be an odict

Use the `reorder` method to move an item from its current position to
a new one.  Rules for `list.insert` are followed when reordering.

  >>> od = odict()
  >>> od['c'] = 3
  >>> od['b'] = 2
  >>> od['a'] = 1
  >>> od['d'] = 4
  >>> od.keys()
  ['c', 'b', 'a', 'd']
  >>> od.reorder(1, 'a')
  >>> od.keys()
  ['c', 'a', 'b', 'd']
  >>> od.reorder(2, 'c')
  >>> od.keys()
  ['a', 'b', 'c', 'd']

Use the `index` method to find the position of a key.

  >>> od = odict()
  >>> od['c'] = 3
  >>> od['b'] = 2
  >>> od['a'] = 1
  >>> od['d'] = 4
  >>> od.keys()
  ['c', 'b', 'a', 'd']
  >>> od.index('b')
  1
  >>> od.reorder(od.index('b'), 'd')
  >>> od.keys()
  ['c', 'd', 'b', 'a']

"""
