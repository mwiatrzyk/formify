import cgi

from formify import forms
from formify.utils import helpers
from formify.undefined import Undefined

__all__ = [
    'Markup', 'Tag', 'Field', 'InputField', 'TextField', 'PasswordField',
    'ChoiceField', 'RadioCheckboxChoiceField', 'CheckboxField',
    'TextAreaField', 'Form']


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

        def join_attr_value(value):
            if helpers.is_iterable(value):
                return ' '.join([Markup.escape(v) for v in sorted(value)])
            else:
                return value

        attrs = u' '.join(
            u'%s="%s"' % (k, Markup.escape(join_attr_value(v)))
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

    def set_id(self, id_):
        """Set ID for this tag.

        This method overwrites previously set ID.

        :param id_:
            the ID for this tag
        """
        self.attr['id'] = id_
        return self

    def add_class(self, *args):
        """Add CSS class or classes for this tag.

        :param *args:
            CSS class name(-s)
        """
        if not args:
            raise TypeError("add_class() takes at least 2 arguments (1 given)")
        for cls in args:
            if 'class' not in self.attr:
                self.attr['class'] = set([cls])
            elif isinstance(self.attr['class'], basestring):
                self.attr['class'] = set([self.attr['class'], cls])
            else:
                self.attr['class'].add(cls)
        return self


class Field(forms.Field):
    """Generic XHTML form field.

    This is a base class for all other XHTML form fields.
    """

    def create_label_widget(self):
        if self.validator.label is Undefined:
            return None
        # Label text
        label_text = Tag('span', self.validator.label)
        label_text.add_class('ffy-label-text')
        # Label widget
        widget = Tag('label')
        widget.attr['for'] = self.id
        widget.add_class('ffy-label')
        if self.validator.required:
            widget.add_class('ffy-label-required')
            # Create marker for required fields
            label_marker = Tag('span', '*')
            label_marker.add_class('ffy-label-marker')
            # Join text and marker together producing complete label
            widget.data = [label_text, label_marker]
        else:
            widget.data = label_text
        return widget

    def create_description_widget(self):
        if not self.validator.description:
            return None
        widget = Tag('span', self.validator.description)
        widget.add_class('ffy-description')
        return widget

    def create_errors_widget(self):
        if not self.validator.errors:
            return None
        widget = Tag('ul')
        widget.add_class('ffy-errors')
        widget.data = [Tag('li', e) for e in self.validator.errors]
        return widget

    @property
    def widget(self):
        widget = self.create_widget()
        widget.set_id(self.id)
        widget.add_class('ffy-field', "ffy-field-%s" % self.name)
        return widget


class InputField(Field):
    """Generic XHTML input field."""

    @property
    def __input_type__(self):
        raise NotImplementedError("'__input_type__' not implemented for %r" % self.__class__)

    def create_widget(self):
        widget = Tag('input')
        widget.add_class("ffy-field-validator-%s" % self.validator.name)
        widget.attr.update({
            'name': self.validator.key,
            'value': self.validator.raw_value,
            'type': self.__input_type__})
        return widget


class TextField(InputField):
    """Single-line text input field."""
    __input_type__ = 'text'


class PasswordField(InputField):
    """Password input field."""
    __input_type__ = 'password'

    def create_widget(self):
        widget = super(PasswordField, self).create_widget()
        widget.attr['value'] = ''  # do not send password back to browser
        return widget


class ChoiceField(Field):
    """Standard choice field."""

    def __init__(self, form, validator, multiple=False):
        super(ChoiceField, self).__init__(form, validator)
        self.multiple = multiple

    def create_container_widget(self, options):
        """Create container widget.

        The container widget is used to group options together.

        :param options:
            list of options widgets
        """
        widget = Tag('select', options)
        widget.attr['name'] = self.validator.key
        if self.multiple:
            widget.attr['multiple'] = 'multiple'
        return widget

    def create_option_widget(self, index, value, description, selected):
        """Create option widget.

        Each option widget is responsible for rendering of single choice
        option. All option widgets will be wrapped with container returned by
        :meth:`create_option_widget`.

        :param index:
            the index of option in the list of available options
        :param value:
            option's value
        :param description:
            option's description (f.e. to be used as a label)
        :param selected:
            ``True`` if this option was selected by user, ``False`` otherwise
        """
        widget = Tag('option', description)
        widget.attr['value'] = value
        if selected:
            widget.attr['selected'] = 'selected'
        return widget

    def create_widget(self):
        options = []
        for i, option in enumerate(self.validator.options.iteritems()):
            value, description = option
            selected = self.validator.is_selected(value)
            option = self.create_option_widget(i, value, description, selected)
            options.append(option)
        return self.create_container_widget(options)


class RadioCheckboxChoiceField(ChoiceField):

    @property
    def name(self):
        if self.multiple:
            return 'CheckboxChoiceField'
        else:
            return 'RadioChoiceField'

    def create_container_widget(self, options):
        return Tag('ul', options)

    def create_option_widget(self, index, value, description, selected):
        # Generate ID for input and its label
        id_ = "%s-%s" % (self.validator.key, index)
        # Generate radio input field
        widget = Tag('input')
        widget.attr.update({
            'type': 'checkbox' if self.multiple else 'radio',
            'name': self.validator.key,
            'value': value,
            'id': id_})
        if selected:
            widget.attr['checked'] = 'checked'
        # Generate label
        label = Tag('label', description)
        label.attr['for'] = id_
        # Wrap both with list item tag
        return Tag('li', [widget, label])


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
        widget = Tag('textarea', self.validator.raw_value or u'')
        widget.attr['name'] = self.validator.key
        widget.add_class("ffy-field-validator-%s" % self.validator.name)
        return widget


class SchemaField(Field):

    def create_widget(self):
        for validator in self.validator.itervalidators():
            yield self.form.create_field(validator)

    @property
    def widget(self):
        return list(self.create_widget())


class Form(forms.Form):
    __undefined_values__ = set([''])

    def visit_basestring(self, validator):
        return TextField(self, validator)

    def visit_text(self, validator):
        return TextAreaField(self, validator)

    def visit_password(self, validator):
        return PasswordField(self, validator)

    def visit_boolean(self, validator):
        return CheckboxField(self, validator)

    def visit_choice(self, validator):
        return ChoiceField(self, validator, validator.multivalue)

    def visit_numeric(self, validator):
        return TextField(self, validator)

    def visit_schema(self, validator):
        return SchemaField(self, validator)

    def as_table(self, **kwargs):
        rows = []
        for field in self.iterfields():
            row = Tag('tr', [
                Tag('td', [field.label_widget, Tag('br'), field.description_widget]),
                Tag('td', [field.widget, field.errors_widget]),
            ])
            rows.append(row)
        return Tag('table', rows, attr=kwargs)
