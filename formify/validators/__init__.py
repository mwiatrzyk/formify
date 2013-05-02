import weakref

from formify import exc, event
from formify.utils import helpers
from formify.undefined import Undefined


class Validator(object):
    """Base class for all validators providing core functionality."""

    __from_string_excs__ = (TypeError, ValueError)

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
        bound = self.__class__(**self._bind_kwargs)
        bound._key = self._key
        bound._schema = weakref.ref(schema)
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

        # Initialize raw_value, value and error container
        if self.is_bound():
            self._raw_value = value
            self._value = Undefined
            self._errors = []

        # Execute only if value needs conversion
        if not self.typecheck(value):

            # Run prevalidators
            value = self._raise_if_unbound(self.prevalidate, ValueError, value)

            # Convert to valid type
            if isinstance(value, basestring):
                value = self._raise_if_unbound(self.from_string, TypeError, value)

            # If value is Undefined object (f.e. there was processing error) -
            # return it to avoid TypeError being raised
            if value is Undefined:
                return Undefined

            # Raise exception if type is still invalid
            if not self.typecheck(value):
                raise TypeError("validator %r does not accept values of type %s" % (self, type(value)))

        # Run postvalidators
        value = self._raise_if_unbound(self.postvalidate, ValueError, value)

        # Set up processed value
        if self.is_bound():
            self._value = value

        return value

    def prevalidate(self, value):
        """Prevalidate input value and return value for further processing."""
        return event.pipeline(self, 'prevalidate', -1, self.schema, self.key, value)

    def postvalidate(self, value):
        """Postvalidate converted value and return value for use as
        :param:`value`."""
        return event.pipeline(self, 'postvalidate', -1, self.schema, self.key, value)

    def from_string(self, value):
        """Convert string value to object of type represented by
        :param:`python_type`.

        This method raises :exc:`~formify.exc.ConversionError` if conversion
        cannot be performed.
        """
        try:
            return self.python_type(value)
        except (ValueError, TypeError):
            raise exc.ConversionError("unable to convert '%(value)s' to desired type" % {'value': value})

    def typecheck(self, value):
        """Check if value type is supported by this validator."""
        return isinstance(value, self.python_type)

    def is_valid(self):
        """Check if last value was processed successfuly."""
        if not self.is_bound():
            return True  # always valid if not bound
        elif self.required and self.value is Undefined:
            if not self._errors:
                self._errors.append(u'this field is required')
            return False
        elif self.errors:
            return False
        else:
            return True

    @property
    def key(self):
        """The key assigned to this validator."""
        return self._key

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
        raise NotImplementedError()

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


# Import base validators to make it importable via 'formify.validators'
# namespace
from formify.validators.base import *
