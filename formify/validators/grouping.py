"""Validators that group other validators in larger structures."""

from formify.validators import Validator

from formify.utils.mixins import KeyValueMixin


class _ValueProxy(object):

    def __init__(self, owner):
        self._owner = owner

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(_ValueProxy, self).__setattr__(name, value)
        elif Validator.is_bound_to(self._owner, name):
            Validator.get_bound_validator(self._owner, name).process(value)
        elif name in self._owner.__validators__:  # Rebind removed validator
            self._owner.__validators__[name].bind(self).process(value)
        else:
            raise AttributeError("no validator named '%s'" % name)

    def __getattribute__(self, name):
        if name.startswith('_') or name not in self._owner.__validators__:
            return super(_ValueProxy, self).__getattribute__(name)
        elif Validator.is_bound_to(self._owner, name):
            return Validator.get_bound_validator(self._owner, name).value
        else:
            raise AttributeError("validator '%s' was deleted from schema" % name)


class Group(Validator):
    """Base class for grouping validators."""
    __visit_name__ = 'group'


class Map(Group, KeyValueMixin):
    """Groups validators of different types."""
    __visit_name__ = 'map'

    def __init__(self, schema_cls, **kwargs):
        super(Map, self).__init__(schema_cls=schema_cls, **kwargs)
        self.__validators__ = schema_cls.__validators__
        for validator in self.__validators__.itervalues():
            validator.bind(self)

    def __iter__(self):
        for k in self.__validators__:
            if Validator.is_bound_to(self, k):
                yield k

    def __contains__(self, key):
        return Validator.is_bound_to(self,key)

    def __getitem__(self, key):
        if Validator.is_bound_to(self, key):
            return Validator.get_bound_validator(self, key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        if Validator.is_bound_to(self, key):
            Validator.get_bound_validator(self, key).unbind()
        else:
            raise KeyError(key)

    def postvalidate(self, value):
        value = super(Group, self).postvalidate(value)
        for k, v in value.iteritems():
            try:
                self[k].process(v)
            except KeyError:
                raise exc.ValidationError("invalid key: %s" % k)
        return value

    def is_valid(self):
        result = True
        for validator in self.itervalues():
            if not validator.is_valid():
                result = False
        return result

    @property
    def python_type(self):
        return dict

    @property
    def value(self):
        return _ValueProxy(self)


class Sequence(Group):
    """Allows to use single validator multiple times."""
    __visit_name__ = 'sequence'
