"""ISO standard validators."""

from formify import exc
from formify.validators import Regex

__all__ = ['ISBN']


class ISBN(Regex):
    """Validator for ISBN numbers."""

    def __init__(self, **kwargs):
        kwargs.pop('pattern', None)
        super(ISBN, self).__init__(pattern=r'[0-9]+X?', **kwargs)

    def postvalidate(self, value):
        value = super(ISBN, self).postvalidate(value)
        checksum = self.__calculate_checksum(value)
        if checksum is None:
            raise exc.ValidationError(
                "ISBN number is expected to have either 10 or 13 digits")
        elif value[-1] != checksum:
            raise exc.ValidationError("ISBN checksum verification failed")
        else:
            return value

    def __calculate_checksum(self, value):
        if len(value) == 10:
            return self.__calculate_checksum_for_isbn_of_length_10(value)
        elif len(value) == 13:
            return self.__calculate_checksum_for_isbn_of_length_13(value)
        else:
            return None

    def __calculate_checksum_for_isbn_of_length_10(self, value):
        checksum = 0
        for i in xrange(len(value)-1):
            checksum += (i + 1) * int(value[i])
        checksum %= 11
        if checksum == 10:
            return 'X'
        else:
            return str(checksum)

    def __calculate_checksum_for_isbn_of_length_13(self, value):
        checksum = 0
        for i in xrange(len(value)-1):
            if i % 2:
                checksum += int(value[i]) * 3
            else:
                checksum += int(value[i])
        checksum %= 10
        if checksum == 0:
            return '0'
        else:
            return str(10 - checksum)
