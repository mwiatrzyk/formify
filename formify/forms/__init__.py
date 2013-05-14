import weakref

from formify.utils.decorators import memoized_property
from formify.utils.collections import OrderedDict


class Field(object):
    """Generic form field class.

    Objects of class :class:`Field` are used to render widgets the user can
    later use to submit his data to validators. There will be one field object
    created for each validator in given schema.

    :param form:
        the form that owns this field
    :param validator:
        validator used to validate data
    """

    def __init__(self, form, validator):
        self._form = weakref.ref(form)
        self._validator = validator

    @property
    def form(self):
        """The form this field belongs to."""
        return self._form()

    @property
    def validator(self):
        """The validator that is validating this field."""
        return self._validator

    @property
    def id(self):
        """ID that uniquely identifies this field within form."""
        return self.validator.key

    @property
    def name(self):
        """Field's name.

        This defaults to field class name.
        """
        return self.__class__.__name__

    @property
    def widget(self):
        """Input widget used to collect data from user."""
        return self.create_widget()

    @property
    def label_widget(self):
        """Label widget used to render label of this field."""
        return self.create_label_widget()

    @property
    def description_widget(self):
        """Widget used to render field's description."""
        return self.create_description_widget()

    @property
    def errors_widget(self):
        """Widget used to display processing and validation errors that occured
        for this field."""
        return self.create_errors_widget()

    def create_widget(self):
        """Create and return input widget."""
        raise NotImplementedError("'create_widget' not implemented for %r" % self.__class__)

    def create_label_widget(self):
        """Create and return label widget.

        If field has no label this method should return ``None``.
        """
        raise NotImplementedError("'create_label_widget' not implemented for %r" % self.__class__)

    def create_description_widget(self):
        """Create and return description widget.

        If field has no description text assigned this method should return
        ``None``.
        """
        raise NotImplementedError()

    def create_errors_widget(self):
        """Create and return errors widget.

        If field has no errors this method will return ``None``.
        """
        raise NotImplementedError("'create_errors_widget' not implemented for %r" % self.__class__)

    def process(self, values):
        """Process given list of values entered by the user.

        The list will usually contain only one element. More elements can be
        found f. e. for choice fields, where the user can pick up one or more
        option from list of predefined options.

        :param values:
            list of values submitted by the user
        """
        return self.validator.process(values[-1])


class Form(object):
    __schema__ = None

    def __init__(self, data=None, schema=None):
        self._fields = OrderedDict()

        if schema is not None:
            self._schema = schema()
        elif self.__schema__ is not None:
            self._schema = self.__schema__()
        else:
            raise TypeError("unable to create form without schema")

        for key in self._schema:
            validator = self._schema[key]
            visit_method = getattr(self, "visit_%s" % validator.__visit_name__, None)
            if visit_method is None:
                visit_method = self.visit_validator
            self._fields[key] = field = visit_method(validator)  # the field is created here
            if data is not None and key in data:
                if hasattr(data, 'getlist'):  # i.e. ImmutableMultiDict from Flask
                    field.process(data.getlist(key))
                else:
                    field.process([data[key]])

    def __iter__(self):
        for key in self._fields:
            yield key

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(Form, self).__setattr__(name, value)
        elif name in self._fields:
            self._fields[name].process([value])
        else:
            raise AttributeError("no such field: %s" % name)

    def __getattr__(self, name):
        if name.startswith('_') or name.startswith('visit_'):
            return super(Form, self).__getattribute__(name)
        elif name in self._fields:
            return self._fields[name].validator.value
        else:
            raise AttributeError("no such field: %s" % name)

    def __getitem__(self, key):
        if key in self._fields:
            return self._fields[key]
        else:
            raise KeyError(key)

    @memoized_property
    def _fields(self):
        result = OrderedDict()
        for key in self._schema:
            validator = self._schema[key]
            visit_method = getattr(self, "visit_%s" % validator.__visit_name__, None)
            if visit_method is None:
                visit_method = self.visit_validator
            result[key] = field = visit_method(validator)  # the field is created here
            if key in self._data:
                field.process(self._data.getlist(key))
        return result

    @property
    def data(self):
        return self._data

    @property
    def schema(self):
        return self._schema

    def visit_validator(self, validator):
        raise NotImplementedError("%r does not have 'visit_%s' method implemented" % (self.__class__, validator.__visit_name__))

    def is_valid(self):
        """Return ``True`` if this form is valid or ``False`` otherwise."""
        return self._schema.is_valid()

    def iterkeys(self):
        for key in self:
            yield key

    def keys(self):
        return list(self.iterkeys())

    def iterfields(self):
        for key in self:
            yield self[key]

    def fields(self):
        return list(self.iterfields())
