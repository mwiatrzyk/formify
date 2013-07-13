import weakref

from formify.utils import helpers
from formify.undefined import Undefined
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
    def key(self):
        """The key of underlying validator."""
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
        """Process given list of values using underlying validator.

        The processing takes place as following:

        * if validator is multivalue validator, entire list is forwarded to
          validator and processed
        * if validator is not multivalue validator, only last item (i.e. most
          recent one) is forwarded and processed

        :param values:
            list of values to be processed
        """
        if self.validator.multivalue:
            return self.validator.process(values)
        else:
            return self.validator.process(values[-1])


class Form(object):
    """Connector of schema, validators and fields.

    :param data:
        multi dict containing form input data submitted by user
    :param obj:
        the object that is being edited by this form. When no *data* is
        provided this is also used as input data source
    :param schema:
        validation schema used to validate data submitted to form
    """
    __schema__ = None
    __undefined_values__ = set()

    def __init__(self, schema=None, data=None, obj=None):

        # Initialize private members
        self._obj = obj
        self._fields = OrderedDict()

        # Create schema instance
        if schema is not None:
            self._schema = schema()
        elif self.__schema__ is not None:
            self._schema = self.__schema__()
        else:
            raise TypeError("unable to create form without schema")

        # Create form field for each validator
        for validator in self._schema.itervalidators():
            self._fields[validator.key] = self.create_field(validator)

        # Forward data to underlying schema and process it
        if data is not None:
            self._process_data(data)
        elif obj is not None:
            self._process_obj(obj)

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

    def _process_data(self, data):
        """Process form data submitted by user."""

        # Get multimapping's ``getlist`` method to get list of values for
        # specified key. If such method does not exist - create dummy one
        getlist = helpers.get_multimapping_getlist(data)
        if getlist is None:
            getlist = lambda k: [data[k]]

        # Forward data to apropriate field to be processed
        for field in self.iterfields():
            key = field.key
            if key in data:
                values = self.remove_undefined(key, getlist(key))
                if values:
                    field.process(values)

    @property
    def schema(self):
        """Validation schema used by form to validate its input."""
        return self._schema

    @property
    def obj(self):
        """Reference of object that is being processed by this form."""
        return self._obj

    def remove_undefined(self, key, values):
        """Remove all ``Undefined`` items from *values* for given *key* and
        return new list of values to be processed by underlying schema.

        This method uses :attr:`__undefined_values__` to guess which values are
        said to be ``Undefined`` and therefore cannot be processed. You can
        overload this method in subclass to provide more sophisticated
        mechanism if needed. This method is executed only if *data* parameter
        of :meth:`__init__` was set.
        """
        if not self.__undefined_values__:
            return values
        else:
            return list(v for v in values if v not in self.__undefined_values__)

    def create_field(self, validator):
        """Create apropriate field object for given validator.

        This method calls ``visit_[name]`` method that must be implemented in
        order to create field for *validator*. If such method is not
        implemented, :exc:`NotImplementedError` is raised. If necessary, this
        method may be overloaded to provide default field instead of raising
        exception.
        """
        visit_method = getattr(self, "visit_%s" % validator.__visit_name__, None)
        if visit_method is None:
            raise NotImplementedError(
                "there is no 'visit_%s' method implemented in %r - the field "
                "cannot be created" % (validator.__visit_name__, self.__class__))
        return visit_method(validator)

    def is_valid(self):
        """Return ``True`` if underlying schema is valid or ``False``
        otherwise."""
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

    def populate(self, obj=None):
        if obj is None and self.obj is None:
            raise TypeError("no object to populate with current form state")
        return self.schema.populate(obj if obj is not None else self.obj)
