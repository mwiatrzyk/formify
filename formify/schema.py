from formify.utils import collections
from formify.validators import Validator, ValidatorProxy


class SchemaMeta(type):

    def __new__(tcls, name, bases, dct):
        # TODO: check if we are inheriting from another schema and inherit its
        # attrs as well
        attrs = []
        for attr, value in dct.items():
            if isinstance(value, Validator):
                if value.key is None:
                    value.key = attr
                attrs.append((value.key, value))
                del dct[attr]
        attrs.sort(key=lambda x: x[1]._creation_order)
        dct['__attrs__'] = collections.OrderedDict(attrs)
        return super(SchemaMeta, tcls).__new__(tcls, name, bases, dct)

    def __getattr__(cls, name):
        if name in cls.__attrs__:
            return cls.__attrs__[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (cls.__class__.__name__, name))


class Schema(object):
    """
    >>> from formify import validators
    >>> from formify.undefined import Undefined

    >>> class Test(Schema):
    ...     foo = validators.String()
    ...     bar = validators.Int(default=1)
    ...     baz = validators.Bool(default=lambda: 'Yes')

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
    """
    __metaclass__ = SchemaMeta

    def __getattr__(self, name):
        if name not in self.__attrs__:
            return super(Schema, self).__getattribute__(name)
        else:
            return self.__attrs__[name].getval(self)

    def __setattr__(self, name, value):
        if name not in self.__attrs__:
            super(Schema, self).__setattr__(name, value)
        else:
            self.__attrs__[name].setval(self, value)

    def __getitem__(self, key):
        if key in self.__attrs__:
            return self.__attrs__[key].__proxy__(self, self.__attrs__[key])
        else:
            raise KeyError(key)
