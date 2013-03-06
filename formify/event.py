"""The core of event processing system."""


def add_listener(sender, event, listener):
    if not hasattr(sender, '_event_listeners'):
        sender._event_listeners = {}
    sender._event_listeners.setdefault(event, []).append(listener)


def listeners_of(sender, event):
    for listener in getattr(sender, '_event_listeners', {}).get(event, []):
        yield listener


def listens_for(sender, event):
    def proxy(f):
        add_listener(sender, event, f)
        return f
    return proxy
