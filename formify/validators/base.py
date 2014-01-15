import re
import weakref

from formify import _utils, exc
from formify.validators.mixins import ValidateMethodMixin, LengthValidationMixin


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
            self.validator.__module__, self.validator.__name__, id(self))

    def __call__(self, owner):
        return self.validator(owner=owner, *self.args, **self.kwargs)

    @property
    def validator(self):
        """Validator class."""
        return self._validator

    @property
    def args(self):
        """Positional args for validator class constructor."""
        return self._args

    @property
    def kwargs(self):
        """Named args for validator class constructor."""
        return self._kwargs


class Validator(ValidateMethodMixin):
    messages = {
        'conversion_error': 'Unable to convert to value of type %(python_type)r: %(exc)s',
        'required_error': 'This field is required'
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
        self.owner = owner
        self.errors = []
        self.value = None
        self.raw_value = None
        self(default)

    def __call__(self, value):
        return self.process(value)

    def process(self, value):
        self.errors = []
        self.raw_value = value
        if value is None:
            value = self.value = None
        else:
            value = self.value = self.try_convert(value)
        return value

    def convert(self, value):
        try:
            return self.python_type(value)
        except Exception, e:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type, exc=e)

    def try_convert(self, value):
        try:
            return self.convert(value)
        except exc.ConversionError, e:
            self.add_error(e.message_id, **e.params)

    def try_validate(self, value):
        try:
            self.validate(value)
        except exc.ValidationError, e:
            self.add_error(e.message_id, **e.params)
            return False
        else:
            return True

    def is_valid(self):
        if self.errors:
            return False
        elif self.required and self.raw_value is None:
            self.add_error('required_error')
            return False
        elif not self.try_validate(self.value):
            return False
        else:
            return True

    def add_error(self, message_id, **params):
        message = self.messages[message_id] % params
        self.errors.append(message)

    @property
    def owner(self):
        if self._owner is None:
           return self._owner
        else:
            return self._owner()

    @owner.setter
    def owner(self, value):
        if value is None:
            self._owner = value
        else:
            self._owner = weakref.ref(value)

    @property
    def python_type(self):
        raise NotImplementedError("'python_type' is not implemented in %r" % self.__class__)


class BaseString(Validator):

    @property
    def python_type(self):
        return unicode


class String(BaseString, LengthValidationMixin):
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

    def validate(self, value):
        if not self._compiled_pattern.match(value):
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

    def validate(self, value):
        if self.min_value is not None and self.max_value is not None:
            self._validate_value_range(value)
        elif self.min_value is not None:
            self._validate_min_value(value)
        elif self.max_value is not None:
            self._validate_max_value(value)

    def _validate_value_range(self, value):
        if not self.min_value <= value <= self.max_value:
            raise exc.ValidationError('value_out_of_range',
                min_value=self.min_value, max_value=self.max_value)

    def _validate_min_value(self, value):
        if value < self.min_value:
            raise exc.ValidationError('too_low', min_value=self.min_value)

    def _validate_max_value(self, value):
        if value > self.max_value:
            raise exc.ValidationError('too_high', max_value=self.max_value)


class Integer(Numeric):

    @property
    def python_type(self):
        return int


class ListOf(Validator, LengthValidationMixin):
    messages = dict(Validator.messages)
    messages.update({
        'too_short': 'Expecting at least %(min_length)s elements',
        'too_long': 'Expecting at most %(max_length)s elements',
        'length_out_of_range': 'Expected number of elements is between %(min_length)s and %(max_length)s',
        'inner_validator_error': 'At least one inner validator has failed'
    })

    def __init__(self, validator, min_length=None, max_length=None, **kwargs):
        super(ListOf, self).__init__(**kwargs)
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
        self.errors = []
        self.raw_value = value
        if value is None:
            self._value_validators = []
            self.value = None
        else:
            self._value_validators = self.__create_value_validators(value)
            self.value = [x.value for x in self._value_validators] or None
        return self.value

    def __create_value_validators(self, value):
        validators = []
        for v in (self.try_convert(value) or []):
            validator = self.validator(owner=self)
            validator.process(v)
            validators.append(validator)
        return validators

    def is_valid(self):
        status = super(ListOf, self).is_valid()
        if not status:
            return False
        for v in self:
            if not v.is_valid():
                status = False
        if not status:
            self.add_error('inner_validator_error')
        return status
