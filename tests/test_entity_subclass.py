"""Entity subclass unit tests.

For copyright, license, and warranty, see bottom of file.
"""

import datetime

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.label import plural
from schevo import test
from schevo.transaction import Transaction


class TestHiddenBases(test.CreatesSchema):

    body = '''

    class _GolfAlphaBase(E.Entity):

        beta = f.unicode()

        _key(beta)


    class GolfAlpha(E._GolfAlphaBase):

        gamma = f.integer()

        _key(gamma, 'beta')
    '''

    def test_subclass(self):
        assert '_GolfAlphaBase' not in db.extent_names()
        GolfAlpha = db.GolfAlpha
        assert GolfAlpha.field_spec.keys() == [
            'beta',
            'gamma',
            ]
        assert ('beta', ) in GolfAlpha.key_spec
        assert ('gamma', 'beta') in GolfAlpha.key_spec


class TestSameNameSubclasses(test.CreatesSchema):

    body = '''

    class Something(E.Entity):

        field1 = f.unicode()

        _key(field1)

        _plural = u'Somethingys'


    class Something(E.Something):

        field2 = f.integer()

        _key(field2, 'field1')
    '''

    def test_subclass_fields(self):
        assert db.extent_names() == ['Something']
        assert db.Something.field_spec.keys() == [
            'field1',
            'field2',
            ]
        assert ('field1', ) in db.Something.key_spec
        assert ('field2', 'field1', ) in db.Something.key_spec

    def test_subclass_labels(self):
        assert plural(db.Something) == u'Somethingys'


class TestSubclassTransactionCorrectness(test.CreatesSchema):

    body = '''
    
    class _Super(E.Entity):
        pass
        
    class First(E._Super):
        pass
        
    class Second(E._Super):
        pass
    '''
    
    def test_tx_correctness(self):
        tx = db.First.t.create()
        assert tx.sys.extent_name == 'First'
        tx = db.Second.t.create()
        assert tx.sys.extent_name == 'Second'


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
