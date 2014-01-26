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


class TestString(unittest.TestCase):

    def test_conversion(self):
        uut = formify.String(standalone=True)

        uut(123)

        self.assertIsInstance(uut.value, unicode)
        self.assertEqual(u'123', uut.value)


class NumericTestsMixin(object):
    messages = {
        'conversion_error': 'Unable to convert',
        'value_too_low': 'Value too low',
        'value_too_high': 'Value too high',
        'value_out_of_range': 'Value out of range'
    }

    def test_successfulConversion(self):
        config = self.config['successful_conversion']
        raw_value, value = config['raw_value'], config['value']
        uut = self.UUT(standalone=True, messages=self.messages)

        uut(raw_value)

        self.assertIsInstance(uut.value, uut.python_type)
        self.assertEqual(value, uut.value)

    def test_failedConversion(self):
        config = self.config['failed_conversion']
        raw_value = config['raw_value']
        uut = self.UUT(standalone=True, messages=self.messages)

        uut(raw_value)

        self.assertIs(uut.value, None)
        self.assertIn('Unable to convert', uut.errors)

    def test_whenTooLowGiven_validationFails(self):
        config = self.config['too_low']
        raw_value, value, min_value = config['raw_value'], config['value'], config['min_value']
        uut = self.UUT(min_value=min_value, standalone=True, messages=self.messages)

        uut(raw_value)

        self.assertEqual(value, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Value too low', uut.errors)

    def test_whenTooHighGiven_validationFails(self):
        config = self.config['too_high']
        raw_value, value, max_value = config['raw_value'], config['value'], config['max_value']
        uut = self.UUT(max_value=max_value, standalone=True, messages=self.messages)

        uut(raw_value)

        self.assertEqual(value, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Value too high', uut.errors)

    def test_whenNotInRange_validationFails(self):
        config = self.config['not_in_range']
        raw_value, value, min_value, max_value = config['raw_value'], config['value'], config['min_value'], config['max_value']
        uut = self.UUT(min_value=min_value, max_value=max_value, standalone=True, messages=self.messages)

        uut(raw_value)

        self.assertEqual(value, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Value out of range', uut.errors)


class TestInteger(unittest.TestCase, NumericTestsMixin):

    def setUp(self):
        self.UUT = formify.Integer
        self.config = {
            'successful_conversion': {'raw_value': '123', 'value': 123},
            'failed_conversion': {'raw_value': 'abc'},
            'too_low': {'raw_value': '5', 'value': 5, 'min_value': 6},
            'too_high': {'raw_value': '5', 'value': 5, 'max_value': 4},
            'not_in_range': {'raw_value': '5', 'value': 5, 'min_value': 6, 'max_value': 7}
        }


class TestRegex(unittest.TestCase):

    def setUp(self):
        self.uut = formify.Regex(r'^[0-9]+$', standalone=True)

    def test_whenValueMatchesPattern_validationSucceeds(self):
        self.uut('123')

        self.assertTrue(self.uut.is_valid())
        self.assertEqual('123', self.uut.value)

    def test_whenValueDoesNotMatchPattern_validationFails(self):
        self.uut('0x123')

        self.assertFalse(self.uut.is_valid())
        self.assertEqual('0x123', self.uut.value)
        self.assertEqual('Value does not match pattern ^[0-9]+$', self.uut.errors[0])


class TestList(unittest.TestCase):

    def setUp(self):
        self.uut = formify.List(formify.Integer, standalone=True)

    def test_ifUnableToConvertToList_conversionFails(self):
        self.uut(123)

        self.assertIs(self.uut.value, None)

    def test_whenListGiven_itIsProcessed(self):
        self.uut(['123'])

        self.assertEqual([123], self.uut.value)

    def test_whenValidatorIsIterated_itYieldsValueValidators(self):
        self.uut('123')

        self.assertEqual([1, 2, 3], [x.value for x in self.uut])

    def test_lenReturnsNumberOfItemsInProcessedList(self):
        self.assertEqual(0, len(self.uut))

        self.uut('123')
        self.assertEqual(3, len(self.uut))

        self.uut('1')
        self.assertEqual(1, len(self.uut))

        self.uut('abc')
        self.assertEqual(3, len(self.uut))

    def test_whenAccessingIndex_validatorForValueAtThatIndexIsReturned(self):
        self.uut('123')

        self.assertEqual(1, self.uut[0].value)
        self.assertEqual(2, self.uut[1].value)
        self.assertEqual(3, self.uut[2].value)

    def test_whenAccessingNonExistingIndex_exceptionIsRaised(self):
        with self.assertRaises(IndexError):
            self.uut[0]

    def test_whenConversionOfSomeItemsFails_noneIsUsedInPlaceOfThatItems(self):
        self.uut('1a2b')

        self.assertFalse(self.uut.is_valid())
        self.assertEqual([1, None, 2, None], self.uut.value)
        self.assertFalse(self.uut[1].is_valid())
        self.assertFalse(self.uut[3].is_valid())

    def test_whenCheckingValidity_innerValidatorsAffectTheResult(self):
        uut = formify.List(formify.Integer(max_value=3), standalone=True)

        uut([3])
        self.assertTrue(uut.is_valid())

        uut([4])
        self.assertFalse(uut.is_valid())


class TestMap(unittest.TestCase):

    def setUp(self):

        class Entity(formify.Entity):
            a = formify.Integer()
            b = formify.String()

        self.Entity = Entity
        self.uut = formify.Map(self.Entity, standalone=True)

    def test_createFromEntity(self):
        uut = formify.Map(self.Entity, standalone=True)

        uut({'a': '1', 'b': 2})

        self.assertEqual({'a': 1, 'b': '2'}, uut.value)

    def test_createFromDict(self):
        uut = formify.Map({'a': formify.Integer, 'b': formify.String}, standalone=True)

        uut({'a': '1', 'b': 2})

        self.assertEqual({'a': 1, 'b': '2'}, uut.value)

    def test_ifNoValidatorForInputDataKey_exceptionIsRaised(self):
        with self.assertRaises(KeyError):
            self.uut({'a': '1', 'b': 2, 'c': 3.14})

    def test_ifUnableToConvertToDict_processingFails(self):
        self.uut(123)

        self.assertIs(self.uut.value, None)

    def test_whenIterating_yieldsKeys(self):
        self.assertEqual(['a', 'b'], list(self.uut))

    def test_gettingAnItemReturnsInnerValidator(self):
        self.uut({'a': '1', 'b': 2})

        self.assertEqual(1, self.uut['a'].value)
        self.assertEqual('2', self.uut['b'].value)

    def test_whenConversionOfElementFails_noneIsUsedAsElementsValueAndValidationFails(self):
        self.uut({'a': 'abc', 'b': 2})

        self.assertEqual({'a': None, 'b': '2'}, self.uut.value)
        self.assertFalse(self.uut.is_valid())

    def test_whenValidationOfElementFails_correspondingInnerValidatorContainsErrors(self):
        uut = formify.Map({'a': formify.Integer(max_value=2)}, standalone=True)

        uut({'a': 3})

        self.assertEqual({'a': 3}, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertTrue(uut['a'].errors)
