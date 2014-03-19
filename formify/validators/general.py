# formify/validators/general.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import re
import weakref
import hashlib
import decimal
import datetime
import collections

from formify import exc
from formify.decorators import message_formatter
from formify.validators.base import Validator
from formify.validators.mixins import LengthValidationMixin, RangeValidationMixin

__all__ = ['BaseString', 'String', 'Regex', 'URL', 'Email', 'Numeric',
    'Integer', 'Float', 'Decimal', 'Boolean', 'DateTime', 'Password', 'AnyOf',
    'BaseChoice', 'Choice', 'MultiChoice', 'EqualTo', 'List', 'Map']


class BaseString(Validator):
    """Common base class for string validators.

    Converts to: ``unicode``
    """

    @property
    def python_type(self):
        return unicode


class String(BaseString, LengthValidationMixin):
    """Validate string input.

    :param min_length:
        minimal length of input value
    :param max_length:
        maximal length of input value
    """
    messages = dict(BaseString.messages)
    messages.update({
        'value_too_short': 'Expecting at least %(min_length)s characters',
        'value_too_long': 'Expecting at most %(max_length)s characters',
        'value_length_out_of_range': 'Expected number of characters is between %(min_length)s and %(max_length)s'
    })

    def __init__(self, min_length=None, max_length=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length


class Regex(BaseString):
    """Validate string input against defined regular expression.

    :param pattern:
        regular expression pattern
    :param flags:
        regular expression flags (see :mod:`re` for details)
    """
    messages = dict(BaseString.messages)
    messages.update({
        'pattern_mismatch': 'Value does not match pattern %(pattern)s'
    })

    def __init__(self, pattern, flags=0, **kwargs):
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags
        self._compiled_pattern = re.compile(pattern, flags)

    def validate(self, value):
        if not self._compiled_pattern.match(value):
            raise exc.ValidationError('pattern_mismatch', pattern=self.pattern)


class URL(Regex):
    """Validate URL address."""
    messages = dict(Regex.messages)
    messages.update({
        'pattern_mismatch': 'Invalid URL address'
    })

    def __init__(self, **kwargs):
        super(URL, self).__init__(r'^((http|https|ftp)\://)?([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,3}(/\S*)?$', **kwargs)


class Email(Regex):
    """Validate e-mail address."""
    messages = dict(Regex.messages)
    messages.update({
        'pattern_mismatch': 'Invalid e-mail address'
    })

    def __init__(self, **kwargs):
        super(Email, self).__init__(r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}$', **kwargs)


class Numeric(Validator, RangeValidationMixin):
    """Base class for numeric validators.

    :param min_value:
        minimal input value
    :param max_value:
        maximal input value
    """
    messages = dict(Validator.messages)
    messages.update({
        'value_too_low': 'Expecting value greater or equal to %(min_value)s',
        'value_too_high': 'Expecting value less or equal to %(max_value)s',
        'value_out_of_range': 'Expecting value between %(min_value)s and %(max_value)s'
    })

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super(Numeric, self).__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value


class Integer(Numeric):
    """Validate integer number input.

    Converts to: ``int``
    """

    @property
    def python_type(self):
        return int


class Float(Numeric):
    """Validate float number input.

    Converts to: ``float``
    """

    @property
    def python_type(self):
        return float


class Decimal(Numeric):
    """Validate decimal number input.

    Converts to: :class:`decimal.Decimal`
    """

    @property
    def python_type(self):
        return decimal.Decimal


class Boolean(Validator):
    """Validate boolean input.

    Converts to: ``bool``

    If string input value is given it is checked against true- or
    false-evaluating phrases. By default these are:

    * 1, y, yes, on, true (for ``True``)
    * 0, n, no, off, false (for ``False``)

    If non-string input value is given it is simply converted to ``bool``.

    Conversion fails if input value is not one of true- or false-evaluating
    phrases (in case of string input) or if conversion to ``bool`` fails (in
    case of non-string input).

    :param trues:
        specify custom true-evaluating phrases
    :param falses:
        specify custom false-evaluating phrases
    """
    trues = set(['1', 'y', 'yes', 'on', 'true'])
    falses = set(['0', 'n', 'no', 'off', 'false'])

    def __init__(self, trues=None, falses=None, **kwargs):
        super(Boolean, self).__init__(**kwargs)
        if trues is not None:
            self.trues = set(trues)
        if falses is not None:
            self.falses = set(falses)

    def convert(self, value):
        if isinstance(value, basestring):
            return self.__convert_string(value)
        else:
            return self.__convert_non_string(value)

    def __convert_non_string(self, value):
        try:
            return bool(value)
        except Exception, e:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type)

    def __convert_string(self, value):
        if value in self.trues:
            return True
        elif value in self.falses:
            return False
        else:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type)

    @property
    def python_type(self):
        return bool


class DateTime(Validator, RangeValidationMixin):
    """Validate date/time input.

    Converts to: :class:`datetime.datetime`

    This validator allows only string input data - other types will cause
    conversion error.

    :param fmt:
        expected format of input value (see :meth:`~datetime.datetime.strptime`)
    :param min_value:
        minimal allowed date/time
    :param max_value:
        maximal allowed date/time
    """
    messages = dict(Validator.messages)
    messages.update({
        'conversion_error': 'Input date/time does not match format %(fmt)s',
        'invalid_input': 'Can only parse strings',
        'value_too_low': 'Minimal date is %(min_value)s',
        'value_too_high': 'Maximal date is %(max_value)s',
        'value_out_of_range': 'Expecting date between %(min_value)s and %(max_value)s'
    })

    @message_formatter('value_too_low', 'value_too_high', 'value_out_of_range')
    def _format_date_time(self, message_id, min_value=None, max_value=None):
        if min_value is not None:
            min_value = self.__to_string(min_value)
        if max_value is not None:
            max_value = self.__to_string(max_value)
        return self.messages[message_id] % {
            'min_value': min_value,
            'max_value': max_value}

    def __to_string(self, value):
        return datetime.datetime.strftime(value, self.fmt)

    def __init__(self, fmt, min_value=None, max_value=None, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        self.fmt = fmt
        self.min_value = min_value
        self.max_value = max_value

    def convert(self, value):
        if not isinstance(value, basestring):
            raise exc.ConversionError('invalid_input')
        else:
            return self.__from_string(value)

    def __from_string(self, value):
        try:
            return datetime.datetime.strptime(value, self.fmt)
        except ValueError:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type, fmt=self.fmt)

    @property
    def python_type(self):
        return datetime.datetime


class Password(String):
    """Validate password input.

    This validator accepts string input and creates hash for it using specified
    hash algorithm. Hashed value is then used as output value.

    :param hash_algorithm:
        name of hash algorithm to be used (``sha1`` by default). See
        :mod:`hashlib` for details
    """

    def __init__(self, hash_algorithm='sha1', **kwargs):
        super(Password, self).__init__(**kwargs)
        self.hash_algorithm = hash_algorithm

    def convert(self, value):
        value = super(Password, self).convert(value)
        self._converted_value = value
        return self.__create_hash(value)

    def __create_hash(self, value):
        hash_obj = hashlib.new(self.hash_algorithm)
        hash_obj.update(value)
        return hash_obj.hexdigest()

    def validate(self, value):
        super(Password, self).validate(self._converted_value)


class AnyOf(Validator):
    """Validates input agains any of given validators.

    This validator tries all of given subvalidators when converting value.
    First one that was able to convert input value is then used. Later, when
    validating, previously found validator is used, but another one is tried
    (if there are any left) if validation fails.

    :param validators:
        list of subvalidators
    """

    def __init__(self, validators, **kwargs):
        self.validators = validators
        super(AnyOf, self).__init__(**kwargs)

    def process(self, value):
        self.raw_value = value
        self._index_of_current = -1
        self._bound_validators = [x(owner=self) for x in self.validators]
        for i, validator in enumerate(self._bound_validators):
            if validator.process(value) is not None:
                self._index_of_current = i
                return self.value

    def try_validate(self, value):
        for i in xrange(self._index_of_current, len(self._bound_validators)):
            validator = self._bound_validators[i]
            if validator.process(value) is not None:
                if validator.is_valid():
                    self._index_of_current = i
                    return True
        else:
            return False

    @property
    def validator(self):
        return self._bound_validators[self._index_of_current]

    @property
    def errors(self):
        return self.validator.errors

    @property
    def value(self):
        return self.validator.value

    @property
    def python_type(self):
        return self.validator.python_type


class BaseChoice(Validator):
    """Base class for choice validators.

    Choice validators allow one (or more) predefined constant input values and
    disallow all other.

    :param options:
        map of choice options (with choice value as key and choice name as
        value)
    :param key_type:
        type of option keys (``str`` by default)
    """

    def __init__(self, options, key_type=str, **kwargs):
        super(BaseChoice, self).__init__(**kwargs)
        self.options = options
        self.key_type = key_type

    @property
    def options(self):
        """Ordered map of enum options."""
        return self._options

    @options.setter
    def options(self, value):
        self._options = collections.OrderedDict(value)


class Choice(BaseChoice):
    """Validates if input data matches any of predefined options."""
    messages = dict(Validator.messages)
    messages.update({
        'invalid_option': 'Invalid option: %(key)s'
    })

    def validate(self, value):
        super(Choice, self).validate(value)
        if value not in self.options:
            raise exc.ValidationError('invalid_option', key=value)

    @property
    def python_type(self):
        return self.key_type


class MultiChoice(BaseChoice):
    """Validates if every item of input data set matches any of predefined
    options."""
    messages = dict(Validator.messages)
    messages.update({
        'invalid_options': 'Invalid options: %(keys)s',
        'key_conversion_error': 'Unable to convert %(key)r to %(key_type)r object'
    })

    def try_convert(self, value):
        value = super(MultiChoice, self).try_convert(value)
        if value is None:
            return value
        result = self.python_type()
        for v in value:
            result.add(self.__try_convert_key(v))
        return result

    def __try_convert_key(self, key):
        try:
            return self.__convert_key(key)
        except exc.ConversionError, e:
            self.add_error(e.message_id, **e.params)

    def __convert_key(self, key):
        try:
            return self.key_type(key)
        except Exception, e:
            raise exc.ConversionError('key_conversion_error',
                key=key, key_type=self.key_type)

    def validate(self, value):
        super(MultiChoice, self).validate(value)
        common_options = set(self.options).intersection(value)
        if common_options != value:
            raise exc.ValidationError('invalid_options',
                keys=value.difference(common_options))

    @property
    def python_type(self):
        return set


class EqualTo(Validator):
    """Checks if input value is equal to value of another validator.

    This validator requires owner and therefore cannot be used in standalone
    mode.

    :param key:
        key of validator to compare input with
    """
    messages = dict(Validator.messages)
    messages.update({
        'not_equal': 'Values are not equal'
    })

    def __init__(self, key, **kwargs):
        if 'owner' not in kwargs:
            raise TypeError("owner is required for %r validator" % self.__class__)
        super(EqualTo, self).__init__(**kwargs)
        self.key = key

    def try_convert(self, value):
        try:
            return self.validator.convert(value)
        except exc.ConversionError, e:
            self.__add_external_error(e.message_id, **e.params)

    def __add_external_error(self, message_id, **params):
        message = self.validator.format_message(message_id, **params)
        self.errors.append(message)

    def validate(self, value):
        super(EqualTo, self).validate(value)
        if self.value != self.validator.value:
            raise exc.ValidationError('not_equal')

    @property
    def validator(self):
        return self.owner[self.key]

    @property
    def python_type(self):
        return self.validator.python_type


class List(Validator, LengthValidationMixin):
    """Validates list of input data using given validator.

    :param validator:
        validator used to validate input data
    """
    messages = dict(Validator.messages)
    messages.update({
        'too_short': 'Expecting at least %(min_length)s elements',
        'too_long': 'Expecting at most %(max_length)s elements',
        'length_out_of_range': 'Expected number of elements is between %(min_length)s and %(max_length)s',
        'inner_validator_error': 'At least one inner validator has failed'
    })

    def __init__(self, validator, min_length=None, max_length=None, **kwargs):
        super(List, self).__init__(**kwargs)
        self.validator = validator
        self.min_length = min_length
        self.max_length = max_length
        self._value_validators = []

    def __iter__(self):
        for validator in self._value_validators:
            yield validator

    def __len__(self):
        return len(self._value_validators)

    def __getitem__(self, index):
        return self._value_validators[index]

    @property
    def python_type(self):
        return list

    def process(self, value):
        value = super(List, self).process(value)
        self._value_validators = self.__create_value_validators(value)
        for i, validator in enumerate(self._value_validators):
            value[i] = validator.value
        return value

    def __create_value_validators(self, value):
        validators = []
        for v in (value or []):
            validator = self.validator(owner=self)
            validator.process(v)
            validators.append(validator)
        return validators

    def is_valid(self):
        status = super(List, self).is_valid()
        if not status:
            return False
        for v in self:
            if not v.is_valid():
                status = False
        if not status:
            self.add_error('inner_validator_error')
        return status


class Map(Validator):
    """Validates map of input data using corresponding map of validators.

    :param validators:
        map of validators. This can be dict or :class:`~formify.schema.Schema`
        class object.
    :param strict_processing:
        enable or disable strict processing of input data. If strict processing
        is enabled (default), any key given in input data that does not have
        corresponding validator will cause :exc:`KeyError` to be raised. If
        strict processing is disabled such keys will be silently ignored.
    """
    messages = dict(Validator.messages)
    messages.update({
        'inner_validator_error': 'Inner validator has failed'
    })

    class _ValueProxy(object):

        def __init__(self, owner):
            self._owner = owner

        @property
        def _owner(self):
            return self.__owner()

        @_owner.setter
        def _owner(self, value):
            self.__owner = weakref.ref(value)

        @property
        def _value(self):
            result = {}
            for k, v in self._owner.validators.iteritems():
                result[k] = v.value
            return result

        def __repr__(self):
            return repr(self._value)

        def __eq__(self, other):
            return self._value == other

        def __getitem__(self, key):
            return self._owner.validators[key].value

        def __setitem__(self, key, value):
            self._owner.validators[key].process(value)

        def __getattr__(self, name):
            return self[name]

        def __setattr__(self, name, value):
            if name.startswith('_'):
                super(Map._ValueProxy, self).__setattr__(name, value)
            else:
                self[name] = value

        def keys(self):
            return self._owner.validators.keys()

    def __init__(self, validators, strict_processing=True, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.strict_processing = strict_processing
        self.add_postprocessor(self.__postprocess)
        if hasattr(validators, '__validators__'):
            self.validators = self.__bind_validators(validators.__validators__)
        else:
            self.validators = self.__bind_validators(validators)

    @staticmethod
    def __postprocess(self, value):
        for k, v in value.items():
            if self.strict_processing or k in self.validators:
                value[k] = self.validators[k].process(v)
            else:
                del value[k]
        return self._ValueProxy(self)

    def __bind_validators(self, validators):
        bound = collections.OrderedDict()
        for k, v in validators.iteritems():
            bound[k] = v(owner=self)
        return bound

    def __iter__(self):
        for k in self.validators:
            yield k

    def __getitem__(self, key):
        return self.validators[key]

    @property
    def python_type(self):
        return dict

    def is_valid(self):
        status = super(Map, self).is_valid()
        if not status:
            return False
        for v in self.validators.itervalues():
            if not v.is_valid():
                status = False
        if not status:
            self.add_error('inner_validator_error')
        return status
