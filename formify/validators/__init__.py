from formify.utils import helpers
from formify.undefined import Undefined


class validator_property(object):
    """A property decorator that allows to share setters and getter between
    validator objects and validator proxies.

    This differs from standard property decorator in a fact that here we have
    both setters and getters accepting 2 parameters: property owner and
    value. Getters will receive previously set value as second parameters, and
    getters must return value instead of setting it somewhere. This allows
    to use getter and setter functions in different scope.
    """

    def __init__(self, fget=None, fset=None, name=None, doc=None):
        self.fget = fget
        self.fset = (lambda s, v: v) if fset is True else fset
        self.__doc__ = doc
        self.__name__ = name
        if self.fget is not None:
            if self.__doc__ is None:
                self.__doc__ = fget.__doc__
            if self.__name__ is None:
                self.__name__ = fget.func_name

    def __call__(self, fget):
        self.fget = fget
        if self.__doc__ is None:
            self.__doc__ = fget.__doc__
        if self.__name__ is None:
            self.__name__ = fget.func_name
        return self

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return self.fget(obj, obj.__dict__["_%s" % self.__name__])

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        obj.__dict__["_%s" % self.__name__] = self.fset(obj, value)

    def __delete__(self, obj):
        raise AttributeError("can't delete attribute")

    def setter(self, fset):
        self.fset = fset
        return self


class ValidatorProxy(object):
    """Base class for validator proxies.

    This class is monitoring attribute operations (read, write and delete) and
    forwards client requests to either original validator (read only access;
    first reads from owner if attribute was changed) or owning object (write
    and delete access).

    .. note::
        :class:`ValidatorProxy` will forward only public attributes; if
        attribute name is prefixed with _ (underscore), all operations will be
        performed in predefined way.

    :param owner:
        an object that created validator proxy. It's ``__dict__`` will be used
        as data placeholder
    :param validator:
        original validator object
    """

    def __init__(self, owner, validator):
        self._owner = owner
        self._validator = validator

    def __getattr__(self, name):
        prop = getattr(self._validator.__class__, name, None)
        storage = self._get_storage(self._owner, self._validator)
        if name in storage:
            if prop is None:
                return storage[name]
            else:
                return prop.fget(self, storage[name])
        else:
            return getattr(self._validator, name)

    def __setattr__(self, name, value):
        if name in set(['_owner', '_validator']):
            super(ValidatorProxy, self).__setattr__(name, value)
        else:
            prop = getattr(self._validator.__class__, name, None)
            storage = self._set_storage(self._owner, self._validator)
            if prop is None:
                storage[name] = value
            else:
                storage[name] = prop.fset(self, value)

    def __delattr__(self, name):
        storage = self._get_storage(self._owner, self._validator)
        if name in storage:
            del storage[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self._validator.__class__.__name__, name))

    @classmethod
    def _set_storage(cls, owner, validator):
        return owner.__dict__.setdefault("_%s" % validator.key, {})

    @classmethod
    def _get_storage(cls, owner, validator):
        return owner.__dict__.get("_%s" % validator.key, {})


class Validator(object):
    """Base class for all validators.

    :var label:
        validator's label to be used f.e. as form field label text. Following
        values are available:

        ``None``
            use capitalized :attr:`key` as label (default)

        ``Undefined``
            do not use label at all. Once label is retrieved, its value will be
            ``Undefined``

        basestring text
            use provided string as label

    :var default:
        default value to be used when there is no data bound to validator. This
        can also be a no-argument callable that returns default value once
        called

    :var description:
        validator's description text to be used f.e. as tooltip or for other
        help purposes

    :var required:
        setting this to ``True`` makes the validator required; once it has no
        value assigned, validation will fail

    :var autoconvert:
        automatically convert provided values to validator-specific type
        represented by :attr:`python_type`. If this is set to ``False``
        automatic conversion will not be performed, but type check will be
        issued instead (default is ``True``)

    :var key:
        use this to rename validator in owning schema. Useful if validator has
        same name as one of schema's method or non-validator attributes
    """
    __proxy__ = ValidatorProxy

    def __init__(self, label=None, default=Undefined, description=None, required=False, autoconvert=True, key=None):
        helpers.set_creation_order(self)
        self.label = label
        self.default = default
        self.description = description
        self.required = required
        self.autoconvert = autoconvert
        self.key = key

    @property
    def python_type(self):
        raise NotImplementedError()

    @validator_property(fset=True)
    def label(self, value):
        if value is None:
            return unicode(self.key.replace('_', ' ').capitalize())
        elif value is Undefined:
            return Undefined
        else:
            return unicode(value)

    @validator_property(fset=True)
    def default(self, value):
        return helpers.maybe_callable(value)

    def getval(self, owner):
        storage = self.__proxy__._get_storage(owner, self)
        value = storage.get('value', Undefined)
        return value

    def setval(self, owner, value):
        value = self.prevalidate(value)
        if self.autoconvert:
            value = self.convert(value)
        elif not self.typecheck(value):
            raise TypeError("validator '%s' does not accept values of type %s" % (self.key, type(value)))
        value = self.postvalidate(value)
        storage = self.__proxy__._set_storage(owner, self)
        storage['value'] = value
        return value

    def prevalidate(self, value, other=None):
        return value

    def convert(self, value, other=None):
        return self.python_type(value)

    def typecheck(self, value, other=None):
        return isinstance(value, self.python_type)

    def postvalidate(self, value, other=None):
        return value


from formify.validators.base import *
