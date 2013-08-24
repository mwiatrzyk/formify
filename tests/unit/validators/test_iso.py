import unittest

from formify import exc
from formify.validators.iso import *


class TestISBN(unittest.TestCase):
    ISBN10 = '0306406152'
    ISBN10_ENDING_WITH_X = '097522980X'
    ISBN10_INVALID_CHECKSUM = '0306406151'
    ISBN13 = '9783161484100'
    ISBN13_NON_ZERO_CHECKSUM = '9788371815102'
    NOT_AN_ISBN_NUMBER = '03064061521'

    def setUp(self):
        self.validator = ISBN()

    def test_ISBN10_ok(self):
        # When
        value = self.validator.process(self.ISBN10)
        # Then
        self.assertEqual(value, self.ISBN10)

    def test_ISBN10_ending_with_X(self):
        # When
        value = self.validator.process(self.ISBN10_ENDING_WITH_X)
        # Then
        self.assertEqual(value, self.ISBN10_ENDING_WITH_X)

    def test_ISBN10_invalid(self):
        # When
        def processor():
            self.validator.process(self.ISBN10_INVALID_CHECKSUM)
        # Then
        self.assertRaises(exc.ValidationError, processor)

    def test_ISBN13_ok(self):
        # When
        value = self.validator.process(self.ISBN13)
        # Then
        self.assertEqual(value, self.ISBN13)

    def test_ISBN13_ok_non_zero_checksum(self):
        # When
        value = self.validator.process(self.ISBN13_NON_ZERO_CHECKSUM)
        # Then
        self.assertEqual(value, self.ISBN13_NON_ZERO_CHECKSUM)

    def test_invalid_length(self):
        # When
        def process():
            self.validator.process(self.NOT_AN_ISBN_NUMBER)
        # Then
        self.assertRaises(exc.ValidationError, process)
