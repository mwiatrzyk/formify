# formify/validators/base.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import weakref

from formify import _utils, exc
from formify.validators.mixins import ValidatorMixin

__all__ = ['UnboundValidator', 'Validator']


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


class ValidatorMeta(type):

    @property
    def __message_formatters__(cls):
        formatters = {}
        for name in dir(cls):
            value = getattr(cls, name)
            for key in getattr(value, '_ffy_message_formatter_keys', []):
                formatters[key] = value
        return formatters


class Validator(ValidatorMixin):
    __metaclass__ = ValidatorMeta
    messages = {
        'conversion_error': 'Unable to convert %(value)r to %(python_type)r object',
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
        elif not isinstance(value, self.python_type):
            value = self.value = self.try_convert(value)
        else:
            self.value = value
        return value

    def convert(self, value):
        try:
            return self.python_type(value)
        except Exception, e:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type)

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

    def format_message(self, message_id, **params):
        formatter = self.__class__.__message_formatters__.get(message_id)
        if formatter is not None:
            return formatter(self, message_id, **params)
        else:
            return self.messages[message_id] % params

    def add_error(self, message_id, **params):
        message = self.format_message(message_id, **params)
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
