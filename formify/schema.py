import copy
import collections

from formify.utils import helpers
from formify.event import add_listener
from formify.undefined import Undefined
from formify.validators import Validator
from formify.utils.decorators import memoized_property
from formify.utils.collections import AttrDict, OrderedDict


class Proxy(object):
    """Base object proxy class.

    Subclasses of this class are used by :meth:`Schema.populate` to populate
    different kind of objects using same interface by providing proxy to
    original object. When implementing concrete subclass following special
    methods have to be defined:

    ``__contains__(key)``
        to check if wrapped object contains attribute *key*

    ``__setitem__(key, value)``
        to overwrite attribute *key* of wrapped object and set it to new
        *value*

    ``__delitem__(key)``
        to delete or clear attribute *key* of wrapped object
    """

    def __init__(self, obj):
        self._obj = obj
        self._modified = False

    def __contains__(self, key):
        return self.contains(key)

    def __getitem__(self, key):
        return self.getitem(key)

    def __setitem__(self, key, value):
        self.setitem(key, value)
        self._modified = True

    def __delitem__(self, key):
        self.delitem(key)
        self._modified = True

    def contains(self, key):
        raise NotImplementedError()

    def getitem(self, key):
        raise NotImplementedError()

    def setitem(self, key, value):
        raise NotImplementedError()

    def delitem(self, key):
        raise NotImplementedError()

    def neq(self, key, value):
        """Return ``True`` if :attr:`obj` *key* value is different than *value*
        or ``False`` otherwise."""
        return self[key] != value

    @property
    def obj(self):
        """Object wrapped by this proxy."""
        return self._obj

    @property
    def modified(self):
        """Return ``True`` if underlying object was modified or ``False``
        otherwise."""
        return self._modified


class ObjectProxy(Proxy):
    """Proxy used for standard objects."""

    def contains(self, key):
        return hasattr(self.obj, key)

    def getitem(self, key):
        return getattr(self.obj, key)

    def setitem(self, key, value):
        setattr(self.obj, key, value)

    def delitem(self, key):
        delattr(self.obj, key)


class MappingProxy(Proxy):
    """Proxy used for mapping objects."""

    def contains(self, key):
        return key in self.obj

    def getitem(self, key):
        return self.obj[key]

    def setitem(self, key, value):
        self.obj[key] = value

    def delitem(self, key):
        del self.obj[key]


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

    def populate(self, obj, proxy_cls=None):
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

        # Wrap object with proxy
        if proxy_cls is not None:
            obj = proxy_cls(obj)
        elif helpers.is_mapping(obj):
            obj = MappingProxy(obj)
        else:
            obj = ObjectProxy(obj)

        # Populate object
        for key, value in self.iteritems():
            if key not in obj:
                if value is not Undefined:
                    obj[key] = value
            elif value is Undefined:
                del obj[key]
            elif obj.neq(key, value):
                obj[key] = value

        # Return populated object if it was modified or None otherwise
        if obj.modified:
            return obj.obj
        else:
            return None

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
