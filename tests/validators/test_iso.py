# tests/validators/test_iso.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import unittest

import formify


class ISBNTestsMixin(object):
    messages = {
        'pattern_mismatch': 'Invalid ISBN number',
        'checksum_mismatch': 'Invalid checksum: found %(found)s, should be %(expected)s'
    }

    def test_whenValidISBN10NumberGiven_validationSucceeds(self):
        self.uut(self.valid)

        self.assertEqual(self.valid, self.uut.value)
        self.assertEqual(self.valid_int, self.uut.int_value)
        self.assertTrue(self.uut.is_valid())

    def test_whenValueDoesNotMatchPattern_validationFails(self):
        self.uut(self.invalid)

        self.assertEqual(self.invalid, self.uut.value)
        self.assertFalse(self.uut.is_valid())
        self.assertIn('Invalid ISBN number', self.uut.errors)

    def test_whenChecksumInvalid_validationFails(self):
        self.uut(self.invalid_checksum)

        self.assertFalse(self.uut.is_valid())
        self.assertIn(
            'Invalid checksum: found %s, should be %s' % (self.invalid_checksum[-1], self.valid[-1]),
            self.uut.errors)


class TestISBN10(unittest.TestCase, ISBNTestsMixin):

    def setUp(self):
        self.uut = formify.ISBN10(standalone=True, messages=self.messages)

        self.valid = '81-7525-766-0'
        self.valid_int = 8175257660
        self.invalid = 'foo bar baz'
        self.invalid_checksum = '81-7525-766-1'


class TestISBN13(unittest.TestCase, ISBNTestsMixin):

    def setUp(self):
        self.uut = formify.ISBN13(standalone=True, messages=self.messages)

        self.valid = '978-81-7525-766-5'
        self.valid_int = 9788175257665
        self.invalid = 'foo bar baz'
        self.invalid_checksum = '978-81-7525-766-1'
