"""Formify library exceptions."""


class FormifyError(Exception):
    pass


class ValidationError(FormifyError, ValueError):
    pass


class ConversionError(FormifyError, TypeError):
    pass
