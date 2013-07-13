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


def is_iterable(value):
    """Check if *value* is iterable.

    An object is said to be an iterable object if it contains ``__iter__``
    method.
    """
    return hasattr(value, '__iter__')


def is_sequence(value):
    """Check if *value* is a sequence.

    An object is said to be a sequence if it contains ``__len__`` and
    ``__getitem__`` methods.
    """
    return hasattr(value, '__len__') and hasattr(value, '__getitem__')


def is_mapping(value):
    """Check if *value* is a mapping.

    An object is said to be a mapping if it is a sequence and contains ``keys``
    method.
    """
    return is_sequence(value) and hasattr(value, 'keys')

def get_multimapping_getlist(value):
    """Retrieve ``getlist`` method (used to get all values for given key) if
    *value* is a multi-dictionary object.

    If *value* is not multi-dictionary or, ``None`` is returned.
    """
    if not is_mapping(value):
        return None
    if hasattr(value, 'getlist'):  # i.e. ImmutableMultiDict from Flask
        return value.getlist
    else:
        return None
