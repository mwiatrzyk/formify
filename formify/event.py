"""The core of event processing system."""

import weakref

F_READ_ACCESS = 1
F_WRITE_ACCESS = 2


def _get_real_sender(sender, flags):
    """Helper used to get real sender from given *sender*."""
    if hasattr(sender, '_event_alias_of'):
        if sender._event_alias_flags & flags != flags:
            raise TypeError("sender does not allow requested operation")
        sender = sender._event_alias_of()
    return sender


def add_listener(sender, event, listener):
    """Register event listener.

    This function first checks if there is a :meth:`add_listener` method
    defined in *sender*. If such method does not exist, default event listener
    registration process takes place. Otherwise sender's :meth:`add_listener`
    is called with following arguments:

    *event*
        event identifier

    *listener*
        event listener callable

    *default_registrar*
        function that takes same arguments as :func:`add_listener` and performs
        default event listener registration process

    :param sender:
        event sender
    :param event:
        event identifier
    :param listener:
        listener callable
    """

    def default_registrar(sender, event, listener):
        if not hasattr(sender, '_event_listeners'):
            sender._event_listeners = {}
        listeners = sender._event_listeners.setdefault(event, [])
        if listener not in listeners:
            listeners.append(listener)

    sender = _get_real_sender(sender, F_WRITE_ACCESS)
    registrar = getattr(sender, 'add_listener', None)
    if registrar is not None:
        registrar(event, listener, default_registrar)
    else:
        default_registrar(sender, event, listener)


def get_listeners(sender, event):
    """Return list of all event listeners registered for given event.

    This function first checks if there is a :meth:`get_listeners` method
    defined in *sender*. If such method does not exist, default event listener
    retrieval action is performed. Otherwise sender's :meth:`get_listeners` is
    expected to return registered listeners and is called with following
    arguments to do so:

    *event*
        event identifier

    *default_getter*
        function that takes same arguments as :func:`get_listeners` and
        performs default event listeners retrieval process

    :param sender:
        event sender
    :param event:
        event identifier
    """

    def default_getter(sender, event):
        return getattr(sender, '_event_listeners', {}).get(event, [])

    sender = _get_real_sender(sender, F_READ_ACCESS)
    provider = getattr(sender, 'get_listeners', None)
    if provider is not None:
        return provider(event, default_getter)
    else:
        return default_getter(sender, event)


def alias_of(sender, real_sender, flags=F_READ_ACCESS|F_WRITE_ACCESS):
    """Make *sender* an alias of *real_sender*.

    All event operations performed on alias are forwarded to *real_sender*.
    Currently alias is a weak reference to real sender.

    :param sender:
        sender that will be an alias
    :param real_sender:
        real sender to which requests will be forwarded
    :param flags:
        alias access flags. Following options are available:

        ``F_READ_ACCESS``
            alias supports all operations that does not modify already
            registered events listeners (f.e. :func:`get_listeners`)

        ``F_WRITE_ACCESS``
            alias supports all operations that do mofify already registered
            events and listeners (f.e. :func:`add_listener`)
    """
    sender._event_alias_of = weakref.ref(real_sender)
    sender._event_alias_flags = flags


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
