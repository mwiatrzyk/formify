# formify/exc.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

"""Set of exception classes used by the library."""


class FormifyError(Exception):
    """Base class for all exceptions defined in this module.

    :param message_id:
        ID of message from :attr:`~formify.validators.Validator.messages` map
    :param `**params`:
        message parameters
    """

    def __init__(self, message_id, **params):
        self.message_id = message_id
        self.params = params


class ConversionError(FormifyError, TypeError):
    """Exception raised when conversion error occurs.

    This exception is raised by :meth:`~formify.validators.Validator.convert`
    method when it is unable to convert input data to expected type.
    """


class ValidationError(FormifyError, ValueError):
    """Exception raised when validation error occurs.

    This exception is raised by
    :meth:`~formify.validators.BaseValidator.validate` method when validation
    fails for converted value of known type.
    """
