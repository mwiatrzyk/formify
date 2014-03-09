# formify/schema.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import collections

from formify import _utils
from formify.validators import UnboundValidator

__all__ = ['SchemaMeta', 'Schema']


class SchemaMeta(type):
    """Metaclass for :class:`Schema`."""

    @property
    def __validators__(cls):
        """Map of unbound validators defined in schema sorted by creation
        order."""
        attrs = []
        for name in dir(cls):
            if name == '__validators__':
                continue
            value = getattr(cls, name)
            if isinstance(value, UnboundValidator):
                if value.key is None:
                    value.key = name
                attrs.append((value.key, value))
        attrs.sort(key=lambda x: x[1]._creation_order)
        return collections.OrderedDict(attrs)


class Schema(object):
    """Base class for data entities."""
    __metaclass__ = SchemaMeta

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __iter__(self):
        for k in self.__validators__:
            yield k

    def __contains__(self, key):
        return key in self.__validators__

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(Schema, self).__setattr__(name, value)
        elif name not in self:
            raise AttributeError("unable to set attribute: %s" % name)
        else:
            self[name].process(value)

    def __getattribute__(self, name):
        if name.startswith('_') or name not in self:
            value = super(Schema, self).__getattribute__(name)
            if isinstance(value, UnboundValidator):
                raise AttributeError("unable to get attribute: %s" % name)
            return value
        else:
            return self[name].value

    def __getitem__(self, key):
        if key in self:
            return self.__validators__[key]
        else:
            raise KeyError(key)

    @_utils.memoized_property
    def __validators__(self):
        """Map of validators defined as class attributes and sorted by creation
        order."""
        validators = collections.OrderedDict()
        for k, v in self.__class__.__validators__.iteritems():
            validators[k] = v(owner=self)
        return validators

    @property
    def errors(self):
        """Map of schema errors."""
        result = {}
        for k, v in self.__validators__.iteritems():
            errors = v.errors
            if errors:
                result[k] = errors
        return result

    def is_valid(self):
        """Check if schema object is valid.

        Calling this method invokes validation process in all validators. If
        one or more validators cannot validate their values validation of
        entire schema fails.
        """
        status = True
        for v in self.__validators__.itervalues():
            if not v.is_valid():
                status = False
        return status
