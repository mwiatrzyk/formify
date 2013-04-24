"""Decorator function and classes."""

import functools
import threading


def synchronized(lock=None):
    """Makes decorated function thread-safe."""

    if lock is None:
        lock = threading.Lock()

    def synchronized_proxy(f):

        @functools.wraps(f)
        def proxy(*args, **kwargs):
            lock.acquire()
            try:
                return f(*args, **kwargs)
            finally:
                lock.release()

        return proxy

    return synchronized_proxy


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
