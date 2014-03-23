# formify/validators/base.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

"""Core part of validation system."""

import copy
import weakref

from formify import _utils, exc

__all__ = ['UnboundValidator', 'ValidatorMeta', 'Validator']


class UnboundValidator(object):
    """Proxy class that wraps :class:`Validator` objects when created without
    owner.

    Objects of this class are created by ``__new__`` method of
    :class:`Validator` class when constructor is called wihout ``owner``
    parameter and not in standalone mode. The role of this class is to wrap
    original :class:`Validator` subclass object with all constructor parameters
    and allow later binding to some owner.
    """

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
    """Metaclass for :class:`Validator`."""

    @property
    def __message_formatters__(cls):
        """Map of custom message formatters."""
        formatters = {}
        for name in dir(cls):
            value = getattr(cls, name)
            for message_id in getattr(value, '_ffy_message_formatter', []):
                formatters[message_id] = value
        return formatters


class BaseValidator(object):
    """Common base class for validators and mixins.

    This class provides set of methods that can be extended using mixin
    pattern. Any mixin that is going to extend functionality of validator class
    must inherit from this base class.
    """

    def validate(self, value):
        """Validate given value of known type.

        If validation fails, this method should raise
        :exc:`~formify.exc.ValidationError` exception. If no exception is
        thrown, ``value`` is said to be valid.
        """


class Validator(BaseValidator):
    """Base class for all validators.

    :param key:
        validator's key under which validator is accessible from its owner. By
        default this is set to validator's attribute name
    :param optional:
        set to ``True`` to mark validator as optional. Validators that are not
        optional (default) require a value. Lack of value causes validation
        process to fail in such case
    :param default:
        validator's default value
    :param owner:
        validator's owner. This can be other validator or
        :class:`~formify.schema.Schema` class object
    :param standalone:
        when set to ``True``, validator is created in standalone mode and can
        be used without schema
    :param messages:
        map of messages to update default ones with
    :param preprocessors:
        list of validator preprocessors

    .. attribute:: messages

        Map of message templates used when rendering errors.

        When raising :exc:`~formify.exc.FormifyError` exceptions, message
        template is searched in this map and rendered with exception params.
        Formatting of messages can be customized with
        :func:`~formify.decorators.message_formatter` decorator.

    .. attribute:: errors

        List of validator's processing or conversion errors.

    .. attribute:: raw_value

        Last processed input value.

    .. attribute:: value

        Last successfuly converted :attr:`raw_value`.
    """
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

    def __init__(self, key=None, optional=False, default=None, owner=None,
            standalone=False, messages=None, preprocessors=None,
            postprocessors=None):
        self.preprocessors = preprocessors or []
        self.postprocessors = postprocessors or []
        self.key = key
        self.optional = optional
        self.default = default
        self.owner = owner
        self.standalone = standalone
        if messages is not None:
            self.__update_messages(messages)
        self(_utils.maybe_callable(default))

    def __update_messages(self, messages):
        self.messages = dict(self.__class__.messages)
        self.messages.update(messages)

    def __call__(self, value):
        """Convert input value to instance of :attr:`python_type`.

        Calling this method will reset previous validator state, i.e.
        :attr:`errors`, :attr:`raw_value` and :attr:`value` properties, and set
        them up according to processing result for ``value``.

        If processing was successful, converted value is returned and
        validator's :attr:`value` is initialized with it. Otherwise, ``None``
        is returned and list of errors is filled with messages specifying what
        went wrong.
        """
        self.errors = []
        self.raw_value = self.__copy_if_mutable(value)
        if self.__needs_conversion(value):
            value = self.preprocess(value)
            value = self.try_convert(value)
        if value is not None:
            value = self.postprocess(value)
        self.value = value
        return value

    def __copy_if_mutable(self, value):
        if _utils.is_mutable(value):
            return copy.deepcopy(value)
        else:
            return value

    def __needs_conversion(self, value):
        return value is not None and not isinstance(value, self.python_type)

    def preprocess(self, value):
        """Execute chain of preprocessors on given value."""
        for func in self.preprocessors:
            value = func(self, value)
        return value

    def postprocess(self, value):
        """Execute chain of postprocessors on given value."""
        for func in self.postprocessors:
            value = func(self, value)
        return value

    def convert(self, value):
        """Convert given value to instance of :attr:`python_type` object.

        If conversion is successful, converted value is returned. Otherwise,
        :exc:`~formify.exc.ConversionError` is raised.

        This method does not change validator's state.
        """
        try:
            return self.python_type(value)
        except Exception, e:
            raise exc.ConversionError('conversion_error',
                value=value, python_type=self.python_type)

    def try_convert(self, value):
        """Convert ``value`` to instance of :attr:`python_type` object and
        raise no exceptions.

        This method calls :meth:`convert` and catches
        :exc:`~formify.exc.ConversionError` it may raise. If conversion is
        successful, converted ``value`` is returned. Otherwise, conversion
        error message is added to :attr:`errors` list and ``None`` is returned.

        This method may change validator's state.
        """
        try:
            return self.convert(value)
        except exc.ConversionError, e:
            self.add_error(e.message_id, **e.params)

    def try_validate(self, value):
        """Validate previously converted ``value`` and raise no exceptions.

        If validation is successful, ``True`` is returned. Otherwise error
        message is added to :attr:`errors` list and ``False`` is returned.
        """
        try:
            self.validate(value)
        except exc.ValidationError, e:
            self.add_error(e.message_id, **e.params)
            return False
        else:
            return True

    def is_valid(self):
        """Check if validator is valid.

        This is done by checking :attr:`errors` list, ``optional`` flag and
        finally by calling :meth:`try_validate`.

        Returns ``True`` if validator is valid or ``False`` otherwise.
        """
        if self.errors:
            return False
        elif not self.optional and self.raw_value is None:
            self.add_error('required_error')
            return False
        elif not self.try_validate(self.value):
            return False
        else:
            return True

    def format_message(self, message_id, **params):
        """Fill message template with params and return formatted message.

        If custom message formatter is defined for ``message_id`` (with
        :func:`~formify.decorators.message_formatter` decorator) it is called
        with same parameters. If not, default message formatter is following::

            def format_message(self, message_id, **params):
                return self.messages[message_id] % params

        :param message_id:
            key of message template in :attr:`messages` map
        :param `**params`:
            message template parameters
        """
        formatter = self.__class__.__message_formatters__.get(message_id)
        if formatter is not None:
            return formatter(self, message_id, **params)
        else:
            return self.messages[message_id] % params

    def add_error(self, message_id, **params):
        """Add error to list of errors.

        This method uses :meth:`format_message` to prepare error message to be
        added.

        :param message_id:
            key of message template in :attr:`messages` map
        :param `**params`:
            message template parameters
        """
        message = self.format_message(message_id, **params)
        self.errors.append(message)

    def add_preprocessor(self, f):
        """Add given function to the end of preprocessing chain."""
        self.preprocessors.append(f)

    def add_postprocessor(self, f):
        """Add given function to the end of postprocessing chain."""
        self.postprocessors.append(f)

    @property
    def owner(self):
        """Owner of this validator.

        If validator has no owner this is ``None``.
        """
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
        """Python type this validator converts to.

        This property is not defined by default and therefore must be
        implemented in all subclasses.
        """
        raise NotImplementedError("'python_type' is not implemented in %r" % self.__class__)
