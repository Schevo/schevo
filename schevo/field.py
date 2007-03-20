"""Provides Field classes, which are like properties, only smarter.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.lib import optimize

import datetime
import md5
import random
import sys
import time

from schevo import base
from schevo.constant import ANY, RESTRICT, UNASSIGNED
import schevo.error
import schevo.fieldspec
import schevo.namespace


# Filters for calls to field_map methods.

def not_expensive(field):
    return not field.expensive

def not_fget(field):
    return not field.fget

def not_hidden(field):
    return not field.hidden


class FieldMeta(type):
    """Create field constuctors for every Field class."""

    def __new__(cls, class_name, bases, class_dict):
        # Only do something if creating a Field subclass.
        if class_name != 'NoSlotsField':
            slots = ['assigned', '_initial', '_instance', '_rev', '_value']
            class_dict['__slots__'] = slots
        return type.__new__(cls, class_name, bases, class_dict)

    def __init__(cls, class_name, bases, class_dict):
        type.__init__(cls, class_name, bases, class_dict)
        # Create a field constructor.
        def_name = class_name[0].lower() + class_name[1:]
        class def_class(schevo.fieldspec.FieldDefinition):
            BaseFieldClass = cls
        def_class.__name__ = def_name
        cls._def_class = def_class
        cls._def_name = def_name
        # Only if this global schema definition variable exists.
        if schevo.namespace.SCHEMADEF is not None:
            # Add this class to the field classes namespace.
            schevo.namespace.SCHEMADEF.F._set(cls.__name__, cls)
            # Add a field constructor to the field constructors namespace.
            schevo.namespace.SCHEMADEF.f._set(def_name, def_class)


class Field(base.Field):
    """Field class.

    Somewhat like a property, only smarter, and not a descriptor.

    allow_empty: True if value can be empty. No checks are made based
    on this attribute in the default validate() routine, so if the
    Field subclass is for a type where the concept of 'empty' makes
    sense, be sure to check this attribute and validate the value
    against it.

    assigned: True if a value was assigned after field was created.

    data_type: Python data type of the value.

    default: Default value, stored as a tuple of (value,).  If value
    is callable, it will be called with no arguments to obtain a
    default value.  A tuple is used so that instantiating a Field
    class does not result in the function being treated as an
    instancemethod.

    doc: Documentation for the field.

    error_message: A custom error message to include with exceptions,
    or None if the default message should be used.

    expensive: True if the field is a calculated field whose `fget`
    function is time-consuming.  Provides a hint to ignore the field
    in certain views such as list views.

    fget: A tuple of (function,) for the function to use to retrieve
    the value of the field, or None if default mechanism should be
    used.  A tuple is used so that instantiating a Field class does
    not result in the function being treated as an instancemethod.

    hidden: True if field should be hidden from users.

    label: Descriptive label for the field that can be used for
    reporting, the GUI field label, the column heading, etc.

    max_size: Maximum size allowed, or None for no limit.

    min_size: Minimum size allowed, or None for no limit.

    max_value: Maximum value allowed, or None for no limit.

    min_value: Minimum value allowed, or None for no limit.

    notice: A tuple of (notice type, notice text) describing a notice
    for this field, or None for no notice.

    preferred_values: A list of preferred values, or None if not
    applicable.

    readonly: True if value cannot be modified directly.

    required: True if a value must be supplied.

    subdued_values: A list of subdued values, or None if not
    applicable.  These values can be thought of as 'less important'
    values.  They are typically used to show values in a GUI using
    less contrast than normal.

    valid_values: A list of valid values, or None if not applicable.

    was: The name of the field in the previous schema, or None if the
    field was not renamed since the previous schema.
    """

    __metaclass__ = FieldMeta  # Defines __slots__ as well.

    # Keeps the original field class around when subclassing in schema
    # definitions.
    BaseFieldClass = None

    allow_empty = False
    data_type = None
    default = (UNASSIGNED, )
    doc = ''
    error_message = None
    expensive = False
    fget = None
    hidden = False
    label = None
    max_size = None
    min_size = None
    max_value = None
    min_value = None
    notice = None
    preferred_values = None
    readonly = False
    required = True
    subdued_values = None
    valid_values = None
    was = None

    _name = None

    @property
    def instance(self):
        return self._instance

    @property
    def name(self):
        return self._name

    @property
    def rev(self):
        return self._rev

    @property
    def value(self):
        return self.get()

    def __init__(self, instance, value=None, rev=None):
        """Create a Field instance for an instance with a given value.

        instance: usually an Entity, Transaction or Query instance.
        
        value: optional initial value, without validation checking.

        rev: revision of the instance containing the value, if
        instance is an Entity.
        """
        self.assigned = False
        # The instance to which this value applies.
        # This should not change once it is set.
        self._instance = instance
        # Initial value for the field, usually for existing fields.
        if value is not None:
            self._value = value
        else:
            # Otherwise a field is created with a value of UNASSIGNED.
            self._value = UNASSIGNED
        # Initial value to support was_changed() method.
        self._initial = self._value
        # Initial rev for the field, usually for existing fields.
        if rev is not None:
            self._rev = rev
        else:
            # Otherwise a field is created with an initial rev of -1.
            self._rev = -1

    def _initialize(self, value):
        """Initialize the field with a value."""
        self._initial = value
        self._value = value

    @classmethod
    def _init_kw(cls, kw):
        """Apply keyword arguments that were specified in a
        FieldDefinition.  Called before _init_args."""
        if 'default' in kw:
            kw['default'] = (kw['default'], )
        for name, value in kw.iteritems():
            setattr(cls, name, value)

    @classmethod
    def _init_args(cls, args):
        """Apply positional arguments that were specified in a
        FieldDefinition.  Called after _init_kw."""
        pass

    @classmethod
    def _init_final(cls):
        """Do finalization of class initialization."""
        pass

    def __repr__(self):
        return '<%s field; value:%r>' % (self.__class__.__name__, self._value)

    def __str__(self):
        v = self.get()
        if v is UNASSIGNED:
            return '<UNASSIGNED>'
        else:
            return str(v)

    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED:
            return u'<UNASSIGNED>'
        else:
            return unicode(v)

    def check(self, value):
        """Return True if the value passes all validation checks."""
        try:
            self.validate(value)
            return True
        except:
            return False

    def convert(self, value, db=None):
        """Convert the value to a different type.

        If `db` is specified, may take into account that database when
        converting values.
        """
        return value

    def copy(self):
        """Return a copy of this field that can be modified."""
        FieldClass = self.__class__
        new_field = FieldClass(None, None)
        new_field.__dict__.update(self.__dict__)
        return new_field
        
    def get(self):
        """Return the field value."""
        if self.fget is not None:
            return self.fget[0](self._instance)
        else:
            return self._value

    def reversible(self, value=None):
        """Return a reversible string representation of the field value, or
        a different value if ``value`` is not None.

        The return value of this method should result in a string
        that, when fed into the `convert` method, results in the
        original field value.

        If not possible, return `None`.
        """
        if value is None:
            value = self.get()
        if value is UNASSIGNED:
            return u''
        else:
            return unicode(self)

    def set(self, value):
        """Set the field value."""
        # None is never allowed.
        if value is None:
            msg = '%s value of None is not allowed by %s %r' % (
                self._name, self._instance, self._instance)
            self._raise(ValueError, msg)
        # Readonly fields cannot be changed directly.
        if self.readonly:
            msg = '%s field is readonly and cannot be changed on %s %r' % (
                self._name, self._instance, self._instance)
            self._raise(AttributeError, msg)
        # Apply any value conversions.
        if value is not UNASSIGNED:
            value = self.convert(value)
##         # If the new value is no different than the current value, return.
##         if hasattr(self, '_value') and value == self._value:
##             return
        # Change the value.
        self._value = value
        # Mark this field as having been assigned.
        self.assigned = True

    def validate(self, value):
        """Validate the value, raising an error on failure.

        Used by the persistence layer and has strict validation
        requirements.
        """
        valid_values = self.valid_values
        if value is UNASSIGNED:
            if self.required:
                # A value must be provided.
                msg = '%s value is required by %s' % (
                    self._name, self._instance)
                self._raise(AttributeError, msg)
        elif valid_values is not None and value not in valid_values:
            # Valid values.
            msg = '%s %s must be one of the valid values %r, not %r %r' % (
                self._instance, self._name, valid_values, value, type(value))
            self._raise(ValueError, msg)

    def verify(self, value):
        """Verify the value, raising an error on failure.

        Used by non-persistence layers and has less strict validation
        requirements.
        """
        return self.validate(value)

    def was_changed(self):
        return self._value != self._initial

    def _raise(self, exctype, msg):
        custom = self.error_message
        if custom is not None:
            msg = custom
        raise exctype(msg)

    def _validate_min_max_value(self, value):
        """Validate `value` against minimum and maximum value of this
        field."""
        if not self.required and value is UNASSIGNED:
            return
        min_value = self.min_value
        convert = self.convert
        converted_value = convert(value)
        if min_value is not None and converted_value < convert(min_value):
            msg = '%s value must be >= %r' % (self._name, min_value)
            self._raise(ValueError, msg)
        max_value = self.max_value
        if max_value is not None and converted_value > convert(max_value):
            msg = '%s value must be <= %r' % (self._name, max_value)
            self._raise(ValueError, msg)

    def _validate_min_max_size(self, value):
        """Validate `value` against minimum and maximum size of this
        field."""
        if not self.required and value is UNASSIGNED:
            return
        value_len = len(self.convert(value))
        if self.allow_empty and value_len == 0:
            return
        min_size = self.min_size
        if min_size is not None and value_len < int(min_size):
            msg = '%s value length must be >= %r' % (self._name, min_size)
            self._raise(ValueError, msg)
        max_size = self.max_size
        if max_size is not None and value_len > int(max_size):
            msg = '%s value length must be <= %r' % (self._name, max_size)
            self._raise(ValueError, msg)


# --------------------------------------------------------------------


class HashedValue(Field):
    """Field which stores a value as a one-way hash.

    Useful for storing passwords.

    When you assign or set the value of this field, it stores a
    one-way hash of that value in the field rather than the plaintext
    value itself.  To see if another plaintext value 'matches' the
    stored hash, use the compare() method.

    hashHeader: The value that is prepended to all hashed values, to
    allow for passing hashed values from field to field unchanged.
    Override this in your subclass if you by chance plan to hash the
    16 random bytes that the default hashHeader consists of.
    """

    data_type = str
    hashHeader = '\xb9\xc8\xfd\xb8\xca\xb7\xc9\xea' \
                 '\xde\xf5\xc7\xac\x9b\xfa\xfc\xa6'

    def __str__(self):
        v = self._value
        if v is UNASSIGNED:
            return Field.__str__(self)
        else:
            return '(Encrypted)'

    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED:
            return Field.__unicode__(self)
        else:
            return u'(Encrypted)'

    def compare(self, value):
        """Return True if value matches this field's one way hash."""
        try:
            return self.hashCompare(value, self._value)
        except:
            # If an exception is raised, the value obviously isn't the
            # same.
            return False

    def convert(self, value, db=None):
        """Return the one-way hash of value."""
        if value is UNASSIGNED:
            return value
        if value.startswith(self.hashHeader):
            # Short-circuit if the value is already hashed.
            return value
        else:
            return self.hashEncode(value)

    def hashCompare(self, value, hashedValue):
        """Compare value to one-way hash, returning True if matching.

        Override this method if you want to use a different hashing
        algorithm.
        """
        headerLen = len(self.hashHeader)
        salt = hashedValue[headerLen:headerLen+12]
        encodedValue = self.hashEncode(value, salt)
        return (encodedValue == hashedValue)

    def hashEncode(self, value, salt=None):
        """Encode a value as a one-way hash and return the hash.

        Override this method if you want to use a different hashing
        algorithm.
        """
        if salt is None:
            salt = ''
            for x in xrange(12):
                salt += chr(random.randrange(0, 256))
        md = md5.md5()
        md.update(salt)
        md.update(value)
        digest = md.digest()
        hashedValue = salt + digest
        return self.hashHeader + hashedValue


class String(Field):
    """String field class.

    monospace: Hint to a UI to display contents using a monospace
    font.
    """

    data_type = str
    monospace = False

    def convert(self, value, db=None):
        """Convert the value to a string."""
        if value is UNASSIGNED:
            return value
        return str(value)

    def validate(self, value):
        Field.validate(self, value)
        if not self.allow_empty and value == '':
            msg = '%s value must not be empty.' % self._name
            self._raise(ValueError, msg)
        self._validate_min_max_size(value)


class Path(String):
    """File path field class.

    Intended to designate a string field as something that stores a
    path to a file or directory.

    directory_only: True if only a directory path should be stored in
    the field.

    file_only: True if only a file path should be stored in the field.
    """

    data_type = str
    directory_only = False
    file_only = False


class Unicode(Field):
    """Unicode field class.

    monospace: Hint to a UI to display contents using a monospace
    font.
    """

    data_type = unicode
    monospace = False

    def convert(self, value, db=None):
        """Convert the value to a Unicode string."""
        if value is UNASSIGNED:
            return value
        return unicode(value)

    def validate(self, value):
        Field.validate(self, value)
        if not self.allow_empty and value == u'':
            msg = '%s value must not be empty.' % self._name
            self._raise(ValueError, msg)
        self._validate_min_max_size(value)


class Memo(Unicode):
    """Memo field class.

    Intended to designate a unicode string field as something that
    stores a multi-line memo rather than a single-line string.
    """

    data_type = unicode


class Password(Unicode):
    """Password field class.

    Intended to designate a unicode field as something that stores a
    plaintext string, but whose value shouldn't be exposed in a UI.
    """

    data_type = unicode

    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED:
            return Field.__unicode__(self)
        else:
            return u'(Hidden)'

    def reversible(self, value=None):
        return u''


# --------------------------------------------------------------------


class Blob(Field):
    """Binary large object field class."""

    data_type = object

    def convert(self, value, db=None):
        """Convert the value to a string."""
        if value is UNASSIGNED:
            return value
        return str(value)

    def __str__(self):
        v = self._value
        if v is UNASSIGNED:
            return Field.__str__(self)
        else:
            return '(Binary data)'
        
    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED:
            return Field.__unicode__(self)
        else:
            return u'(Binary data)'
        

class Image(Blob):
    """Image field class."""

    data_type = object


# --------------------------------------------------------------------


class Integer(Field):
    """Integer field class."""

    data_type = int

    def convert(self, value, db=None):
        """Convert the value to an integer."""
        if value == '':
            value = UNASSIGNED
        if value is UNASSIGNED:
            return value
        return int(value)

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        self._validate_min_max_value(value)


class Float(Field):
    """Float field class."""

    data_type = float

    def convert(self, value, db=None):
        """Convert the value to a floating point number."""
        if value == '':
            value = UNASSIGNED
        if value is UNASSIGNED:
            return value
        return float(value)

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        self._validate_min_max_value(value)


class Money(Field):
    """Money field class.

    This should really use a decimal type, and offer three options of
    rounding:  Chop, Add Half and Chop, and Bankers.

    For now, convert() performs chop rounding and when the others are
    added, chop rounding will remain the default.

    fract_digits: The number of digits after the decimal point.
    """

    data_type = float
    fract_digits = 2

    def __str__(self):
        v = self._value
        if v is UNASSIGNED:
            return Field.__str__(self)
        else:
            format = '%.' + str(self.fract_digits) + 'f'
            return format % float(v)

    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED:
            return Field.__unicode__(self)
        else:
            format = u'%.' + unicode(self.fract_digits) + u'f'
            return format % float(v)

    def reversible(self, value=None):
        if value is None:
            value = self._value
        if value is UNASSIGNED:
            return u''
        else:
            return unicode(self)

    def convert(self, value, db=None):
        """Convert the value to a monetary value."""
        if value == '':
            value = UNASSIGNED
        if value is UNASSIGNED:
            return value
        return round(float(value), self.fract_digits)

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        self._validate_min_max_value(value)


# --------------------------------------------------------------------


class Date(Field):
    """Date field class.

    Uses the datetime.date type from Python 2.3+ to store values.
    """

    data_type = datetime.date

    def convert(self, value, db=None):
        """Convert the value to a datetime.datetime object."""
        if value is UNASSIGNED:
            return value
        elif isinstance(value, tuple):
            try:
                year, month, day = value
                d = datetime.date(year, month, day)
            except ValueError:
                msg = '%r not a valid ISO or US date.' % (value, )
                self._raise(ValueError, msg)
            return value
        elif isinstance(value, float):
            # A factory already exists to create a datetime.datetime
            # instance from a timestamp.
            d = datetime.date.fromtimestamp(value)
            return (d.year, d.month, d.day)
        elif isinstance(value, basestring):
            if len(value.split('-')) == 3:
                # Parse ISO date.
                year, month, day = (int(x) for x in value.split('-'))
                # Ensure that it converts to a date correctly.
                try:
                    d = datetime.date(year, month, day)
                except ValueError:
                    msg = '%r not a valid ISO or US date.' % value
                    self._raise(ValueError, msg)
                return (year, month, day)
            elif len(value.split('/')) == 3:
                # Parse US date.
                month, day, year = (int(x) for x in value.split('/'))
                # Ensure that it converts to a date correctly.
                try:
                    d = datetime.date(year, month, day)
                except ValueError:
                    msg = '%r not a valid ISO or US date.' % value
                    self._raise(ValueError, msg)
                return (year, month, day)
            else:
                msg = '%r not a valid ISO or US date.' % value
                self._raise(ValueError, msg)
        else:
            # If the value is not represented as a timestamp, assume
            # that it has the same attributes as a datetime object
            # itself.
            return (value.year, value.month, value.day)

    def get(self):
        v = Field.get(self)
        if isinstance(v, tuple):
            year, month, day = v
            v = datetime.date(year, month, day)
        return v

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        self._validate_min_max_value(value)


class Datetime(Field):
    """Date and time field class.

    Uses the datetime.datetime type from Python 2.3+ to store values.
    """

    data_type = datetime.datetime
    format = '%Y-%m-%dT%H:%M:%S'

    def convert(self, value, db=None):
        """Convert the value to a datetime.datetime object."""
        if value is UNASSIGNED:
            pass
        elif isinstance(value, tuple):
            # Fill out missing hour, minute, second, microseconds.
            if 3 <= len(value) < 7:
                items = list(value)
                while len(items) < 7:
                    items.append(0)
                value = tuple(items)
            # Make sure the tuple represents a valid datetime.
            try:
                datetime.datetime(*value)
            except:
                raise
        elif isinstance(value, float):
            # A factory already exists to create a datetime.datetime
            # instance from a timestamp.
            dt = datetime.datetime.fromtimestamp(value)
            value = (dt.year, dt.month, dt.day, dt.hour, dt.minute,
                     dt.second, dt.microsecond)
        elif isinstance(value, basestring):
            # Get microseconds first if available.
            parts = value.split('.', 2)
            if len(parts) == 2:
                value, microsecond = parts
                if len(microsecond) > 6:
                    # Chop.
                    microsecond = microsecond[:6]
                elif len(microsecond) < 6:
                    # Pad.
                    microsecond = microsecond + ('0' * (6 - len(microsecond)))
                microsecond = int(microsecond)
            else:
                microsecond = 0
            # Try our format, then some default formats.
            formats = [
                self.format,
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y%m%d%H%M%S',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y %H:%M',
                ]
            for format in formats:
                try:
                    tt = time.strptime(value, format)
                except ValueError:
                    continue
                else:
                    break
            else:
                self._raise(ValueError, '%r not a valid datetime' % value)
            ts = time.mktime(tt)
            dt = datetime.datetime.fromtimestamp(ts)
            value = (dt.year, dt.month, dt.day, dt.hour, dt.minute,
                     dt.second, microsecond)
        else:
            # If the value is not represented as a timestamp, assume
            # that it has the same attributes as a datetime object
            # itself.
            value = (value.year, value.month, value.day, value.hour,
                     value.minute, value.second, value.microsecond)
        return value

    def get(self):
        v = Field.get(self)
        if isinstance(v, tuple):
            year, month, day, hour, minute, second, microsecond = v
            v = datetime.datetime(year, month, day, hour, minute,
                                  second, microsecond)
        return v

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        self._validate_min_max_value(value)


# --------------------------------------------------------------------


class Boolean(Field):
    """Boolean field class.

    Stores a boolean value and provides attributes for UI to inspect
    to get preferred labels for representing True and False.
    """

    data_type = bool
    false_label = unicode(False)
    true_label = unicode(True)
    unassigned_label = None

    def __str__(self):
        v = self._value
        if v is UNASSIGNED and self.unassigned_label is not None:
            return self.unassigned_label
        elif v is UNASSIGNED:
            return Field.__str__(self)
        else:
            if v:
                return str(self.true_label)
            else:
                return str(self.false_label)

    def __unicode__(self):
        v = self.get()
        if v is UNASSIGNED and self.unassigned_label is not None:
            return unicode(self.unassigned_label)
        elif v is UNASSIGNED:
            return Field.__unicode__(self)
        else:
            if v:
                return unicode(self.true_label)
            else:
                return unicode(self.false_label)

    def convert(self, value, db=None):
        """Convert the value to a boolean value."""
        if value is UNASSIGNED:
            return value
        elif value == self.false_label:
            return False
        elif value == self.true_label:
            return True
        return bool(value)


# --------------------------------------------------------------------


class Entity(Field):
    """Entity instance field class.

    allow_create: set to True if UI should give users the option of
    creating new instances when displaying this field.

    allow_update: set to True if UI should give users the option of
    updating instances displayed in this field.

    allow: if this attribute has a list of names of Entity
    classes in it, you can only assign an instance of one of those
    classes to the field.

    on_delete: Action to take when the entity referenced by this field
    is deleted.  If set to CASCADE, the entity that this field is in
    will be deleted.  If set to RESTRICT (the default), a
    DeleteRestricted error will be raised.  If set to UNASSIGN, this
    field will be set to UNASSIGNED if possible, or a KeyCollision
    error will be raised.
    """

    data_type = object
    allow_create = True
    allow_update = False
    allow = set()
    on_delete = {}
    on_delete_default = RESTRICT

    @classmethod
    def _init_kw(cls, kw):
        on_delete = cls.on_delete = cls.on_delete.copy()
        kw_on_delete = kw.pop('on_delete', {})
        if not isinstance(kw_on_delete, dict):
            cls.on_delete_default = kw_on_delete
        allow = cls.allow = set(cls.allow)
        kw_allow = kw.pop('allow', [])
        if isinstance(kw_allow, str):
            kw_allow = [kw_allow]
        elif kw_allow is ANY:
            kw_allow = [ANY]
        cls._init_args(kw_allow)
        for name, value in kw.iteritems():
            setattr(cls, name, value)

    @classmethod
    def _init_args(cls, args):
        allow = cls.allow
        for arg in args:
            if isinstance(arg, str):
                allow.add(arg)
                if arg not in cls.on_delete:
                    cls.on_delete[arg] = cls.on_delete_default
            elif isinstance(arg, tuple):
                arg, on_delete = arg
                allow.add(arg)
                cls.on_delete[arg] = on_delete
            elif arg is ANY:
                allow.add(arg)

    @classmethod
    def _init_final(cls):
        if not cls.allow:
            raise schevo.error.AmbiguousFieldDefinition(
                'Must specify allow=ANY or specific extent names.')
        if cls.allow == frozenset([ANY]):
            cls.allow = set()

    def convert(self, value, db=None):
        instance = self._instance
        if instance is None:
            return Field.convert(self, value, db)
        else:
            if value is UNASSIGNED:
                return value
            if isinstance(value, basestring):
                if value == '':
                    return UNASSIGNED
                else:
                    try:
                        name, oid = value.split('-')
                        oid = int(oid)
                        return db.extent(name)[oid]
                    except (AttributeError, KeyError, IndexError, ValueError):
                        return UNASSIGNED
            else:
                return value

    def reversible(self, value=None):
        if value is None:
            value = self.get()
        if value is UNASSIGNED:
            return u''
        else:
            return u'%s-%i' % (value.sys.extent.name, value.sys.oid)
        
    def reversible_valid_values(self, db):
        """Returns a list of (reversible, value) tuples for the valid
        values of this field."""
        values = []
        if not self.required:
            values.append(UNASSIGNED)
        if self.valid_values is not None:
            values.extend(self.valid_values)
        elif self.allow:
            for extent_name in sorted(self.allow):
                for entity in db.extent(extent_name):
                    values.append(entity)
        else:
            # XXX: This branch is if all entities are valid.  Do we want
            # to return nothing?
            values = []
        r = self.reversible
        return [(r(value), value) for value in values]

    def validate(self, value):
        """Validate the value, raising an error on failure."""
        Field.validate(self, value)
        allow = self.allow
        if isinstance(value, tuple):
            return
        elif value is UNASSIGNED and not self.required:
            return
        elif not isinstance(value, base.Entity):
            msg = '%s value must be an Entity instance, not %r %r' % (
                self._name, type(value), value)
            self._raise(TypeError, msg)
        elif allow and value.sys.extent.name not in allow:
            msg = '%s value must be an instance of %r, not %r %r' % (
                self._name, allow, type(value), value)
            self._raise(TypeError, msg)

    def verify(self, value):
        """Verify the value, raising an error on failure."""
        if value is UNASSIGNED:
            if not self.required:
                return
            else:
                msg =  '%s value is required' % self._name
                self._raise(AttributeError, msg)
        allow = self.allow
        extent_name = value.sys.extent.name
        if allow and extent_name not in allow:
            msg = "%s value's class must be %r, not %r" % (
                self._name, allow, extent_name)
            self._raise(TypeError, msg)
        if not isinstance(value, base.Entity):
            msg = '%s value must be an entity instance.' % self._name
            self._raise(TypeError, msg)


optimize.bind_all(sys.modules[__name__])  # Last line of module.


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
