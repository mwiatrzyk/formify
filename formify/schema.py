import copy

from formify.utils import collections
from formify.undefined import Undefined
from formify.validators import Validator, ValidatorProxy


class SchemaMeta(type):

    def __new__(tcls, name, bases, dct):
        # TODO: check if we are inheriting from another schema and inherit its
        # validators as well
        validators = []
        for attr, value in dct.items():
            if isinstance(value, Validator):
                if value.key is None:
                    value.key = attr
                validators.append((value.key, value))
                del dct[attr]
        validators.sort(key=lambda x: x[1]._creation_order)
        dct['__validators__'] = collections.OrderedDict(validators)
        return super(SchemaMeta, tcls).__new__(tcls, name, bases, dct)

    def __getattr__(cls, name):
        if name in cls.__validators__:
            return cls.__validators__[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (cls.__class__.__name__, name))


class Schema(object):
    """
    >>> from formify import event, validators
    >>> from formify.undefined import Undefined

    >>> class Test(Schema):
    ...     foo = validators.String(2)
    ...     bar = validators.Int(default='1')
    ...     baz = validators.Bool(default=lambda: 'Yes')
    ...
    ...     @event.listens_for(foo, 'postvalidate')
    ...     @event.listens_for(baz, 'prevalidate')
    ...     def prevalidate_baz(self, sender, value):
    ...         if hasattr(value, 'strip'):
    ...             return value.strip()
    ...         else:
    ...             return value

    #>>> @Test.listens_for('prevalidate')
    #... def prevalidate_string(self, name, value):
    #...     return value

    >>> t = Test()
    >>> t['foo'].label  # Access validator's label via object
    u'Foo'
    >>> Test.foo.label  # Access validator's label via class
    u'Foo'
    >>> t['baz'].default
    'Yes'
    >>> t['baz'].default = Undefined  # Override validator's default for object (not class)
    >>> t['baz'].default
    Undefined
    >>> t.__class__.baz.default   # Still old value when accessed via class
    'Yes'
    >>> del t['baz'].default  # Remove object's default and restore class default
    >>> t['baz'].default
    'Yes'
    >>> t.foo
    Undefined
    >>> t.foo = 1
    >>> t.foo
    u'1'
    >>> t.foo = 'bar'
    Traceback (most recent call last):
    ...
    ValidationError: number of characters must not be greater than 2
    >>> t['foo'].length_max = 3  # Override length constraint
    >>> t.foo = 'bar'  # No error now
    >>> t.bar
    1
    >>> t.baz = 1
    >>> t.baz
    True
    >>> t.baz = 'no'
    >>> t.baz
    False
    >>> t.baz = ' yes '  # Check if prevalidator works
    >>> t.baz
    True
    >>> t.foo = ' ab'  # There also is same prevalidator for 'foo'
    >>> t.foo
    u'ab'
    >>> Test.foo(' ab')  # Call in standalone mode (no owner)
    u'ab'
    """
    __metaclass__ = SchemaMeta

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        for name, attr in self.__validators__.items():
            if name not in kwargs:
                default = attr.default
                if default is not Undefined:
                    setattr(self, name, copy.deepcopy(default))

    def __getattr__(self, name):
        if name not in self.__validators__:
            return super(Schema, self).__getattribute__(name)
        else:
            return self.__validators__[name]._get_value(self)

    def __setattr__(self, name, value):
        if name not in self.__validators__:
            super(Schema, self).__setattr__(name, value)
        else:
            self.__validators__[name]._set_value(self, value)

    def __getitem__(self, key):
        if key in self.__validators__:
            return self.__validators__[key].__proxy__(self, self.__validators__[key])
        else:
            raise KeyError(key)
