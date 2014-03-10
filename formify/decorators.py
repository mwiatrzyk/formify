# formify/decorators.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

"""Module containing various decorator functions."""

import functools


def message_formatter(*message_ids):
    """Decorate validator method to be a custom message formatter.

    Decorated method should return formatted string and accept one required
    positional argument (``message_id``) and set of message parameters (if
    message has any). Example::

        class MyValidator(formify.Validator):
            messages = dict(formify.Validator.messages)
            messages.update({
                'my_message': 'Something wrong happend with value %(value)s'
            })

            @message_formatter('my_message')
            def my_message_formatter(self, message_id, value):
                return self.messages[message_id] % {'value': do_sth_with_value(value)}

    """

    def proxy(f):
        f._ffy_message_formatter = set(message_ids)
        return f

    return proxy


def preprocessor(*validator_keys):
    """Decorate schema method as preprocessor of given validators."""

    def proxy(f):
        f._ffy_preprocessor = set(validator_keys)
        return f

    return proxy
