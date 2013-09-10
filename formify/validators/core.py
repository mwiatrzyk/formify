import re
import decimal
import hashlib

from formify import exc
from formify.undefined import Undefined
from formify.validators import Validator
from formify.utils.collections import OrderedDict


class Group(Validator):
    __visit_name__ = 'schema'

    def __init__(self, schema_cls=None, **kwargs):
        super(Group, self).__init__(**kwargs)
        self.schema_cls = schema_cls

    def itervalidators(self):
        for value in self.cls.__validators__.itervalues():
            yield value


class BaseString(Validator):
    """Generic string input validator."""
    __visit_name__ = 'basestring'

    @property
    def python_type(self):
        return unicode


class String(BaseString):
    """String input validator.

    :param length_max:
        maximal string length
    :param length_min:
        minimal string length
    :param multiline:
        if ``True``, multiline input field will be used when rendering this
        validator
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


class Text(String):
    """Multiline version of :class:`String` validator."""
    __visit_name__ = 'text'


class Password(BaseString):
    """Password input validator.

    :param hashfunc:
        hash function to be used to encode password. Following values are
        supported:

        string name
            specify algorithm name within :mod:`hashlib` module

        callable
            single-argument callable taking raw password and returning hashed
            password

        ``None``
            use raw passwords
        """
    __visit_name__ = 'password'

    def __init__(self, hashfunc='sha1', **kwargs):
        super(Password, self).__init__(**kwargs)
        self.hashfunc = hashfunc

    def postvalidate(self, value):
        value = super(Password, self).postvalidate(value)
        if self.hashfunc is None:
            return value
        elif callable(self.hashfunc):
            value = self.hashfunc(value)
        else:
            hashfunc = getattr(hashlib, self.hashfunc, None)
            if hashfunc is not None:
                value = hashfunc(value).hexdigest()
            else:
                raise ValueError("unknown hash function %r" % self.hashfunc)
        return value


class Regex(BaseString):
    """Validate input with given regular expression.

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
    """Generic numeric input validator.

    :param value_min:
        minimal allowed input value
    :param value_max:
        maximal allowed input value
    """
    __visit_name__ = 'numeric'

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
    """Integer number input validator."""

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
    """Floating point number input validator."""

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
    """Decimal number input validator."""

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
    """Boolean value input validator.

    :param trues:
        sequence of phrases that evaluate to ``True``. Default case-insensitive
        true-evaluating phrases are: ``1``, ``y``, ``on``, ``yes``, ``true``
    :param falses:
        sequence of phrases that evaluate to ``False``. Default
        case-insensitive false-evaluating phrases are: ``0``, ``n``, ``off``,
        ``no``, ``false``
    """
    __visit_name__ = 'boolean'

    def __init__(self, trues=None, falses=None, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = False  # make it False by default to avoid 'required missing' errors
        super(Boolean, self).__init__(**kwargs)
        self.trues = trues
        self.falses = falses

    @property
    def python_type(self):
        return bool

    def from_string(self, value):
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


class Choice(Validator):
    __visit_name__ = 'choice'

    def __init__(self, options, python_type=str, multivalue=False, **kwargs):
        super(Choice, self).__init__(
            python_type=python_type, multivalue=multivalue, **kwargs)
        self.options = options

    @property
    def python_type(self):
        return self._python_type

    @python_type.setter
    def python_type(self, value):
        self._python_type = value

    @property
    def multivalue(self):
        return self._multivalue

    @multivalue.setter
    def multivalue(self, value):
        self._multivalue = value

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        if hasattr(value, 'items'):
            value = sorted((k, v) for k, v in value.items())
        self._options = OrderedDict(value)

    def postvalidate(self, value):
        if self.multivalue:
            for v in value:
                if v not in self.options:
                    raise exc.ValidationError("invalid choice")
        else:
            if value not in self.options:
                raise exc.ValidationError("invalid choice")
        return super(Choice, self).postvalidate(value)

    def is_selected(self, value):
        if self.value is Undefined:
            return False
        elif self.multivalue:
            return self.from_string(value) in self.value
        else:
            return self.from_string(value) == self.value
