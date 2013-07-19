import copy
import itertools
import collections

from formify.event import add_listener
from formify.objproxy import create_proxy
from formify.undefined import Undefined
from formify.validators import Validator
from formify.utils.decorators import memoized_property
from formify.utils.collections import AttrDict, OrderedDict


class SchemaMeta(type):
    """Metaclass for class :class:`Schema`.

    This metaclass is responsible for collecting all validators that were
    defined in in schema class, sorting them by creation order and making
    available for schema via :param:`__validators__` special property.
    """

    @property
    def __validators__(cls):
        """Map of unbound validators added to schema."""
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
    """Form schema base class.

    This class is responsible for grouping all validators in one object, making
    them a single entity. Once schema is instantated, all validators in newly
    created object are said to be *bound*. You will need to create at least one
    sublcass of :class:`Schema` when using this library.
    """
    __metaclass__ = SchemaMeta
    __info_default__ = {}

    def __init__(self, **kwargs):

        # Initialize private properties
        self._bound_validators = {}

        # Bind validators to schema and initialize with defaults
        for name, validator in self.__validators__.items():
            validator.bind(self)
            if name not in kwargs:
                default = validator.default
                if default is not Undefined:
                    setattr(self, name, copy.deepcopy(default))

        # Process data passed to __init__ method
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
        """Memoized map of unbound validators."""
        return self.__class__.__validators__

    @property
    def errors(self):
        """Dict with schema processing and validation errors.

        If there were no errors, the dict will be empty. Otherwise keys
        represent validators for which errors were found and values - list of
        exception objects raised during processing of assigned validator.
        """
        result = {}
        for k in self:
            errors = self[k].errors
            if errors:
                result[k] = errors
        return result

    @memoized_property
    def info(self):
        """Placeholder for custom data.

        This is a memoized property that can be set to defaults using class
        :attr:`__info_default__` attribute. This can be useful to transfer
        additional data to event listeners etc.
        """
        return AttrDict(self.__info_default__)

    def is_valid(self):
        """Return ``True`` if data processed by schema is valid or ``False``
        otherwise.

        A schema is valid if and only if all of its validators are valid.
        """
        result = True
        for k in self:
            if not self[k].is_valid():
                result = False
        return result

    def iterkeys(self, skip_undefined=False):
        """Generator of validator keys.

        :param skip_undefined:
            if ``True``, keys of validators that do not have a value will be
            skipped (default is ``False``)
        """
        if skip_undefined:
            for key in self:
                if self[key].value is not Undefined:
                    yield key
        else:
            for key in self:
                yield key

    def keys(self, skip_undefined=False):
        """Return list of validator keys."""
        return list(self.iterkeys(skip_undefined))

    def itervalues(self, skip_undefined=False):
        """Generator of processed validator values."""
        for key in self.iterkeys(skip_undefined):
            yield self[key].value

    def values(self, skip_undefined=False):
        """Return list of processed validator values."""
        return list(self.itervalues(skip_undefined))

    def iteritems(self, skip_undefined=False):
        """Generator of ``(key, value)`` pairs."""
        for key in self.iterkeys(skip_undefined):
            yield key, self[key].value

    def items(self, skip_undefined=False):
        """Return list of ``(key, value)`` pairs."""
        return list(self.iteritems(skip_undefined))

    def itervalidators(self):
        """Generator of validator objects registered for this schema."""
        for key in self:
            yield self[key]

    def validators(self):
        """Return list of validator objects registered for this schema."""
        return list(self.itervalidators())

    def populate(self, obj, extra=None, proxy_cls=create_proxy):
        """Update given object with current state of this form.

        This method returns ``True`` if one or more attributes of *obj* were
        updated or ``False`` otherwise (state of *obj* and schema is the same
        so no update was performed).

        :param obj:
            an object to be populated (of any type)
        :param proxy_cls:
            optional proxy to be used when accessing *obj* (if not given,
            default one will be used according to *obj* type)
        """
        if extra is None:
            extra = {}

        # Wrap object with proxy
        obj = proxy_cls(obj)

        # Populate object
        for key, value in itertools.chain(self.iteritems(), extra.iteritems()):
            if key not in obj:
                if value is not Undefined:
                    obj[key] = value
            elif value is Undefined:
                del obj[key]
            elif obj.neq(key, value):
                obj[key] = value

        # Return True if object was modified or False otherwise
        if obj.modified:
            return True
        else:
            return False

    @classmethod
    def add_listener(sender, event, listener, default_registrar):
        """Overrides event registration process."""
        if isinstance(event, basestring):
            default_registrar(sender, event, listener)
        else:
            event, eargs = event[0], event[1:]
            for arg in eargs:
                if isinstance(arg, type) and issubclass(arg, Validator):
                    for k, v in sender.__validators__.iteritems():
                        if isinstance(v, arg):
                            add_listener(v, event, listener)
                elif isinstance(arg, basestring) and arg in sender.__validators__:
                    add_listener(sender.__validators__[arg], event, listener)
                else:
                    raise TypeError("invalid event argument: %r" % arg)
