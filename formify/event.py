"""The core of event processing system."""


def add_listener(sender, event, listener):
    """Register event listener.

    The behaviour of this function can be changed for each *sender* by
    supplying its class with ``on_add_listener`` method accepting *event* and
    *listener* as parameters.

    :param sender:
        event sender
    :param event:
        event name string or tuple object
    :param listener:
        listener callable
    """
    registrar = getattr(sender, 'on_add_listener', None)
    if registrar is not None:
        registrar(event, listener)
    else:
        if not hasattr(sender, '_event_listeners'):
            sender._event_listeners = {}
        sender._event_listeners.setdefault(event, []).append(listener)


def get_listeners(sender, event):
    """Event listeners generator.

    The behaviour of this function can be changed for each *sender* by
    supplying its class with ``on_get_listeners`` method accepting *event* as
    single parameter.

    :param sender:
        event sender
    :param event:
        event name string or tuple object
    """
    provider = getattr(sender, 'on_get_listeners', None)
    if provider is not None:
        source = provider(event)
    else:
        source = getattr(sender, '_event_listeners', {}).get(event, [])
    for listener in source:
        yield listener


def notify(sender, event, *args, **kwargs):
    """Execute all event listeners ignoring result.

    :param sender:
        event sender
    :param event:
        event name string or tuple object
    :param *args:
        positional args forwarded to each listener callable
    :param **kwargs:
        named args forwarded to each listener callable
    """
    for listener in get_listeners(sender, event):
        listener(*args, **kwargs)


def pipeline(sender, event, key, *args, **kwargs):
    """Execute all event listeners and use result of N-th listener as *key*
    argument of (N+1)-th listener.

    :param sender:
        event sender
    :param event:
        event name string or tuple object
    :param key:
        specifies which positional or keyword argument should be forwarded to
        next listener and finally returned as this function's result. Following
        values are allowed:

        ``int`` number
            if positional arg should be used; the value is arg's position
            within *args* tuple (can be negative as well)

        ``str`` value
            if keyword arg should be used; the value is name of keyword arg
    :param *args:
        positional args forwarded to each listener callable
    :param **kwargs:
        named args forwarded to each listener callable
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
