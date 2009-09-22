"""Field unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import unittest

import datetime
import sys
import warnings

from schevo.constant import UNASSIGNED
from schevo import field
from schevo import fieldspec
from schevo.test import BaseTest, DocTest, raises


class TestField(BaseTest):

    def test_Field(self):
        f = field.Field(instance=None)
        f.set('Spam')
        assert f.get() == 'Spam'
        f.set(123)
        assert f.get() == 123

    def test_FieldMap(self):
        fm = fieldspec.FieldMap()
        f = field.Field(instance=None)
        f.set('Spam')
        fm['Test'] = f
        assert fm.value_map() == {'Test': 'Spam'}

    def test_FieldSpecMap_field_map(self):
        fsm = fieldspec.FieldSpecMap()
        class _Field(field.Field):
            valid_values = [1, 2, 3]
        fsm['foo_bar'] = _Field
        fm = fsm.field_map()
        assert fm.keys() == ['foo_bar']
        assert fm['foo_bar'].valid_values == [1, 2, 3]
        assert isinstance(fm['foo_bar'], field.Field)


class Base:
    """The standard battery of tests for all field types.

    bad_values_default: A list of bad values that should cause an error
    to occur.

    convert_values_default: A list of tuples of (value, convertedValue).
    The test suite will convert value and test for equality between
    the result and convertedValue, when using default field
    attributes.

    FieldClass: The field subclass to test.

    good_values_default: A list of good values that should cause no
    error and cause no different value to occur upon conversion, when
    using default field attributes.
    """

    bad_values_default = []
    convert_values_default = []
    FieldClass = None
    good_values_default = []
    str_values_default = []
    min_max_values = []
    min_max_sizes = []
    error_message = 'Custom error message.'

    def empty_field(self, **kw):
        """Returns a field instance with no instance or attribute."""
        class CustomClass(self.FieldClass):
            pass
        for key, value in kw.iteritems():
            setattr(CustomClass, key, value)
        field = CustomClass(instance=None)
        return field

    def test_never_allow_none(self):
        f = self.empty_field()
        assert raises(ValueError, f.set, None)

    def test_requiredIsFalse(self):
        f = self.empty_field(required=False)
        f.set(UNASSIGNED)
        assert f.get() is UNASSIGNED

    def test_convert_values_default(self):
        for value, convertedValue in self.convert_values_default:
            f = self.empty_field()
            assert f.convert(value) == convertedValue

    def test_good_values_default(self):
        for value in self.good_values_default:
            # Setting.
            f = self.empty_field()
            f.set(value)
            # Validation.
            f = self.empty_field()
            f.validate(value)
            # Verification.
            f = self.empty_field()
            f.verify(value)

    def test_bad_values_default(self):
        for value in self.bad_values_default:
            f = self.empty_field()
            try:
                f.validate(value)
            except ValueError, e:
                assert e.args[0] != self.error_message
            else:
                raise Exception('ValueError not raised for value', value)
            f = self.empty_field(error_message = self.error_message)
            try:
                f.validate(value)
            except ValueError, e:
                assert e.args[0] == self.error_message
            else:
                raise Exception('ValueError not raised for value', value)

    def test_str_values_default(self):
        for value, strValue in self.str_values_default:
            f = self.empty_field()
            f.set(value)
            assert str(f) == strValue

    def test_min_max_values(self):
        for value, min_value, max_value, is_valid in self.min_max_values:
            kw = {}
            if min_value:
                kw['min_value'] = min_value
            if max_value:
                kw['max_value'] = max_value
            f = self.empty_field(**kw)
            if is_valid:
                # No exception is expected.
                f.validate(value)
                f.set(value)
                assert f.value == value
            else:
                # Exception is expected.
                assert raises(ValueError, f.validate, value)

    def test_min_max_sizes(self):
        for (value, min_size, max_size,
             allow_empty, is_valid) in self.min_max_sizes:
            kw = {}
            if min_size:
                kw['min_size'] = min_size
            if max_size:
                kw['max_size'] = max_size
            if allow_empty:
                kw['allow_empty'] = allow_empty
            f = self.empty_field(**kw)
            if is_valid:
                # No exception is expected.
                f.validate(value)
                f.set(value)
                assert f.value == value
            else:
                # Exception is expected.
                assert raises(ValueError, f.validate, value)


class TestStringMultilineNone(Base, BaseTest):

    class FieldClass(field.String):
        multiline = None                # (The default value.)

    # More Unicode expertise needed.

    convert_values_default = [(0., u'0.0'),
                              (555.55, u'555.55'),
                              (-555.55, u'-555.55'),
                              (555, u'555'),
                              (-555, u'-555'),
                              ('abcdefg', u'abcdefg'),
                              ]
    good_values_default = [u'abcdefg',
                           u'abcdefg\nhijklmno']
    min_max_sizes = [
        # (value, min, max, allow_empty, is_valid),
        (u'test', None, None, True, True),
        (u'test', None, None, False, True),
        (u'', None, None, True, True),
        (u'', None, None, False, False),
        (u'test', 2, 8, False, True),
        (u'', 5, 8, False, False),
        (u'', 5, 8, True, True),
        (u'test', 5, None, False, False),
        (u'test_test', None, 8, False, False),
        ]


class TestStringMultilineTrue(TestStringMultilineNone):

    class FieldClass(field.String):
        multiline = True


class TestStringMultilineFalse(TestStringMultilineNone):

    class FieldClass(field.String):
        multiline = False

    good_values_default = [u'abcdefg']

    bad_values_default = [u'abcdefg\nhijklmno']


class TestInteger(Base, BaseTest):

    class FieldClass(field.Integer): pass

    convert_values_default = [(0.0, 0),
                              (555.55, 555),
                              (-555.55, -555),
                              ('0', 0),
                              ('555', 555),
                              ('-555', -555),
                              (u'0', 0),
                              (u'555', 555),
                              (u'-555', -555),
                              ]
    good_values_default = [0,
                           5, 555, 555555,
                           -5, -555, -555555,
                           sys.maxint, -sys.maxint - 1,
                           ]
    str_values_default = [(0, '0'),
                          (5, '5'),
                          (555, '555'),
                          (555555, '555555'),
                          (-5, '-5'),
                          (-555, '-555'),
                          (-555555, '-555555'),
                          ]
    min_max_values = [
        # (value, min, max, is_valid),
        (-sys.maxint - 10000, None, None, True),
        (sys.maxint + 10000, None, None, True),
        (-100, -200, None, True),
        (-300, -200, None, False),
        (100, None, 200, True),
        (300, None, 200, False),
        (-100, -200, 200, True),
        (-300, -200, 200, False),
        (100, -200, 200, True),
        (300, -200, 200, False),
        ]


class TestFloat(Base, BaseTest):

    class FieldClass(field.Float): pass

    convert_values_default = [(0, 0.0),
                              (555, 555.0),
                              (-555, -555.0),
                              ('0', 0.0),
                              ('0.', 0.0),
                              ('555', 555.0),
                              ('555.55', 555.55),
                              ('-555', -555.0),
                              ('-555.55', -555.55),
                              (u'0', 0.0),
                              (u'0.', 0.0),
                              (u'555', 555.0),
                              (u'555.55', 555.55),
                              (u'-555', -555.0),
                              (u'-555.55', -555.55),
                              ]
    good_values_default = [0.0,
                           5.5, 555.555, 555555.5,
                           -5.5, -555.555, -555555.5,
                           ]
    str_values_default = [(0.0, '0.0'),
                          (5.5, '5.5'),
                          (555.555, '555.555'),
                          (55555.5, '55555.5'),
                          (-5.5, '-5.5'),
                          (-555.555, '-555.555'),
                          (-55555.5, '-55555.5'),
                          ]
    min_max_values = [
      # (value, min, max, is_valid),
      (-10000., None, None, True),
      (10000., None, None, True),
      (-100., -200., None, True),
      (-300., -200., None, False),
      (100., None, 200., True),
      (300., None, 200., False),
      (-100., -200., 200., True),
      (-300., -200., 200., False),
      (100., -200., 200., True),
      (300., -200., 200., False),
      ]


## class TestMoney(Base, BaseTest):

##     convert_values_default = [(0, 0.0),
##                               (55.555, 55.55),
##                               (-55.555, -55.55),
##                               ('55.55', 55.55),
##                               ('-55.55', -55.55),
##                               ('55.555', 55.55),
##                               ('-55.555', -55.55),
##                               (u'55.55', 55.55),
##                               (u'-55.55', -55.55),
##                               (u'55.555', 55.55),
##                               (u'-55.555', -55.55),
##                               ]
##     class FieldClass(field.Money): pass
##     good_values_default = [0.00,
##                            5.50, 555.67, 555678.90,
##                            -5.50, -555.67, -555678.90,
##                            ]
##     str_values_default = [(0.00, '0.00'),
##                           (5.50, '5.50'),
##                           (555.67, '555.67'),
##                           (555678.90, '555678.90'),
##                           (-5.50, '-5.50'),
##                           (-555.67, '-555.67'),
##                           (-555678.90, '-555678.90'),
##                           (55.551, '55.55'),
##                           ]
##     # XXX: Be sure to add min_max_values to this test
##     # when it is reactivated.


class TestDate(Base, BaseTest):

    class FieldClass(field.Date): pass

    good_values_default = [
        datetime.date(2004, 5, 5),
        datetime.date(1765, 4, 3),
        '2004-05-05',
        '1765-04-03',
        '05/05/2004',
        '04/03/1765',
        (2004, 5, 5),
        (1765, 4, 3),
        ]
    bad_values_default = [
        '0000-01-01',                   # year < minyear
        (0, 1, 1),
        '10000-01-01',                  # year > maxyear
        (10000, 1, 1),
        '2000-00-01',                   # month < 1
        (2000, 0, 1),
        '2000-13-01',                   # month > 12
        (2000, 13, 1),
        '2000-01-00',                   # day < 1
        (2000, 1, 0),
        '2000-01-32',                   # day > end of month
        (2000, 1, 32),
        ]
    convert_values_default = [
        ('2004-05-05', (2004, 5, 5)),
        ('2004-5-5', (2004, 5, 5)),
        ('05/05/2004', (2004, 5, 5)),
        ('5/5/2004', (2004, 5, 5)),
        ('1765-04-03', (1765, 4, 3)),
        ('1765-4-3', (1765, 4, 3)),
        ('04/03/1765', (1765, 4, 3)),
        ('4/3/1765', (1765, 4, 3)),
        ]
    min_max_values = [
        # (value, min, max, is_valid),
        (datetime.date(2004, 5, 5), None, None, True),
        (datetime.date(2004, 3, 3), datetime.date(2004, 2, 2), None, True),
        (datetime.date(2004, 1, 1), datetime.date(2004, 2, 2), None, False),
        (datetime.date(2004, 1, 1), None, datetime.date(2004, 2, 2), True),
        (datetime.date(2004, 3, 3), None, datetime.date(2004, 2, 2), False),
        (datetime.date(2004, 3, 3),
         datetime.date(2004, 2, 2), datetime.date(2004, 4, 4),
         True),
        (datetime.date(2004, 1, 1),
         datetime.date(2004, 2, 2), datetime.date(2004, 4, 4),
         False),
        (datetime.date(2004, 5, 5),
         datetime.date(2004, 2, 2), datetime.date(2004, 4, 4),
         False),
        ]


class TestDatetime(Base, BaseTest):

    class FieldClass(field.Datetime): pass

    good_values_default = [
        datetime.datetime(2004, 5, 5, 22, 32, 5),
        datetime.datetime(1765, 4, 3, 10, 11, 12),
        ]
    bad_values_default = [
        '0-5-5 1:2:3',
        '2000-0-5 1:2:3',
        '2000-13-5 1:2:3',
        '2000-1-0 1:2:3',
        '2000-1-32 1:2:3',
        '2000-1-1 24:2:3',
        '2000-1-1 1:60:3',
        ## XXX: This is actually valid and resolves to 2000-1-1 1:3:0
        # '2000-1-1 1:2:60',
        ]
    convert_values_default = [
        ('2004-05-05 22:32:05', (2004, 5, 5, 22, 32, 5, 0)),
        ('2004-05-05 22:32:05.920000', (2004, 5, 5, 22, 32, 5, 920000)),
        ('2004-5-5 22:32:05', (2004, 5, 5, 22, 32, 5, 0)),
        ('5/5/2004 22:32', (2004, 5, 5, 22, 32, 0, 0)),
        ('5/5/2004 22:32:05.8700', (2004, 5, 5, 22, 32, 5, 870000)),
        ('2004-05-05T22:32:05', (2004, 5, 5, 22, 32, 5, 0)),
        ('2004-05-05T22:32:05.1', (2004, 5, 5, 22, 32, 5, 100000)),
        ]
    min_max_values = [
        # (value, min, max, is_valid),
        (datetime.datetime(2004, 5, 5), None, None,
         True),
        (datetime.datetime(2004, 3, 3),
         datetime.datetime(2004, 2, 2), None,
         True),
        (datetime.datetime(2004, 1, 1),
         datetime.datetime(2004, 2, 2), None,
         False),
        (datetime.datetime(2004, 1, 1), None,
         datetime.datetime(2004, 2, 2),
         True),
        (datetime.datetime(2004, 3, 3), None,
         datetime.datetime(2004, 2, 2),
         False),
        (datetime.datetime(2004, 3, 3),
         datetime.datetime(2004, 2, 2), datetime.datetime(2004, 4, 4),
         True),
        (datetime.datetime(2004, 1, 1),
         datetime.datetime(2004, 2, 2), datetime.datetime(2004, 4, 4),
         False),
        (datetime.datetime(2004, 5, 5),
         datetime.datetime(2004, 2, 2), datetime.datetime(2004, 4, 4),
         False),
        ]


class TestBoolean(Base, BaseTest):

    class FieldClass(field.Boolean): pass

    convert_values_default = [(1, True),
                              (0, False),
                              ('True', True), # trueLabel
                              ('False', False), # falseLabel
                              ]
    good_values_default = [True, False]
    str_values_default = [(True, 'True'),
                          (False, 'False'),
                          ]


class TestHashedValue(Base, BaseTest):

    class FieldClass(field.HashedValue): pass

    def test_hash_differs_from_value(self):
        value = 'abcde'
        f = self.empty_field()
        f.set(value)
        assert value != f.get()

    def test_hash_always_different(self):
        value = 'abcde'
        f = self.empty_field()
        f.set(value)
        hash1 = f.get()
        f.set(value)
        hash2 = f.get()
        assert hash1 != hash2

    def test_value_comparison_success(self):
        value = 'abcde'
        f = self.empty_field()
        f.set(value)
        assert f.compare(value)
        f.set(value)
        assert f.compare(value)

    def test_value_comparison_failure(self):
        value = 'abcde'
        f = self.empty_field()
        f.set(value)
        wrongValue = 'fghij'
        assert not f.compare(wrongValue)

    def test_field_value_copy(self):
        value = 'abcde'
        # f1 represents the field used by the GUI.
        f1 = self.empty_field()
        f1.set(value)
        # f2 represents the persisted field, whose value is set based
        # on the value of f1
        f2 = self.empty_field()
        f2.set(f1.get())
        # f2 should still be able to be compared against the correct
        # value.
        assert f2.compare(value)

    def test_unassigned(self):
        value = field.UNASSIGNED
        f = self.empty_field()
        f.set(value)
        assert f.get() == value
        assert not f.compare(value)


class TestImage(object):

    def test_unicode_representation(self):
        f = field.Image(None, None)
        f.set('some-image-data')
        assert unicode(f) == u'(Binary data)'


class TestHashedPassword(object):

    def test_unicode_representation(self):
        f = field.HashedPassword(None, None)
        f.set('some-password')
        assert unicode(f) == u'(Encrypted)'

    def test_unicode_values(self):
        f = field.HashedPassword(None, None)
        value = u'some-unicode-password-\ucafe'
        f.set(value)
        assert f.compare(value)


class TestDeprecatedFields(object):

    def test_blob(self):
        body = '''
            class Foo(E.Entity):
                blob = f.blob()
            '''
        with warnings.catch_warnings(record=True) as w:
            t = DocTest(body)
            assert len(w) == 1
            assert w[-1].category is DeprecationWarning
            assert str(w[-1].message).startswith("'blob' is a deprecated")
            assert w[-1].lineno == 5

    def test_memo(self):
        body = '''
            class Foo(E.Entity):
                memo = f.memo()
            '''
        with warnings.catch_warnings(record=True) as w:
            t = DocTest(body)
            assert len(w) == 1
            assert w[-1].category is DeprecationWarning
            assert str(w[-1].message).startswith("'memo' is a deprecated")
            assert w[-1].lineno == 5

    def test_password(self):
        body = '''
            class Foo(E.Entity):
                password = f.password()
            '''
        with warnings.catch_warnings(record=True) as w:
            t = DocTest(body)
            assert len(w) == 1
            assert w[-1].category is DeprecationWarning
            assert str(w[-1].message).startswith("'password' is a deprecated")
            assert w[-1].lineno == 5

    def test_unicode(self):
        body = '''
            class Foo(E.Entity):
                name = f.unicode()
            '''
        with warnings.catch_warnings(record=True) as w:
            t = DocTest(body)
            assert len(w) == 1
            assert w[-1].category is DeprecationWarning
            assert str(w[-1].message).startswith("'unicode' is a deprecated")
            assert w[-1].lineno == 5
