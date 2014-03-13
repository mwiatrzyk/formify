# formify/_utils.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

"""Set of helper functions and classes."""


_creation_order = 0
def set_creation_order(self):
    """Sets ``_creation_order`` property of given instance to the current value
    of global counter and then increases that counter by one."""
    global _creation_order
    self._creation_order = _creation_order
    _creation_order += 1


def maybe_callable(value, *args, **kwargs):
    """If ``value`` is callable, call it with given args and return result or
    otherwise return ``value``."""
    if callable(value):
        return value(*args, **kwargs)
    else:
        return value


def is_mutable(value):
    """Return ``True`` if ``value`` is instance of mutable type or ``False``
    otherwise."""
    return isinstance(value, (dict, list))


class memoized_property(object):
    """A read-only property that is only evaluated once."""

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result
