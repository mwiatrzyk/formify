# formify/decorators.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import functools


def message_formatter(*keys):

    def proxy(f):
        f._ffy_message_formatter_keys = set(keys)
        return f

    return proxy
