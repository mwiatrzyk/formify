import cgi

from formify import forms
from formify.utils import helpers
from formify.undefined import Undefined


class Markup(unicode):
    """Used to wrap XHTML-safe strings."""

    def __html__(self):
        return self

    @classmethod
    def escape(cls, value):
        if isinstance(value, cls):
            return value
        elif hasattr(value, '__html__'):
            return cls(value.__html__())
        else:
            return cls(cgi.escape(unicode(value), True))


class Tag(object):
    """Used to create XHTML tags.

    :param name:
        name of tag (f.e. ``table``)
    :param data:
        textual data to be placed between opening and closing tag
    :param cdata:
        unparsed character data to be placed between opening and closing tag
    :param attr:
        dict of tag attributes
    """

    def __init__(self, name, data=None, cdata=None, attr=None):
        self.name = name
        self.data = data
        self.cdata = cdata
        self.attr = attr or {}

    def __repr__(self):
        return repr(self.__html__())

    def __str__(self):
        return str(self.__html__())

    def __unicode__(self):
        return unicode(self.__html__())

    def __html__(self):
        attrs = u' '.join(
            u'%s="%s"' % (k, Markup.escape(v))
            for k, v in sorted(self.attr.iteritems()))
        if attrs:
            attrs = u" %s" % attrs
        if self.data is not None:
            if helpers.is_iterable(self.data):
                data = u''.join(Markup.escape(v) for v in self.data if v is not None)
            else:
                data = Markup.escape(self.data)
            return Markup(u"<%s%s>%s</%s>" % (self.name, attrs, data, self.name))
        elif self.cdata is not None:
            if helpers.is_iterable(self.cdata):
                data = u''.join(unicode(v) for v in self.cdata if v is not None)
            else:
                data = self.cdata
            return Markup(u"<%s%s><![CDATA[%s]]></%s>" % (self.name, attrs, data, self.name))
        else:
            return Markup(u"<%s%s/>" % (self.name, attrs))


class Field(forms.Field):

    def create_label_widget(self):
        widget = Tag('label', self.validator.label)
        widget.attr['for'] = self.id
        return widget

    def create_errors_widget(self):
        return self.validator.errors

    def process(self, values):
        if len(values) == 1 and not values[0]:
            return Undefined
        else:
            return super(Field, self).process(values)


class InputField(Field):

    @property
    def __input_type__(self):
        raise NotImplementedError()

    def create_widget(self):
        widget = Tag('input')
        widget.attr.update({
            'name': self.validator.key,
            'value': self.validator.raw_value,
            'type': self.__input_type__,
            'id': self.id})
        return widget


class TextField(InputField):
    __input_type__ = 'text'


class PasswordField(InputField):
    __input_type__ = 'password'

    def create_widget(self):
        widget = super(PasswordField, self).create_widget()
        widget.attr['value'] = ''  # do not send password back to browser
        return widget


class ChoiceField(Field):

    def __init__(self, schema, validator, options, multiple=False):
        super(ChoiceField, self).__init__(schema, validator)
        self.options = options
        self.multiple = multiple

    def create_container_widget(self, option_widgets):
        widget = Tag('select', option_widgets)
        widget.attr.update({
            'name': self.validator.key,
            'id': self.id,
        })
        if self.multiple:
            widget.attr['multiple'] = 'multiple'
        return widget

    def create_option_widget(self, index, key, value):
        widget = Tag('option', value)
        widget.attr['value'] = key
        if key == self.validator.value:
            widget.attr['selected'] = 'selected'
        return widget

    def create_widget(self):
        options = []
        for index, (key, value) in enumerate(self.options):
            options.append(self.create_option_widget(index, key, value))
        return self.create_container_widget(options)


class CheckboxField(InputField):
    __input_type__ = 'checkbox'

    def create_widget(self):
        widget = super(CheckboxField, self).create_widget()
        widget.attr['value'] = '1'
        if self.validator.value:
            widget.attr['checked'] = 'checked'
        return widget


class TextAreaField(Field):

    def create_widget(self):
        widget = Tag('textarea', self.validator.raw_value)
        widget.attr.update({
            'name': self.validator.key,
            'id': self.id})
        return widget


class Form(forms.Form):

    def visit_basestring(self, validator):
        return TextField(self, validator)

    def visit_string(self, validator):
        if validator.multiline:
            return TextAreaField(self, validator)
        else:
            return self.visit_basestring(validator)

    def visit_password(self, validator):
        return PasswordField(self, validator)

    def visit_boolean(self, validator):
        return CheckboxField(self, validator)

    def visit_choice(self, validator):
        return ChoiceField(self, validator, validator.options.items())

    def visit_numeric(self, validator):
        return TextField(self, validator)

    def as_table(self):
        rows = []
        for field in self:
            row = Tag('tr', [
                Tag('td', field.label_widget),
                Tag('td', field.widget),
                Tag('td', field.errors_widget),
            ])
            rows.append(row)
        return Markup(''.join(unicode(r) for r in rows))
