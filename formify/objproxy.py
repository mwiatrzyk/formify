"""Proxy classes used for object population and form initialization."""

from formify.utils import helpers


def create_proxy(obj):
    """Create and return proxy for *obj* depending on *obj* type."""
    if helpers.is_mapping(obj):
        return MappingProxy(obj)
    else:
        return ObjectProxy(obj)


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
