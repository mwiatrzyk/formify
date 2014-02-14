# formify/exc.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php


class ConversionError(TypeError):

    def __init__(self, message_id, **params):
        self.message_id = message_id
        self.params = params


class ValidationError(ValueError):

    def __init__(self, message_id, **params):
        self.message_id = message_id
        self.params = params
