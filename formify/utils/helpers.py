"""Set of helper functions and classes."""


_creation_order = 0
def set_creation_order(instance):
    """Set ``_creation_order`` attribute in the instance to current value and
    increase global counter by one."""
    global _creation_order
    instance._creation_order = _creation_order
    _creation_order += 1


def maybe_callable(value, *args, **kwargs):
    """If *value* is callable call it with provided args and kwargs and return
    result. Otherwise return unchanged *value*."""
    if callable(value):
        return value(*args, **kwargs)
    else:
        return value


class importlater(object):
    """Allows to import module at the time one of its attributes is
    accessed."""

    def __init__(self, name, *fromlist):
        self._il_name = name
        self._il_fromlist = fromlist
        self._il_module = None

    def _import(self):
        if self._il_module is None:
            if self._il_fromlist:
                self._il_module = __import__(self._il_name, fromlist=self._il_fromlist)
            else:
                if '.' in self._il_name:
                    self._il_module = __import__(self._il_name, fromlist=self._il_name.rsplit('.', 1)[1])
                else:
                    self._il_module = __import__(self._il_name)
        return self._il_module

    def __getattr__(self, name):
        return getattr(self._import(), name)

    def __setattr__(self, name, value):
        if name.startswith('_il_'):
            super(importlater, self).__setattr__(name, value)
        else:
            setattr(self._import(), name, value)

    def __delattr__(self, name):
        if name.startswith('_il_'):
            super(importlater, self).__delattr__(name)
        else:
            delattr(self._import(), name)
