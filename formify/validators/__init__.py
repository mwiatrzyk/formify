import re
import decimal
import weakref
import hashlib

from formify import exc, event
from formify.utils import helpers
from formify.undefined import Undefined
from formify.utils.collections import OrderedDict

__all__ = [
    'Validator', 'BaseString', 'String', 'Regex', 'Numeric', 'Integer',
    'Float', 'Decimal', 'Boolean', 'Choice']


class Validator(object):
    """Base class for all validators providing core functionality."""
    __visit_name__ = 'validator'

    def __init__(self, **kwargs):
        helpers.set_creation_order(self)

        # The purpose of this variable is to restore original validator's state
        # once validator is bound to schema
        self._bind_kwargs = dict(kwargs)

        # Read only properties
        self._key = kwargs.pop('key', None)
        self._schema = None
        self._raw_value = Undefined
        self._value = Undefined
        self._errors = []

        # Read and write properties
        self.label = kwargs.pop('label', None)
        self.default = kwargs.pop('default', Undefined)
        self.description = kwargs.pop('description', None)
        self.required = kwargs.pop('required', True)

        # Remaining custom read and write properties
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, name, value):
        super(Validator, self).__setattr__(name, value)
        if not name.startswith('_'):  # Keep track of changed public properties
            self._bind_kwargs[name] = value

    def _raise_if_unbound(self, func, excs, *args, **kwargs):
        """Call given function with provided args and kwargs and return its
        value.

        If exception occurs (one of listed *excs*) do following:

        for unbound validator
            raise exception

        for bound validator
            add exception description to list of current validator's errors and
            return ``Undefined`` object

        :param func:
            function to be called
        :param excs:
            exception or tuple tuple of exceptions to be catched by
            ``try...except`` block
        :param *args:
            function's args
        :param **kwargs:
            function's named args
        """
        try:
            return func(*args, **kwargs)
        except excs, e:
            if self.is_bound():
                self.errors.append(unicode(e))
                return Undefined
            else:
                raise

    def _typecheck(self, value):
        """A helper to perform correct type checking of processed value depending on
        :attr:`multivalue` state."""
        if self.multivalue:
            for v in value:
                if not self.typecheck(v):
                    return False
            return True
        else:
            return self.typecheck(value)

    def _from_string(self, value):
        """A helper to perform correct from string conversion of processed
        value depending on :attr:`multivalue` state."""
        if self.multivalue:
            for i in xrange(len(value)):
                if isinstance(value[i], basestring):
                    value[i] = self.from_string(value[i])
            return value
        elif isinstance(value, basestring):
            return self.from_string(value)
        else:
            return value

    def is_bound(self):
        """Check if this validator is bound to schema."""
        return self._schema is not None

    def bind(self, schema):
        """Bind validator to given schema.

        This method returns new bound validator based on current one. Original
        validator (the one for which this method was called) remains unchanged.
        """
        if self.is_bound():
            raise exc.AlreadyBound("%r -> %r" % (self, self.schema))

        # Create bound validator instance
        # Use custom defined function to do this if registered as 'bind' event
        # listener
        binders = event.get_listeners(self, 'bind')
        if not binders:
            bound = self.__class__(**self._bind_kwargs)
        else:
            bound = binders[-1](self.schema, self.key, self.__class__, self._bind_kwargs)

        # Reset properties that cannot be modified
        bound._key = self._key
        bound._schema = weakref.ref(schema)

        # Forward all event retrieval requests to validator originally created
        # as schema attribute
        event.alias_of(bound, self, event.F_READ_ACCESS)

        # Bind newly created validator to schema and return
        schema._bound_validators[self._key] = bound
        return bound

    def unbind(self):
        """Unbind this validator from current schema.

        If this validator was not bound to any schema,
        :exc:`~formify.exc.NotBound` is raised.
        """
        if not self.is_bound():
            raise exc.NotBound(repr(self))
        del self.schema._bound_validators[self._key]
        self._schema = None

    def process(self, value):
        """Process value by running prevalidators, converters and
        postvalidators.

        This method returns processed value. Also, if validator is bound, it
        sets up :param:`raw_value` and :param:`value` params.
        """

        # Expect value to be a sequence and convert it to list in case of
        # multivalue validators
        if self.multivalue:
            value = list(value)

        # Initialize raw_value, value and error container
        if self.is_bound():
            self._raw_value = value
            self._value = Undefined
            self._errors = []

        # Execute only if value needs conversion
        if not self._typecheck(value):

            # Run prevalidators
            value = self._raise_if_unbound(self.prevalidate, ValueError, value)

            # Convert to valid type from string
            if value is not Undefined:
                value = self._raise_if_unbound(self._from_string, TypeError, value)

            # If value is Undefined object (f.e. there was processing error) -
            # return it to avoid TypeError being raised
            if value is Undefined:
                return Undefined

            # Raise exception if type is still invalid
            if not self._typecheck(value):
                raise TypeError(
                    "validator %r was unable to convert %r to valid type" %
                    (self, value if self.multivalue else value[0]))

        # Run postvalidators
        value = self._raise_if_unbound(self.postvalidate, ValueError, value)

        # Set up processed value
        if self.is_bound():
            self._value = value

        return value

    def prevalidate(self, value):
        """Process input value of unsupported type.

        Prevalidators are executed if *value* needs to be converted to valid
        type expected for this validator. It is expected that prevalidators
        will convert *value* either to :param:`python_type` object or to
        :class:`basestring` object.

        .. note::
            There is no need to convert strings inside prevalidators - use
            :meth:`from_string` instead.

        :param value:
            the value to be prevalidated

        :rtype: :class:`basestring` or :meth:`python_type`
        """
        return event.pipeline(self, 'prevalidate', -1, self.schema, self.key, value)

    def postvalidate(self, value):
        """Process converted value.

        This method is executed only if conversion to :param:`python_type` was
        successful.

        :param value:
            the value to be postvalidated
        """
        return event.pipeline(self, 'postvalidate', -1, self.schema, self.key, value)

    def validate(self, value):
        """Validate processed value.

        This validation process is issued once :meth:`is_valid` is called for
        this validator.
        """
        return event.pipeline(self, 'validate', -1, self.schema, self.key, value)

    def from_string(self, value):
        """Convert string value to :param:`python_type` type object.

        This method raises :exc:`~formify.exc.ConversionError` if conversion
        cannot be performed.
        """
        try:
            return self.python_type(value)
        except (ValueError, TypeError):
            raise exc.ConversionError("unable to convert '%(value)s' to desired type" % {'value': value})

    def typecheck(self, value):
        """Check if type of *value* is supported by this validator."""
        return isinstance(value, self.python_type)

    def is_valid(self):
        """Check if last value was processed successfuly."""
        if not self.is_bound():
            return True  # always valid if not bound
        elif self.errors:
            return False  # if validator already has errors, return false and skip further validation
        elif self.required and self.value is Undefined:
            self._errors.append(u'this field is required')
            return False
        self._value = self._raise_if_unbound(self.validate, ValueError, self._value)
        return len(self.errors) == 0

    @property
    def key(self):
        """The key assigned to this validator."""
        return self._key

    @property
    def name(self):
        """The name of this validator.

        This is equal to validator's class name.
        """
        return self.__class__.__name__

    @property
    def schema(self):
        """Schema object this validator is bound to or ``None`` if this
        validator is not bound to any schema."""
        if self._schema is not None:
            return self._schema()

    @property
    def raw_value(self):
        """Unchanged value :meth:`process` was called with.

        If this is ``Undefined``, :meth:`process` was not called yet or was
        called with ``Undefined`` object value.
        """
        return self._raw_value

    @property
    def value(self):
        """Output value produced by this validator.

        If this is ``Undefined``, :meth:`process` was not called yet or - if
        :param:`raw_value` is set - validator was not able to process value.
        """
        return self._value

    @property
    def errors(self):
        """List of validation errors.

        Access to this list is public - it can be modified to force validation
        errors f.e. in custom event listener callables.
        """
        return self._errors

    @property
    def python_type(self):
        """Python type object this validator converts input values to."""
        raise NotImplementedError("'python_type' is not implemented in %r" % self.__class__)

    @property
    def multivalue(self):
        """``True`` if validator is a multivalue validator (i.e. it accepts and
        validates sequence of values of same type) or ``False`` otherwise."""
        return False

    @property
    def label(self):
        """Validator's label.

        By default, this is calculated from validator's :param:`key`.
        """
        if self._label is None:
            return unicode(self.key.replace('_', ' ').capitalize())
        elif self._label is Undefined:
            return Undefined
        else:
            return unicode(self._label)

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def default(self):
        """Default value of this validator."""
        if self._default is Undefined:
            return Undefined
        else:
            return helpers.maybe_callable(self._default)

    @default.setter
    def default(self, value):
        self._default = value


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
    __visit_name__ = 'string'

    def __init__(self, length_max=None, length_min=None, multiline=False, **kwargs):
        super(String, self).__init__(**kwargs)
        self.length_max = length_max
        self.length_min = length_min
        self.multiline = multiline

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
        value = super(Choice, self).postvalidate(value)
        if self.multivalue:
            for v in value:
                if v not in self.options:
                    raise exc.ValidationError("invalid choice")
        else:
            if value not in self.options:
                raise exc.ValidationError("invalid choice")
        return value

    def is_selected(self, value):
        if self.value is Undefined:
            return False
        elif self.multivalue:
            return self.from_string(value) in self.value
        else:
            return self.from_string(value) == self.value
