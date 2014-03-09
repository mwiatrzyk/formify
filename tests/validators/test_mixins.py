# tests/validators/test_mixins.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import unittest

from formify.validators import mixins, Validator


class TestLengthValidationMixin(unittest.TestCase):

    def setUp(self):

        class UUT(Validator, mixins.LengthValidationMixin):
            python_type = unicode
            messages = {
                'value_too_short': 'Expecting at least %(min_length)s characters',
                'value_too_long': 'Expecting at most %(max_length)s characters',
                'value_length_out_of_range': 'Expecting number of characters between %(min_length)s and %(max_length)s'
            }

            def __init__(self, min_length=None, max_length=None, **kwargs):
                super(UUT, self).__init__(**kwargs)
                self.min_length = min_length
                self.max_length = max_length

        self.UUT = UUT

    def test_minLengthConstraint(self):
        uut = self.UUT(min_length=4, standalone=True)

        uut('spam')
        self.assertTrue(uut.is_valid())

        uut('spam more spam')
        self.assertTrue(uut.is_valid())

        uut('foo')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting at least 4 characters', uut.errors[0])

    def test_maxLengthConstraint(self):
        uut = self.UUT(max_length=3, standalone=True)

        uut('ab')
        self.assertTrue(uut.is_valid())

        uut('foo')
        self.assertTrue(uut.is_valid())

        uut('spam')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting at most 3 characters', uut.errors[0])

    def test_lengthRangeConstraint(self):
        uut = self.UUT(min_length=3, max_length=5, standalone=True)

        uut('foo')
        self.assertTrue(uut.is_valid())

        uut('spam')
        self.assertTrue(uut.is_valid())

        uut('abcde')
        self.assertTrue(uut.is_valid())

        uut('ab')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting number of characters between 3 and 5', uut.errors[0])

        uut('spam more spam')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting number of characters between 3 and 5', uut.errors[0])


class TestRangeValidationMixin(unittest.TestCase):

    def setUp(self):

        class UUT(Validator, mixins.RangeValidationMixin):
            python_type = int
            messages = {
                'value_too_low': 'Value must not be less than %(min_value)s',
                'value_too_high': 'Value must not be greater than %(max_value)s',
                'value_out_of_range': 'Expecting value between %(min_value)s and %(max_value)s'
            }

            def __init__(self, min_value=None, max_value=None, **kwargs):
                super(UUT, self).__init__(**kwargs)
                self.min_value = min_value
                self.max_value = max_value

        self.UUT = UUT

    def test_minimalValueConstraint(self):
        uut = self.UUT(min_value=4, standalone=True)

        uut('4')
        self.assertTrue(uut.is_valid())

        uut('5')
        self.assertTrue(uut.is_valid())

        uut('3')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Value must not be less than 4', uut.errors[0])

    def test_maximalValueConstraint(self):
        uut = self.UUT(max_value=5, standalone=True)

        uut('4')
        self.assertTrue(uut.is_valid())

        uut('5')
        self.assertTrue(uut.is_valid())

        uut('6')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Value must not be greater than 5', uut.errors[0])

    def test_valueRangeConstraint(self):
        uut = self.UUT(min_value=4, max_value=6, standalone=True)

        uut('4')
        self.assertTrue(uut.is_valid())

        uut('5')
        self.assertTrue(uut.is_valid())

        uut('6')
        self.assertTrue(uut.is_valid())

        uut('3')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting value between 4 and 6', uut.errors[0])

        uut('7')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting value between 4 and 6', uut.errors[0])
