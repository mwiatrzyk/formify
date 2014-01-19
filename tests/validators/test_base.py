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


class TestNumeric(unittest.TestCase):

    def setUp(self):

        class UUT(formify.Numeric):
            python_type = int

        self.UUT = UUT

    def test_conversion(self):
        uut = self.UUT(standalone=True)

        uut('123')

        self.assertIsInstance(uut.value, int)
        self.assertEqual(123, uut.value)


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


class TestListOf(unittest.TestCase):

    def setUp(self):
        self.uut = formify.ListOf(formify.Integer, standalone=True)

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
        uut = formify.ListOf(formify.Integer(max_value=3), standalone=True)

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
