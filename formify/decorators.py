import functools


def message_formatter(*keys):

    def proxy(f):
        f._ffy_message_formatter_keys = set(keys)
        return f

    return proxy
