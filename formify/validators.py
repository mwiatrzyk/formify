import re

from formify import _utils, exc


class UnboundValidator(object):
    """Proxy class that wraps :class:`Validator` objects when created without
    owner."""

    def __init__(self, validator, *args, **kwargs):
        _utils.set_creation_order(self)
        self._validator = validator
        self._args = args
        self._kwargs = dict(kwargs)

    def __getattr__(self, name):
        return self._kwargs.get(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(UnboundValidator, self).__setattr__(name, value)
        else:
            self._kwargs[name] = value

    def __repr__(self):
        return "<%s.Unbound%s object at 0x%x>" % (
            self._validator.__module__, self._validator.__name__, id(self))

    def bind(self, owner):
        return self._validator(owner=owner, *self._args, **self._kwargs)


class Validator(object):
    """Common base class for all types.

    Instances of this class handle two kind of operations: type conversion and
    validation of converted value. These two operations are separated -
    conversion is invoked once :param:`raw_value` is set and validation once
    :meth:`is_valid` is called. Any failure causes list of errors to be filled
    with human-readable error description.
    """
    messages = {
        'unable_to_convert': 'Unable to convert to value of type %(python_type)r: %(exc)s',
        'field_is_required': 'This field is required'
    }

    def __new__(cls, *args, **kwargs):
        if 'owner' not in kwargs:
            return UnboundValidator(cls, *args, **kwargs)
        else:
            return object.__new__(cls, *args, **kwargs)

    def __init__(self, key=None, required=True, default=None, owner=None):
        self.key = key
        self.required = required
        self.default = default
        self.value = None
        self.raw_value = default
        self.errors = []
        self.validators = []

    def convert(self, value):
        try:
            return self.python_type(value)
        except ValueError, e:
            raise exc.ConversionError('unable_to_convert',
                value=value, python_type=self.python_type, exc=e)

    def try_convert(self, value):
        try:
            return self.convert(value)
        except exc.ConversionError, e:
            self.add_error(e.message_id, **e.params)

    def validate(self):
        pass

    def try_validate(self):
        try:
            self.validate()
        except exc.ValidationError, e:
            self.add_error(e.message_id, **e.params)
            return False
        else:
            return True

    def is_valid(self):
        if self.errors:
            return False
        elif self.required and self.raw_value is None:
            self.add_error('field_is_required')
            return False
        elif not self.try_validate():
            return False
        else:
            return True

    def add_error(self, message_id, **params):
        message = self.messages[message_id] % params
        self.errors.append(message)

    def add_validator(self, validator):
        self.validators.append(validator)

    @property
    def raw_value(self):
        return self._raw_value

    @raw_value.setter
    def raw_value(self, value):
        self._raw_value = value
        self.errors = []
        if value is None:
            self.value = None
        else:
            self.value = self.try_convert(value)

    @property
    def python_type(self):
        raise NotImplementedError("'python_type' is not implemented in %r" % self.__class__)


class BaseString(Validator):

    @property
    def python_type(self):
        return unicode


class String(BaseString):
    messages = dict(BaseString.messages)
    messages.update({
        'too_short': 'Expecting at least %(min_length)s characters',
        'too_long': 'Expecting at most %(max_length)s characters',
        'length_out_of_range': 'Expected number of characters is between %(min_length)s and %(max_length)s'
    })

    def __init__(self, min_length=None, max_length=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length

    @property
    def python_type(self):
        return unicode

    def validate(self):
        if self.min_length is not None and self.max_length is not None:
            self._validate_length_range()
        elif self.min_length is not None:
            self._validate_min_length()
        elif self.max_length is not None:
            self._validate_max_length()

    def _validate_length_range(self):
        if not self.min_length <= len(self.value) <= self.max_length:
            raise exc.ValidationError('length_out_of_range',
                min_length=self.min_length,
                max_length=self.max_length)

    def _validate_min_length(self):
        if len(self.value) < self.min_length:
            raise exc.ValidationError('too_short', min_length=self.min_length)

    def _validate_max_length(self):
        if len(self.value) > self.max_length:
            raise exc.ValidationError('too_long', max_length=self.max_length)


class Regex(BaseString):
    messages = dict(BaseString.messages)
    messages.update({
        'pattern_mismatch': 'Value does not match pattern %(pattern)s'
    })

    def __init__(self, pattern, flags=0, **kwargs):
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags
        self._compiled_pattern = re.compile(pattern, flags)

    def validate(self):
        if not self._compiled_pattern.match(self.value):
            raise exc.ValidationError('pattern_mismatch', pattern=self.pattern)


class Numeric(Validator):
    messages = dict(Validator.messages)
    messages.update({
        'too_low': 'Expecting value greater or equal to %(min_value)s',
        'too_high': 'Expecting value less or equal to %(max_value)s',
        'value_out_of_range': 'Expecting value between %(min_value)s and %(max_value)s'
    })

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super(Numeric, self).__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self):
        if self.min_value is not None and self.max_value is not None:
            self._validate_value_range()
        elif self.min_value is not None:
            self._validate_min_value()
        elif self.max_value is not None:
            self._validate_max_value()

    def _validate_value_range(self):
        if not self.min_value <= self.value <= self.max_value:
            raise exc.ValidationError('value_out_of_range',
                min_value=self.min_value, max_value=self.max_value)

    def _validate_min_value(self):
        if self.value < self.min_value:
            raise exc.ValidationError('too_low', min_value=self.min_value)

    def _validate_max_value(self):
        if self.value > self.max_value:
            raise exc.ValidationError('too_high', max_value=self.max_value)


class Integer(Numeric):

    @property
    def python_type(self):
        return int
