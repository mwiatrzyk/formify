import re
import decimal

from formify import exc
from formify.validators import Validator

__all__ = [
    'BaseString', 'String', 'Regex', 'Numeric', 'Integer', 'Float', 'Decimal',
    'Boolean']


class BaseString(Validator):
    """Common base class for all string validators."""

    @property
    def python_type(self):
        return unicode


class String(BaseString):
    """String input validator.

    :param length_max:
        maximal string length
    :param length_min:
        minimal string length
    """

    def __init__(self, length_max=None, length_min=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self.length_max = length_max
        self.length_min = length_min

    def postvalidate(self, value):
        value = super(String, self).postvalidate(value)
        params = {
            'length_min': self.length_min,
            'length_max': self.length_max}
        if self.length_min is not None and\
           self.length_max is not None and\
           not (self.length_min <= len(value) <= self.length_max):
            raise exc.ValidationError(
                "number of characters must be between %(length_min)s and "
                "%(length_max)s" % params)
        elif self.length_min is not None and\
             len(value) < self.length_min:
            raise exc.ValidationError(
                "number of characters must not be less than %(length_min)s" %
                params)
        elif self.length_max is not None and\
             len(value) > self.length_max:
            raise exc.ValidationError(
                "number of characters must not be greater than %(length_max)s"
                % params)
        return value


class Regex(BaseString):
    """Validates input against given regular expression.

    :param pattern:
        regular expression pattern
    :param flags:
        regular expression flags (see :mod:`re` for details)
    """

    def __init__(self, pattern, flags=0, **kwargs):
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags

    def postvalidate(self, value):
        value = super(Regex, self).postvalidate(value)
        params = {
            'value': value,
            'pattern': self.pattern}
        if not re.match(self.pattern, value, self.flags):
            raise exc.ValidationError(
                "value '%(value)s' does not match pattern '%(pattern)s'" %
                params)
        return value


class Numeric(Validator):
    """Base class for validators performing numeric input validation.

    :param value_min:
        minimal allowed input value
    :param value_max:
        maximal allowed input value
    """

    def __init__(self, value_min=None, value_max=None, **kwargs):
        super(Numeric, self).__init__(**kwargs)
        self.value_min = value_min
        self.value_max = value_max

    def postvalidate(self, value):
        value = super(Numeric, self).postvalidate(value)
        params = {
            'value_min': self.value_min,
            'value_max': self.value_max}
        if self.value_min is not None and\
           self.value_max is not None and\
           not (self.value_min <= value <= self.value_max):
            raise exc.ValidationError(
                "value must be between %(value_min)s and %(value_max)s" %
                params)
        elif self.value_min is not None and\
             value < self.value_min:
            raise exc.ValidationError(
                "value must not be less than %(value_min)s" % params)
        elif self.value_max is not None and\
             value > self.value_max:
            raise exc.ValidationError(
                "value must not be greater than %(value_max)s" % params)
        return value


class Integer(Numeric):
    """Validates integer number input."""

    @property
    def python_type(self):
        return int

    def from_string(self, value):
        try:
            return self.python_type(value)
        except ValueError:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to integer number" %
                {'value': value})


class Float(Numeric):
    """Validates floating point number input."""

    @property
    def python_type(self):
        return float

    def from_string(self, value):
        try:
            return self.python_type(value)
        except ValueError:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to floating point (a.k.a. real) "
                "number" % {'value': value})


class Decimal(Numeric):
    """Validates decimal number input."""

    @property
    def python_type(self):
        return decimal.Decimal

    def from_string(self, value):
        try:
            return self.python_type(value)
        except decimal.InvalidOperation:
            raise exc.ConversionError(
                "unable to convert '%(value)s' to decimal number" %
                {'value': value})


class Boolean(Validator):
    """Validates boolean value input.

    :param trues:
        sequence of phrases that evaluate to ``True``. Default case-insensitive
        true-evaluating phrases are: ``1``, ``y``, ``on``, ``yes``, ``true``
    :param falses:
        sequence of phrases that evaluate to ``False``. Default
        case-insensitive false-evaluating phrases are: ``0``, ``n``, ``off``,
        ``no``, ``false``
    """

    @property
    def python_type(self):
        return bool

    def __init__(self, trues=None, falses=None, **kwargs):
        super(Boolean, self).__init__(**kwargs)
        self.trues = trues
        self.falses = falses

    def from_string(self, value):
        if not value:  # empty string
            return False
        else:
            value = value.lower()
            trues = set(self.trues or ['1', 'y', 'on', 'yes', 'true'])
            falses = set(self.falses or ['0', 'n', 'off', 'no', 'false'])
            if value in trues:
                return True
            elif value in falses:
                return False
            else:
                raise exc.ConversionError(
                    "cannot convert '%(value)s' to boolean" %
                    {'value': value})
