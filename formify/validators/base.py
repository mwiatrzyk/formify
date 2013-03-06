import re
import decimal

from formify import exc
from formify.validators import validator_property, Validator

__all__ = [
    'BaseString', 'String', 'Regex', 'Numeric', 'Int', 'Float', 'Decimal',
    'Bool']


class BaseString(Validator):
    """Common base class for all string validators."""
    python_type = unicode


class String(BaseString):
    """Validate unicode string values.

    :param length_max:
        maximal allowed length of output string
    :param length_min:
        minimal allowed length of output string

    Standalone usage examples:

    >>> validator = String()
    >>> validator(1)
    u'1'
    >>> validator('foo')
    u'foo'
    >>> String(3, 2).process('ab')
    u'ab'
    >>> String(3, 2).process('a')
    Traceback (most recent call last):
    ...
    ValidationError: number of characters must be between 2 and 3
    >>> String(3, 2).process('abcd')
    Traceback (most recent call last):
    ...
    ValidationError: number of characters must be between 2 and 3
    >>> String(3).process('abcd')
    Traceback (most recent call last):
    ...
    ValidationError: number of characters must not be greater than 3
    >>> String(length_min=3).process('ab')
    Traceback (most recent call last):
    ...
    ValidationError: number of characters must not be less than 3
    """

    def __init__(self, length_max=None, length_min=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self.length_max = length_max
        self.length_min = length_min

    def postvalidate(self, value, owner):
        value = super(String, self).postvalidate(value, owner)
        length_max = self.param('length_max', owner)
        length_min = self.param('length_min', owner)
        params = {
            'length_min': length_min,
            'length_max': length_max,
        }
        if length_min is not None and\
           length_max is not None and\
           not (length_min <= len(value) <= length_max):
            raise exc.ValidationError(
                "number of characters must be between %(length_min)s and "
                "%(length_max)s" % params)
        elif length_min is not None and\
             len(value) < length_min:
            raise exc.ValidationError(
                "number of characters must not be less than %(length_min)s" %
                params)
        elif length_max is not None and\
             len(value) > length_max:
            raise exc.ValidationError(
                "number of characters must not be greater than %(length_max)s"
                % params)
        return value


class Regex(BaseString):
    """Validate strings against given regular expression.

    >>> validator = Regex('[A-Z]{3}')
    >>> validator('ABC')
    u'ABC'
    >>> validator('abc')
    Traceback (most recent call last):
    ...
    ValidationError: value 'abc' does not match pattern '[A-Z]{3}'
    """

    def __init__(self, pattern, flags=0, **kwargs):
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags

    def postvalidate(self, value, owner):
        pattern = self.param('pattern', owner)
        flags = self.param('flags', owner)
        params = {
            'value': value,
            'pattern': pattern,
        }
        if not re.match(pattern, value, flags):
            raise exc.ValidationError(
                "value '%(value)s' does not match pattern '%(pattern)s'" %
                params)
        return value


class Numeric(Validator):
    """Common base class for all numeric validators."""

    def __init__(self, value_min=None, value_max=None, **kwargs):
        super(Numeric, self).__init__(**kwargs)
        self.value_min = value_min
        self.value_max = value_max

    def postvalidate(self, value, owner):
        value = super(Numeric, self).postvalidate(value, owner)
        value_min = self.param('value_min', owner)
        value_max = self.param('value_max', owner)
        params = {
            'value_min': value_min,
            'value_max': value_max,
        }
        if value_min is not None and\
           value_max is not None and\
           not (value_min <= value <= value_max):
            raise exc.ValidationError(
                "value must be between %(value_min)s and %(value_max)s" %
                params)
        elif value_min is not None and\
             value < value_min:
            raise exc.ValidationError(
                "value must not be less than %(value_min)s" % params)
        elif value_max is not None and\
             value > value_max:
            raise exc.ValidationError(
                "value must not be greater than %(value_max)s" % params)
        return value


class Int(Numeric):
    """Validate integer numbers.

    >>> validator = Int()
    >>> validator('foo')
    Traceback (most recent call last):
    ...
    ConversionError: unable to convert 'foo' to integer number
    >>> validator(123)
    123
    >>> validator('-11')
    -11
    >>> Int(2, 3).process(2)
    2
    >>> Int(2, 3).process(1)
    Traceback (most recent call last):
    ...
    ValidationError: value must be between 2 and 3
    >>> Int(2).process(1)
    Traceback (most recent call last):
    ...
    ValidationError: value must not be less than 2
    >>> Int(value_max=2).process(3)
    Traceback (most recent call last):
    ...
    ValidationError: value must not be greater than 2
    """
    python_type = int

    def convert(self, value, owner):
        try:
            return self.python_type(value)
        except ValueError:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to integer number" %
                {'value': value})


class Float(Numeric):
    """Floating point input validator.

    >>> validator = Float(0, 3.14)
    >>> validator('-5.35')
    Traceback (most recent call last):
    ...
    ValidationError: value must be between 0 and 3.14
    >>> validator('foo')
    Traceback (most recent call last):
    ...
    ConversionError: unable to convert 'foo' to floating point number
    >>> validator(3.14)
    3.14
    """
    python_type = float

    def convert(self, value, owner):
        try:
            return self.python_type(value)
        except ValueError, e:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to floating point number" %
                {'value': value})


class Decimal(Numeric):
    """Decimal input validator.

    >>> decimal = Decimal()
    >>> decimal(10)
    Decimal('10')
    >>> decimal(10.5)
    Decimal('10.5')
    >>> decimal('3.14159')
    Decimal('3.14159')
    >>> decimal(True)
    Decimal('1')
    >>> decimal({})
    Traceback (most recent call last):
    ...
    TypeError: Cannot convert {} to Decimal
    >>> decimal('12d')
    Traceback (most recent call last):
    ...
    ConversionError: unable to convert '12d' to decimal number
    """
    python_type = decimal.Decimal

    def convert(self, value, owner):
        try:
            return self.python_type(value)
        except decimal.InvalidOperation, e:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to decimal number" %
                {'value': value})


class Bool(Validator):
    """Boolean input validator.

    >>> validator = Bool()
    >>> validator(True)
    True
    >>> validator(1)
    True
    >>> validator(None)
    False
    >>> validator('')
    False
    >>> validator('yes')
    True
    >>> validator('foo')
    Traceback (most recent call last):
    ...
    ConversionError: cannot convert 'foo' to boolean
    """
    python_type = bool

    def __init__(self, trues=None, falses=None, **kwargs):
        super(Bool, self).__init__(**kwargs)
        self.trues = trues
        self.falses = falses

    def convert(self, value, owner):
        if not value:
            return False
        elif not isinstance(value, basestring):
            return self.python_type(value)
        else:
            value = value.lower()
            trues = set(self.param('trues', owner) or ['1', 'y', 'on', 'yes', 'true'])
            falses = set(self.param('falses', owner) or ['0', 'n', 'off', 'no', 'false'])
            if value in trues:
                return True
            elif value in falses:
                return False
            else:
                raise exc.ConversionError(
                    "cannot convert '%(value)s' to boolean" %
                    {'value': value})
