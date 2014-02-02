import decimal
import unittest
import collections

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


class TestFloat(unittest.TestCase, NumericTestsMixin):

    def setUp(self):
        self.UUT = formify.Float
        self.config = {
            'successful_conversion': {'raw_value': '3.14', 'value': 3.14},
            'failed_conversion': {'raw_value': 'abc'},
            'too_low': {'raw_value': '3.14', 'value': 3.14, 'min_value': 3.5},
            'too_high': {'raw_value': '3.14', 'value': 3.14, 'max_value': 3},
            'not_in_range': {'raw_value': '3.14', 'value': 3.14, 'min_value': 3.2, 'max_value': 3.3}
        }


class TestDecimal(unittest.TestCase, NumericTestsMixin):

    def setUp(self):
        self.UUT = formify.Decimal
        self.config = {
            'successful_conversion': {'raw_value': '3.14', 'value': decimal.Decimal('3.14')},
            'failed_conversion': {'raw_value': 'abc'},
            'too_low': {'raw_value': '3.14', 'value': decimal.Decimal('3.14'), 'min_value': 3.5},
            'too_high': {'raw_value': '3.14', 'value': decimal.Decimal('3.14'), 'max_value': 3},
            'not_in_range': {'raw_value': '3.14', 'value': decimal.Decimal('3.14'), 'min_value': 3.2, 'max_value': 3.3}
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


class TestAnyOf(unittest.TestCase):

    def setUp(self):
        self.uut = formify.AnyOf([
            formify.Integer(min_value=1),
            formify.Float], standalone=True)

    def test_initialState(self):
        self.assertIsInstance(self.uut.validator, self.uut.validators[-1])
        self.assertIs(self.uut.value, None)
        self.assertIs(self.uut.raw_value, None)
        self.assertFalse(self.uut.errors)

    def test_whenProcessingValue_firstValidatorThatSuccessfulyProcessesItIsUsed(self):
        self.uut('3.14')

        self.assertIsInstance(self.uut.validator, formify.Float)
        self.assertIs(self.uut.python_type, float)
        self.assertEqual(3.14, self.uut.value)

        self.uut('1')

        self.assertIsInstance(self.uut.validator, formify.Integer)
        self.assertIs(self.uut.python_type, int)
        self.assertEqual(1, self.uut.value)

    def test_whenNoValidatorCouldProcessValue_processingFails(self):
        self.uut('abc')

        self.assertIs(self.uut.value, None)
        self.assertIsInstance(self.uut.validator, formify.Float)
        self.assertFalse(self.uut.is_valid())
        self.assertTrue(self.uut.errors)

    def test_whenProcessingValidValueAfterInvalidOne_validatorIsAssigned(self):
        self.uut('abc')
        self.assertIsInstance(self.uut.validator, formify.Float)

        self.uut('1')
        self.assertIsInstance(self.uut.validator, formify.Integer)

    def test_whenValidationFailsForCurrentValidator_validatorIsChanged(self):
        self.uut('-1')

        self.assertIsInstance(self.uut.validator, formify.Integer)
        self.assertEqual(-1, self.uut.value)

        self.assertTrue(self.uut.is_valid())

        self.assertIsInstance(self.uut.validator, formify.Float)
        self.assertEqual(-1.0, self.uut.value)


class TestBaseEnum(unittest.TestCase):

    def test_createWithDictAsOptions(self):
        uut = formify.BaseEnum({1: 'One'}, standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)

    def test_createWithListOfTuplesAsOptions(self):
        uut = formify.BaseEnum([(1, 'One')], standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)

    def test_createWithOrderedDictAsOptions(self):
        uut = formify.BaseEnum(collections.OrderedDict({1: 'One'}), standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)


class TestEnum(unittest.TestCase):
    options = {
        1: 'One',
        2: 'Two'
    }

    def test_validInputData(self):
        uut = formify.Enum(self.options, key_type=int, standalone=True)

        self.assertIs(uut.python_type, int)

        uut('1')
        self.assertEqual(1, uut.value)
        self.assertTrue(uut.is_valid())

        uut(2)
        self.assertEqual(2, uut.value)
        self.assertTrue(uut.is_valid())

    def test_invalidInputData(self):
        uut = formify.Enum(self.options, key_type=int, standalone=True)

        uut('3')
        self.assertEqual(3, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Invalid option: 3', uut.errors)


class TestMultiEnum(unittest.TestCase):
    options = {
        1: 'One',
        2: 'Two',
        3: 'Thre'
    }

    def test_validInputData(self):
        uut = formify.MultiEnum(self.options, key_type=int, standalone=True)

        uut('1')
        self.assertEqual(set([1]), uut.value)
        self.assertTrue(uut.is_valid())

        uut('13')
        self.assertEqual(set([1, 3]), uut.value)
        self.assertTrue(uut.is_valid())

        uut([1, 2, 3])
        self.assertEqual(set([1, 2, 3]), uut.value)
        self.assertTrue(uut.is_valid())

    def test_invalidInputData(self):
        uut = formify.MultiEnum(self.options, key_type=int, standalone=True)

        uut(1)
        self.assertIs(uut.value, None)
        self.assertFalse(uut.is_valid())

        uut('4')
        self.assertEqual(set([4]), uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Invalid options: set([4])', uut.errors)

        uut('a')
        self.assertEqual(set([None]), uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'a' to <type 'int'> object", uut.errors)

        uut('ab')
        self.assertEqual(set([None]), uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'a' to <type 'int'> object", uut.errors)
        self.assertIn("Unable to convert 'b' to <type 'int'> object", uut.errors)

        uut('ab12')
        self.assertEqual(set([None, 1, 2]), uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'a' to <type 'int'> object", uut.errors)
        self.assertIn("Unable to convert 'b' to <type 'int'> object", uut.errors)


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
