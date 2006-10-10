"""
$URL: svn+ssh://svn/repos/trunk/durus/persistent_set.py $
$Id: persistent_set.py 27529 2005-10-07 20:54:14Z dbinger $
"""

import sys
from schevo.lib import optimize

from schevo.store.persistent import PersistentData


class PersistentSet(PersistentData):

    data_is = set

    __slots__ = []

    def __init__(self, *args):
        self.data = set(*args)
        self._p_note_change()

    def __and__(self, other):
        if isinstance(other, PersistentSet):
            return self.__class__(self.data & other.data)
        else:
            return self.__class__(self.data & other)

    def __cmp__(self, other):
        raise TypeError("cannot compare PersistentSets using cmp()")

    def __contains__(self, item):
        return item in self.data

    def __eq__(self, other):
        if not isinstance(other, PersistentSet):
            return False
        return self.data == other.data

    def __ge__(self, other):
        if not isinstance(other, PersistentSet):
            raise TypeError("can only compare to a PersistentSet")
        return self.data >= other.data

    def __gt__(self, other):
        if not isinstance(other, PersistentSet):
            raise TypeError("can only compare to a PersistentSet")
        return self.data > other.data

    def __iand__(self, other):
        self._p_note_change()
        if isinstance(other, PersistentSet):
            self.data &= other.data
        else:
            self.data &= other
        return self

    def __ior__(self, other):
        self._p_note_change()
        if isinstance(other, PersistentSet):
            self.data |= other.data
        else:
            self.data |= other
        return self

    def __isub__(self, other):
        self._p_note_change()
        if isinstance(other, PersistentSet):
            self.data -= other.data
        else:
            self.data -= other
        return self

    def __iter__(self):
        for x in self.data:
            yield x

    def __ixor__(self, other):
        self._p_note_change()
        if isinstance(other, PersistentSet):
            self.data ^= other.data
        else:
            self.data ^= other
        return self

    def __le__(self, other):
        if not isinstance(other, PersistentSet):
            raise TypeError("can only compare to a PersistentSet")
        return self.data <= other.data

    def __len__(self):
        return len(self.data)

    def __lt__(self, other):
        if not isinstance(other, PersistentSet):
            raise TypeError("can only compare to a PersistentSet")
        return self.data < other.data

    def __ne__(self, other):
        if not isinstance(other, PersistentSet):
            return True
        return self.data != other.data

    def __or__(self, other):
        if isinstance(other, PersistentSet):
            return self.__class__(self.data | other.data)
        else:
            return self.__class__(self.data | other)

    def __rand__(self, other):
        return self.__class__(other & self.data)

    def __ror__(self, other):
        return self.__class__(other | self.data)

    def __rsub__(self, other):
        return self.__class__(other - self.data)

    def __rxor__(self, other):
        return self.__class__(other ^ self.data)

    def __sub__(self, other):
        if isinstance(other, PersistentSet):
            return self.__class__(self.data - other.data)
        else:
            return self.__class__(self.data - other)

    def __xor__(self, other):
        if isinstance(other, PersistentSet):
            return self.__class__(self.data ^ other.data)
        else:
            return self.__class__(self.data ^other)

    def add(self, item):
        self._p_note_change()
        self.data.add(item)

    def clear(self):
        self._p_note_change()
        self.data.clear()

    def copy(self):
        return self.__class__(self.data)

    def discard(self, item):
        self._p_note_change()
        self.data.discard(item)

    def pop(self):
        self._p_note_change()
        return self.data.pop()

    def remove(self, item):
        self._p_note_change()
        self.data.remove(item)

    difference = __sub__
    difference_update = __isub__
    intersection = __and__
    intersection_update = __iand__
    issubset = __le__
    issuperset = __ge__
    symmetric_difference = __xor__
    symmetric_difference_update = __ixor__
    union = __or__
    update = __ior__


optimize.bind_all(sys.modules[__name__])  # Last line of module.
