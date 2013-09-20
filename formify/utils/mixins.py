"""Collection of mixin classes."""


class KeyValueMixin(object):
    """Supplies classes providing :meth:`__iter__` and :meth:`__getitem__` with
    methods to retrieve keys, values and both (like in standard dict
    object)."""

    def iterkeys(self):
        for key in self:
            yield key

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        for key in self:
            yield self[key]

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for key in self:
            yield key, self[key]

    def items(self):
        return list(self.iteritems())
