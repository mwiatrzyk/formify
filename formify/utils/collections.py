"""General purpose collection classes."""


class OrderedDict(object):
    """Dictionary that remembers order of its keys."""

    def __init__(self, iterable=None):
        self.clear()
        for k, v in (iterable or []):
            self[k] = v

    def __setitem__(self, key, value):
        if key not in self._storage:
            self._order.append(key)
        self._storage[key] = value

    def __getitem__(self, key):
        if key not in self._storage:
            raise KeyError(key)
        return self._storage[key]

    def __delitem__(self, key):
        if key not in self._storage:
            raise KeyError(key)
        del self._storage[key]
        self._order.remove(key)

    def __contains__(self, key):
        return key in self._storage

    def __iter__(self):
        for k in self._order:
            yield k

    def __len__(self):
        return len(self._order)

    def __repr__(self):
        tmp = ["%r: %r" % (k, v) for k, v in self.iteritems()]
        return "{%s}" % (', '.join(tmp))

    def clear(self):
        self._storage = {}
        self._order = []

    def copy(self):
        result = self.__class__()
        result._storage = dict(self._storage)
        result._order = list(self._order)
        return result

    def iterkeys(self):
        for k in self._order:
            yield k

    def itervalues(self):
        for k in self._order:
            yield self._storage[k]

    def iteritems(self):
        for k in self._order:
            yield k, self._storage[k]

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def get(self, key, default=None):
        if key in self._storage:
            return self._storage[key]
        else:
            return default

    def pop(self, *args):
        if len(args) > 2:
            raise TypeError(
                "pop() takes at most 2 arguments, got %d" %
                len(args))
        elif not args:
            raise TypeError("pop() takes at least 1 argument, got 0")
        elif args[0] in self._storage:
            value = self._storage.pop(args[0])
            self._order.remove(args[0])
            return value
        elif len(args) == 2:
            return args[1]
        else:
            raise KeyError(args[0])

    def popitem(self):
        if not self._storage:
            raise KeyError("popitem(): dictionary is empty")
        key = self._order.pop()
        value = self._storage.pop(key)
        return key, value

    def setdefault(self, key, default=None):
        result = self.get(key, default)
        if key not in self:
            self[key] = default
        return result

    def update(self, iterable):
        for k, v in iterable:
            self[k] = v
