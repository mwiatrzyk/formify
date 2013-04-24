"""The core of event processing system."""


def add_listener(sender, event, listener):
    """Register event listener.

    This function is used to append new event listener to the end of list of
    event listeners registered for given *sender* and *event*. Default
    behaviour of this method can be overriden by defining :meth:`add_listener`
    method in *sender*'s class. If such method is found, it is called with
    *event* and *listener* arguments and no further processing is performed.

    :param sender:
        event sender
    :param event:
        event identifier
    :param listener:
        listener callable
    """
    registrar = getattr(sender, 'add_listener', None)
    if registrar is not None:
        registrar(event, listener)
    else:
        if not hasattr(sender, '_event_listeners'):
            sender._event_listeners = {}
        sender._event_listeners.setdefault(event, []).append(listener)


def get_listeners(sender, event):
    """Return list of all event listeners registered for given event.

    This function returns list of event listeners preserving listener
    registration order. Default behaviour can be changed by defining
    :meth:`get_listeners` method in *sender*'s class. If one is found, it is
    called with *event* argument and its return value is returned.

    :param sender:
        event sender
    :param event:
        event identifier
    """
    provider = getattr(sender, 'get_listeners', None)
    if provider is not None:
        return provider(event)
    else:
        return getattr(sender, '_event_listeners', {}).get(event, [])


def notify(sender, event, *args, **kwargs):
    """Execute all event listeners ignoring result.

    :param sender:
        event sender
    :param event:
        event identifier
    :param *args:
        positional args forwarded to listeners
    :param **kwargs:
        keyword args forwarded to listeners
    """
    for listener in get_listeners(sender, event):
        listener(*args, **kwargs)


def pipeline(sender, event, key, *args, **kwargs):
    """Execute all event listeners and use result of N-th listener as *key*
    argument of (N+1)-th listener.

    :param sender:
        event sender
    :param event:
        event identifier
    :param key:
        specifies which positional or keyword argument should be forwarded to
        next listener and finally returned as this function's result. Following
        values are allowed:

        * index of positional arg (``int``)
        * name of keyword argument (``str``)
    :param *args:
        positional args forwarded to listeners
    :param **kwargs:
        keyword args forwarded to listeners
    """
    if isinstance(key, int):
        args = list(args)
        result = args[key]
    else:
        result = kwargs[key]
    for listener in get_listeners(sender, event):
        result = listener(*args, **kwargs)
        if isinstance(key, int):
            args[key] = result
        else:
            kwargs[key] = result
    return result


def listens_for(sender, *event):
    """A decorator used to mark given function as event listener."""
    if not event:
        raise TypeError("event name is missing")

    def proxy(f):
        add_listener(sender, event[0] if len(event) == 1 else event, f)
        return f

    return proxy
