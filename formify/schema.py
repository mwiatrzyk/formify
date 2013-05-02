import copy
import collections

from formify.event import add_listener
from formify.undefined import Undefined
from formify.validators import Validator
from formify.utils.decorators import memoized_property
from formify.utils.collections import OrderedDict


class SchemaMeta(type):
    """Metaclass for class :class:`Schema`."""

    @property
    def __validators__(cls):
        validators = []
        for k in dir(cls):
            if not k.startswith('_'):
                v = getattr(cls, k)
                if isinstance(v, Validator):
                    if v._key is None:
                        v._key = k
                    validators.append((v._key, v))
        validators.sort(key=lambda x: x[1]._creation_order)
        return OrderedDict(validators)


class Schema(object):
    __metaclass__ = SchemaMeta

    def __init__(self, **kwargs):
        self._bound_validators = {}
        for name, validator in self.__validators__.items():
            validator.bind(self)
            if name not in kwargs:
                default = validator.default
                if default is not Undefined:
                    kwargs[name] = copy.deepcopy(default)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __iter__(self):
        for k in self.__validators__:
            if k in self._bound_validators:
                yield k

    def __contains__(self, key):
        return key in self._bound_validators

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(Schema, self).__setattr__(name, value)
        elif name in self._bound_validators:
            self._bound_validators[name].process(value)
        elif name in self.__validators__:  # Rebind removed validator
            self.__validators__[name].bind(self).process(value)
        else:
            raise AttributeError("no validator named '%s'" % name)

    def __getattribute__(self, name):
        if name.startswith('_') or name not in self.__validators__:
            return super(Schema, self).__getattribute__(name)
        elif name in self._bound_validators:
            return self._bound_validators[name].value
        else:
            raise AttributeError("validator '%s' was deleted from schema" % name)

    def __delattr__(self, name):
        if name in self._bound_validators:
            self._bound_validators[name].process(Undefined)
        else:
            super(Schema, self).__delattr__(name)

    def __getitem__(self, key):
        if key in self._bound_validators:
            return self._bound_validators[key]
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        if key in self._bound_validators:
            self._bound_validators[key].unbind()
        else:
            raise KeyError(key)

    @memoized_property
    def __validators__(self):
        return self.__class__.__validators__

    @property
    def errors(self):
        result = {}
        for k in self:
            errors = self[k].errors
            if errors:
                result[k] = errors
        return result

    def is_valid(self):
        result = True
        for k in self:
            if not self[k].is_valid():
                result = False
        return result

    @classmethod
    def add_listener(sender, event, listener):
        event, eargs = event[0], event[1:]
        for arg in eargs:
            if isinstance(arg, type) and issubclass(arg, Validator):
                for k, v in sender.__validators__.iteritems():
                    if isinstance(v, arg):
                        add_listener(v, event, listener)
            elif isinstance(arg, basestring) and arg in sender.__validators__:
                add_listener(sender.__validators__[arg], event, listener)
