import re
import weakref
import collections

from formify import _utils, exc
from formify.validators.mixins import (
    ValidatorMixin, LengthValidatorMixin, ValueValidatorMixin)


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


class Validator(ValidatorMixin):
    messages = {
        'conversion_error': 'Unable to convert to value of type %(python_type)r: %(exc)s',
        'required_error': 'This field is required'
    }

    def __new__(cls, *args, **kwargs):
        if kwargs.get('standalone', False):
            return object.__new__(cls, owner=object(), *args, **kwargs)
        elif 'owner' not in kwargs:
            return UnboundValidator(cls, *args, **kwargs)
        else:
            return object.__new__(cls, *args, **kwargs)

    def __init__(self, key=None, required=True, default=None, owner=None, standalone=False, messages=None):
        self.key = key
        self.required = required
        self.default = default
        self.owner = owner
        self.standalone = standalone
        if messages is not None:
            self.__update_messages(messages)
        self.process(default)

    def __update_messages(self, messages):
        self.messages = dict(self.__class__.messages)
        self.messages.update(messages)

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


class String(BaseString, LengthValidatorMixin):
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


class Numeric(Validator, ValueValidatorMixin):
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

    @property
    def python_type(self):
        return int


class Float(Numeric):

    @property
    def python_type(self):
        return float


class List(Validator, LengthValidatorMixin):
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
    messages = dict(Validator.messages)
    messages.update({
        'inner_validator_error': 'Inner validator has failed'
    })

    def __init__(self, validators, **kwargs):
        super(Map, self).__init__(**kwargs)
        if hasattr(validators, '__validators__'):
            self.validators = self.__bind_validators(validators.__validators__)
        else:
            self.validators = self.__bind_validators(validators)

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

    def process(self, value):
        value = super(Map, self).process(value)
        for k, v in (value or {}).iteritems():
            value[k] = self.validators[k].process(v)
        return value

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
