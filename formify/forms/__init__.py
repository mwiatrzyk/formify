import weakref

from formify.utils.decorators import memoized_property
from formify.utils.collections import OrderedDict


class Field(object):

    def __init__(self, form, validator):
        self._form = weakref.ref(form)
        self._validator = validator

    @property
    def form(self):
        """Form this field belongs to."""
        return self._form()

    @property
    def validator(self):
        """Validator that is rendered by this field."""
        return self._validator

    @property
    def id(self):
        """ID that uniquely identifies this field within form."""
        return self.validator.key

    @property
    def value(self):
        return self.validator.value

    @property
    def raw_value(self):
        return self.validator.raw_value

    @property
    def widget(self):
        """Widget used to render field and collect data from user."""
        return self.create_widget()

    @property
    def label_widget(self):
        """Label widget used to render label of this field."""
        return self.create_label_widget()

    @property
    def errors_widget(self):
        """Widget used to display processing errors that occured for this field."""
        return self.create_errors_widget()

    def create_widget(self):
        raise NotImplementedError("'create_widget' not implemented for %r" % self.__class__)

    def create_label_widget(self):
        raise NotImplementedError("'create_label_widget' not implemented for %r" % self.__class__)

    def create_errors_widget(self):
        raise NotImplementedError("'create_errors_widget' not implemented for %r" % self.__class__)

    def process(self, values):
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

        if data is not None:
            for key in self._schema:
                validator = self._schema[key]
                visit_method = getattr(self, "visit_%s" % validator.__visit_name__, None)
                if visit_method is None:
                    visit_method = self.visit_validator
                self._fields[key] = field = visit_method(validator)  # the field is created here
                if key in data:
                    if hasattr(data, 'getlist'):  # i.e. ImmutableMultiDict from Flask
                        field.process(data.getlist(key))
                    else:
                        field.process([data[key]])

    def __iter__(self):
        for field in self._fields.itervalues():
            yield field

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
            return self._fields[name]
        else:
            raise AttributeError("no such field: %s" % name)

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
