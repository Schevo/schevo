"""Entity subclass unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import datetime

from schevo.constant import UNASSIGNED
from schevo import error
from schevo.label import plural
from schevo.test import CreatesSchema
from schevo.transaction import Transaction


class BaseHiddenBases(CreatesSchema):

    body = '''

    class _GolfBase(E.Entity):

        beta = f.string()

        _key(beta)


    class GolfAlpha(E._GolfBase):

        gamma = f.integer()

        _key(gamma, 'beta')


    class GolfBeta(E._GolfBase):

        gamma = f.integer()

        _key(gamma, 'beta')

        class _Create(T.Create):

            def _setup(self):
                # Set an initial value.
                self.gamma = 10

    '''

    def test_subclass(self):
        assert '_GolfBase' not in db.extent_names()
        GolfAlpha = db.GolfAlpha
        assert GolfAlpha.field_spec.keys() == ['beta', 'gamma']
        assert ('beta', ) in GolfAlpha.key_spec
        assert ('gamma', 'beta') in GolfAlpha.key_spec
        tx = GolfAlpha.t.create()
        assert tx._field_spec.keys() == ['beta', 'gamma']
        tx.beta = 'foo'
        tx.gamma = 42
        golf = db.execute(tx)
        assert golf.beta == 'foo'
        assert golf.gamma == 42
        tx = golf.t.update()
        assert tx._field_spec.keys() == ['beta', 'gamma']
        tx = golf.t.delete()
        assert tx._field_spec.keys() == ['beta', 'gamma']
        tx = db.GolfBeta.t.create()
        assert tx._field_spec.keys() == ['beta', 'gamma']
        tx.beta = 'foo'
        golf = db.execute(tx)
        assert golf.beta == 'foo'
        assert golf.gamma == 10
        tx = golf.t.update()
        assert tx._field_spec.keys() == ['beta', 'gamma']
        tx = golf.t.delete()
        assert tx._field_spec.keys() == ['beta', 'gamma']


class BaseSameNameSubclasses(CreatesSchema):

    body = '''

    class Something(E.Entity):

        field1 = f.string()

        _key(field1)

        _plural = u'Somethingys'


    class Something(E.Something):

        field2 = f.integer()

        _key(field2, 'field1')
    '''

    def test_subclass_fields(self):
        assert db.extent_names() == ['Something']
        assert db.Something.field_spec.keys() == ['field1', 'field2']
        assert ('field1', ) in db.Something.key_spec
        assert ('field2', 'field1', ) in db.Something.key_spec

    def test_subclass_labels(self):
        assert plural(db.Something) == u'Somethingys'


class BaseSubclassTransactionCorrectness(CreatesSchema):

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
        assert tx.s.extent_name == 'First'
        tx = db.Second.t.create()
        assert tx.s.extent_name == 'Second'


# class TestHiddenBases1(BaseHiddenBases):

#     include = True

#     format = 1


class TestHiddenBases2(BaseHiddenBases):

    include = True

    format = 2


# class TestSameNameSubclasses1(BaseSameNameSubclasses):

#     include = True

#     format = 1


class TestSameNameSubclasses2(BaseSameNameSubclasses):

    include = True

    format = 2


# class TestSubclassTransactionCorrectness1(BaseSubclassTransactionCorrectness):

#     include = True

#     format = 1


class TestSubclassTransactionCorrectness2(BaseSubclassTransactionCorrectness):

    include = True

    format = 2
