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
