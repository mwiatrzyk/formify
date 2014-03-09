# formify/validators/iso.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

from formify import exc
from formify.validators.general import Regex


class BaseISBN(Regex):
    """Base class for ISBN number validators."""
    messages = dict(Regex.messages)
    messages.update({
        'pattern_mismatch': 'Not a valid ISBN number',
        'checksum_mismatch': 'Invalid checksum digit: found %(found)s, expecting %(expected)s)'
    })

    def __init__(self, **kwargs):
        super(BaseISBN, self).__init__(self.isbn_re, **kwargs)

    def validate(self, value):
        super(BaseISBN, self).validate(value)
        checksum = self.calculate_checksum(self.value)
        self.validate_checksum(value, checksum)

    def calculate_checksum(self, value):
        raise NotImplementedError("'calculate_checksum' is not implemented in %r" % self.__class__)

    def validate_checksum(self, value, checksum):
        if value[-1] != str(checksum):
            raise exc.ValidationError('checksum_mismatch', found=value[-1], expected=checksum)

    @property
    def int_value(self):
        return int(self.value.replace('-', ''))


class ISBN10(BaseISBN):
    """Validates ISBN10 numbers."""
    isbn_re = r'^\d+-\d+-\d+-\d$'

    def calculate_checksum(self, value):
        checksum = ndash = 0
        for i in xrange(len(value)-1):
            if value[i] != '-':
                checksum += (i - ndash + 1) * int(value[i])
            else:
                ndash += 1
        checksum %= 11
        if checksum == 10:
            return 'X'
        else:
            return str(checksum)


class ISBN13(BaseISBN):
    """Validates ISBN13 numbers."""
    isbn_re = r'^((978|979)-)?\d+-\d+-\d+-\d+$'

    def calculate_checksum(self, value):
        checksum = ndash = 0
        for i in xrange(len(value)-1):
            if value[i] == '-':
                ndash += 1
            else:
                if (i - ndash) % 2:
                    checksum += int(value[i]) * 3
                else:
                    checksum += int(value[i])
        checksum %= 10
        if checksum == 0:
            return '0'
        else:
            return str(10 - checksum)
