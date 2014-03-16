# tests/validators/test_base.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import unittest

import formify


class TestValidator(unittest.TestCase):

    def setUp(self):

        class UUT(formify.Validator):
            messages = dict(formify.Validator.messages)
            messages.update({
                'conversion_error': 'Not a valid integer number',
                'required_error': 'This field is required',
            })
            python_type = int

        self.UUT = UUT
        self.uut = UUT(standalone=True)

    def test_whenCreatingWithoutOwner_unboundValidatorIsCreated(self):
        self.assertIsInstance(self.UUT(), formify.UnboundValidator)

    def test_whenCreatingWithOwner_boundValidatorIsCreated(self):
        self.assertIsInstance(self.uut, self.UUT)

    def test_whenCalledWithConvertibleValue_conversionSucceeds(self):
        value = self.uut('123')

        self.assertIs(value, self.uut.value)
        self.assertEqual('123', self.uut.raw_value)
        self.assertEqual(123, self.uut.value)

    def test_whenCalledWithNotConvertibleValue_returnsNoneAndConversionFails(self):
        value = self.uut('abc')

        self.assertIs(value, None)
        self.assertIn('Not a valid integer number', self.uut.errors)
        self.assertFalse(self.uut.is_valid())

    def test_callingWithConvertibleValueClearsExistingMapOfErrors(self):
        self.uut('abc')
        self.assertEqual(1, len(self.uut.errors))

        self.uut('123')
        self.assertEqual(0, len(self.uut.errors))

    def test_whenRequiredAndValueIsMissing_validationFails(self):
        self.assertFalse(self.uut.is_valid())
        self.assertIn('This field is required', self.uut.errors)

    def test_whenPreprocessorAdded_itIsInvokedWhenProcessingBeforeConversion(self):
        values_preprocessed = set()

        def preprocess(self, value):
            values_preprocessed.add(value)
            if value.isalpha():
                return -1
            else:
                return value

        self.uut('x')
        self.assertEqual(0, len(values_preprocessed))
        self.assertFalse(self.uut.is_valid())

        self.uut.add_preprocessor(preprocess)

        self.uut('x')
        self.assertEqual(1, len(values_preprocessed))
        self.assertTrue(self.uut.is_valid())
        self.assertEqual(-1, self.uut.value)

        self.uut(123)
        self.assertEqual(1, len(values_preprocessed))  # not ivoked if conversion not needed
        self.assertTrue(self.uut.is_valid())
        self.assertEqual(123, self.uut.value)

    def test_whenPostprocessorAdded_itIsInvokedWhenProcessingAfterConversion(self):
        values_postprocessed = set()

        def postprocess(self, value):
            values_postprocessed.add(value)
            return str(value)

        self.uut.add_postprocessor(postprocess)

        self.uut(None)
        self.assertEqual(0, len(values_postprocessed))

        self.uut('x')
        self.assertEqual(0, len(values_postprocessed))
        self.assertFalse(self.uut.is_valid())

        self.uut(123)
        self.assertEqual(1, len(values_postprocessed))
        self.assertTrue(self.uut.is_valid())
        self.assertEqual('123', self.uut.value)

        self.uut('123')
        self.assertEqual(1, len(values_postprocessed))
        self.assertTrue(self.uut.is_valid())
        self.assertEqual('123', self.uut.value)

    def test_rawValueIsACopyInCaseOfMutableTypes(self):
        data = {}
        self.uut(data)
        self.assertIsNot(data, self.uut.raw_value)

        data = tuple()
        self.uut(data)
        self.assertIs(data, self.uut.raw_value)
