"""Formify library exceptions."""


class FormifyError(Exception):
    """Common base class for all Formify exceptions."""


class BindError(FormifyError):
    pass


class AlreadyBound(BindError):
    """Raised when already bound validator is tried to bind once again."""


class NotBound(BindError):
    """Raised when trying to unbind validator that was not bound to any
    schema."""


class ValidationError(FormifyError, ValueError):
    """Raised when validation error occurs.

    This exception should be used to cover errors occuring after the value had
    been converted to valid type.
    """


class ConversionError(FormifyError, TypeError):
    """Raised when it is unable to convert string to value of type supported by
    validator."""
