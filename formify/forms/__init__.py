import weakref
import collections

from formify.utils import helpers
from formify.objproxy import create_proxy
from formify.undefined import Undefined
from formify.utils.mixins import KeyValueMixin
from formify.utils.decorators import memoized_property
from formify.utils.collections import OrderedDict
from formify.validators.grouping import Map, Sequence


class SchemaVisitor(object):
    """Converts schema validators into form fields."""

    def __init__(self, owner, schema):
        self._owner = owner
        self._schema = schema

    @property
    def owner(self):
        return self._owner

    def get_fields(self):
        fields = OrderedDict()
        for validator in self._schema.itervalues():
            fields[validator.key] = validator.accept(self)
        return fields


class Field(object):
    """Generic form field class.

    Objects of class :class:`Field` are used to render widgets the user can
    later use to submit his data to validators. There will be one field object
    created for each validator in given schema.

    :param owner:
        the owner of this field
    :param validator:
        validator for which the field is created
    """

    def __init__(self, owner, validator):
        self._owner = weakref.ref(owner)
        self._validator = validator

    @property
    def owner(self):
        """The owner of this field.

        The owner can be either :class:`Form` or :class:`GroupField` object.
        """
        return self._owner()

    @property
    def validator(self):
        """Validator used to process data transfered to this field."""
        return self._validator

    @memoized_property
    def id(self):
        """ID that uniquely identifies this field within form."""
        if isinstance(self.owner, Field):
            return "%s-%s" % (self.owner.id, self.validator.key)
        else:
            return self.validator.key

    @property
    def name(self):
        """Field's name.

        This defaults to field class name.
        """
        return self.__class__.__name__

    def create_widget(self):
        """Create data input and display widget."""
        raise NotImplementedError(
            "create_widget() not implemented for %r" %
            self.__class__)

    def create_label_widget(self):
        """Create label widget.

        If field has no label this method should return ``None``.
        """
        raise NotImplementedError(
            "create_label_widget() not implemented for %r" %
            self.__class__)

    def create_description_widget(self):
        """Create description widget.

        If field has no description text assigned this method should return
        ``None``.
        """
        raise NotImplementedError(
            "create_description_widget() not implemented for %r" %
            self.__class__)

    def create_errors_widget(self):
        """Create errors widget.

        If field has no errors or if errors are notified in other way (f.e.
        using dialog widgets) this method should return ``None``.
        """
        raise NotImplementedError(
            "create_errors_widget() not implemented for %r" %
            self.__class__)

    def process(self, values):
        """Process given list of values using underlying validator.

        If underlying validator is not multivalue validator, only last value
        from list is processed.

        :param values:
            list of values to be processed
        """
        if self.validator.multivalue:
            return self.validator.process(values)
        else:
            return self.validator.process(values[-1])


class GroupField(Field):
    """Base class for fields that aggregate other fields in larger
    structures."""
    __schema_visitor__ = SchemaVisitor

    @memoized_property
    def _fields(self):
        """Return map of contained fields."""
        return self.__schema_visitor__(self, self.validator).get_fields()


class MapField(GroupField, KeyValueMixin):
    """Groups fields of different types and provides dict-like access to it."""

    def __iter__(self):
        for key in self._fields:
            yield key

    def __getitem__(self, key):
        if key in self._fields:
            return self._fields[key]
        else:
            raise KeyError(key)


class SequenceField(GroupField):
    """Groups n-occurences of concrete field."""


class Form(KeyValueMixin):
    """Connector of schema, validators and fields.

    :param schema:
        validation schema used to validate data submitted to form
    :param data:
        mapping containing form input data submitted by user
    :param obj:
        the object that is being edited by this form. When no *data* is
        provided this is also used as input data source
    :param proxy_cls:
        proxy class used to wrap *obj* and customize attribute read operations.
        If not given default one will be determined by *obj* type
    """
    __schema__ = None
    __schema_visitor__ = SchemaVisitor
    __undefined_values__ = set()

    def __init__(self, schema=None, data=None, obj=None, proxy_cls=create_proxy):

        # Initialize private members
        self._obj = obj
        self._proxy_cls = proxy_cls

        # Create schema instance
        if schema is not None:
            self._schema = schema()
        elif self.__schema__ is not None:
            self._schema = self.__schema__()
        else:
            raise TypeError("unable to create form without schema")

        # Create form field for each validator
        self._fields = self.__schema_visitor__(self, self._schema).get_fields()

        # Forward data to underlying schema and process it
        if data is not None:
            self._process_data(data)
        elif obj is not None:
            self._process_obj(obj)

    def __iter__(self):
        for key in self._fields:
            yield key

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
        for field in self.walk():
            key = field.id
            if key in data:
                values = self.remove_undefined(key, getlist(key))
                if values:
                    field.process(values)

    def _process_obj(self, obj):
        """Process form using data from given object."""

        # Wrap object with proxy
        obj = self._proxy_cls(obj)

        # Iterate through each field and check if object has corresponding key
        # If so, use it as data source for the field
        for field in self.walk():
            key = field.key
            if key in obj:
                field.process([obj[key]])

    @property
    def schema(self):
        """Validation schema used by form to validate its input."""
        return self._schema

    @property
    def info(self):
        """Placeholder for custom data.

        This is a shortcut for :attr:`Schema.info` of underlying schema object.
        """
        return self.schema.info

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

    def is_valid(self):
        """Return ``True`` if underlying schema is valid or ``False``
        otherwise."""
        return self._schema.is_valid()

    def walk(self):
        """Generate all fields contained in form in a recursive way."""

        def generate(owner):
            for field in owner.itervalues():
                yield field
                if isinstance(field, GroupField):
                    for field in generate(field):
                        yield field

        return generate(self)

    def populate(self, obj=None):
        if obj is None and self.obj is None:
            raise TypeError("no object to populate with current form state")
        return self.schema.populate(
            obj if obj is not None else self.obj,
            proxy_cls=self._proxy_cls)
