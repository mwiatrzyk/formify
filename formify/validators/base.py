from formify.validators import Validator

__all__ = ['String', 'Int', 'Bool']


class String(Validator):
    python_type = unicode


class Int(Validator):
    python_type = int


class Bool(Validator):
    python_type = bool
