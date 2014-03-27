# tests/validators/test_general.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import decimal
import datetime
import unittest
import collections

import formify


class TestString(unittest.TestCase):

    def test_conversion(self):
        uut = formify.String(standalone=True)

        uut(123)

        self.assertIsInstance(uut.value, unicode)
        self.assertEqual(u'123', uut.value)


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


class TestURL(unittest.TestCase):

    def test_ifValidUrlGiven_validationSucceeds(self):
        uut = formify.URL(standalone=True)

        uut('http://www.example.com/foo/bar/baz.html')
        self.assertTrue(uut.is_valid())

        uut('https://example.com')
        self.assertTrue(uut.is_valid())

        uut('ftp://example.com/foo.txt')
        self.assertTrue(uut.is_valid())

        uut('www.example.com')
        self.assertTrue(uut.is_valid())

    def test_ifInvalidUrlGiven_validationFails(self):
        uut = formify.URL(standalone=True)

        uut('foo')
        self.assertFalse(uut.is_valid())
        self.assertIn('Invalid URL address', uut.errors)

        uut('http:/example')
        self.assertFalse(uut.is_valid())

        uut('http://www.example..com')
        self.assertFalse(uut.is_valid())

        uut('http://example')
        self.assertFalse(uut.is_valid())


class TestEmail(unittest.TestCase):

    def test_ifValidEmailGiven_validationSucceeds(self):
        uut = formify.Email(standalone=True)

        uut('foo@bar.baz')
        self.assertTrue(uut.is_valid())

        uut('john.doe@foo.bar.baz')
        self.assertTrue(uut.is_valid())

    def test_ifInvalidEmailGiven_validationFails(self):
        uut = formify.Email(standalone=True)

        uut('spam')
        self.assertFalse(uut.is_valid())
        self.assertIn('Invalid e-mail address', uut.errors)

        uut('foo@@bar.baz')
        self.assertFalse(uut.is_valid())

        uut('foo@bar')
        self.assertFalse(uut.is_valid())

        uut('foo@bar..baz')
        self.assertFalse(uut.is_valid())

        uut('foo@bar.baz.spaaam')
        self.assertFalse(uut.is_valid())


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


class TestBoolean(unittest.TestCase):

    def test_customTruesAndFalses(self):
        uut = formify.Boolean(trues='y', falses='n', standalone=True)

        self.assertIs(uut('y'), True)
        self.assertIs(uut('n'), False)

        self.assertIs(uut('Y'), None)
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'Y' to <type 'bool'> object", uut.errors)

        self.assertIs(uut('N'), None)
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'N' to <type 'bool'> object", uut.errors)

    def test_validInputData(self):
        uut = formify.Boolean(standalone=True)

        self.assertIs(uut('1'), True)
        self.assertIs(uut(1), True)
        self.assertIs(uut('y'), True)
        self.assertIs(uut('yes'), True)
        self.assertIs(uut('on'), True)
        self.assertIs(uut('true'), True)
        self.assertIs(uut(True), True)

        self.assertIs(uut('0'), False)
        self.assertIs(uut(0), False)
        self.assertIs(uut('n'), False)
        self.assertIs(uut('no'), False)
        self.assertIs(uut('off'), False)
        self.assertIs(uut('false'), False)
        self.assertIs(uut(False), False)

    def test_invalidInputData(self):
        uut = formify.Boolean(standalone=True)

        uut('yes or no')
        self.assertFalse(uut.is_valid())
        self.assertIn("Unable to convert 'yes or no' to <type 'bool'> object", uut.errors)


class TestDateTime(unittest.TestCase):

    def setUp(self):
        self.uut = formify.DateTime('%Y-%m-%d %H:%M:%S', standalone=True)

    def test_parseFromStringThatMatchesPattern(self):
        self.uut('2000-01-01 07:30:59')

        self.assertEqual(datetime.datetime(2000, 1, 1, 7, 30, 59), self.uut.value)

    def test_parseFromStringThatDoesNotMatchPattern(self):
        self.uut('2000-01-01')

        self.assertIs(self.uut.value, None)
        self.assertIn('Input date/time does not match format %Y-%m-%d %H:%M:%S', self.uut.errors)

    def test_parseFromNonString(self):
        self.uut(123)

        self.assertIs(self.uut.value, None)
        self.assertIn('Can only parse strings', self.uut.errors)

    def test_parseFromObjectOfSameType(self):
        date = datetime.datetime(2000, 1, 1)

        self.uut(date)

        self.assertIs(self.uut.value, date)

    def test_minDateConstraint(self):
        uut = formify.DateTime('%Y-%m-%d', min_value=datetime.datetime(2000, 1, 1), standalone=True)

        uut('2000-01-01')
        self.assertTrue(uut.is_valid())

        uut('2000-01-02')
        self.assertTrue(uut.is_valid())

        uut('1999-12-31')
        self.assertFalse(uut.is_valid())
        self.assertIn('Minimal date is 2000-01-01', uut.errors)

    def test_maxDateConstraint(self):
        uut = formify.DateTime('%Y-%m-%d', max_value=datetime.datetime(2000, 1, 1), standalone=True)

        uut('1999-12-31')
        self.assertTrue(uut.is_valid())

        uut('2000-01-01')
        self.assertTrue(uut.is_valid())

        uut('2000-01-02')
        self.assertFalse(uut.is_valid())
        self.assertIn('Maximal date is 2000-01-01', uut.errors)

    def test_dateRangeConstraint(self):
        uut = formify.DateTime('%Y-%m-%d', min_value=datetime.datetime(2000, 1, 1), max_value=datetime.datetime(2000, 12, 31), standalone=True)

        uut('2000-01-01')
        self.assertTrue(uut.is_valid())

        uut('2000-06-01')
        self.assertTrue(uut.is_valid())

        uut('2000-12-12')
        self.assertTrue(uut.is_valid())

        uut('1999-12-31')
        self.assertFalse(uut.is_valid())
        self.assertIn('Expecting date between 2000-01-01 and 2000-12-31', uut.errors)

        uut('2001-01-01')
        self.assertFalse(uut.is_valid())
        self.assertIn('Expecting date between 2000-01-01 and 2000-12-31', uut.errors)


class TestPassword(unittest.TestCase):

    def test_hashIsProducedAsOutput(self):
        uut = formify.Password(standalone=True)

        uut('A')

        self.assertTrue(uut.is_valid())
        self.assertEqual('A', uut.raw_value)
        self.assertEqual('6dcd4ce23d88e2ee9568ba546c007c63d9131c1b', uut.value)

    def test_passwordTooShort(self):
        uut = formify.Password(min_length=4, max_length=8, standalone=True)

        uut('A')

        self.assertFalse(uut.is_valid())
        self.assertIn('Expected number of characters is between 4 and 8', uut.errors)

    def test_passwordTooLong(self):
        uut = formify.Password(min_length=4, max_length=8, standalone=True)

        uut('ABCDEFGHI')

        self.assertFalse(uut.is_valid())
        self.assertIn('Expected number of characters is between 4 and 8', uut.errors)

    def test_passwordCorrect(self):
        uut = formify.Password(min_length=4, max_length=8, standalone=True)

        uut('ABCD')
        self.assertTrue(uut.is_valid())

        uut('ABCDEFGH')
        self.assertTrue(uut.is_valid())


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


class TestBaseChoice(unittest.TestCase):

    def test_createWithDictAsOptions(self):
        uut = formify.BaseChoice({1: 'One'}, standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)

    def test_createWithListOfTuplesAsOptions(self):
        uut = formify.BaseChoice([(1, 'One')], standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)

    def test_createWithOrderedDictAsOptions(self):
        uut = formify.BaseChoice(collections.OrderedDict({1: 'One'}), standalone=True)
        self.assertIsInstance(uut.options, collections.OrderedDict)
        self.assertEqual({1: 'One'}, uut.options)


class TestChoice(unittest.TestCase):
    options = {
        1: 'One',
        2: 'Two'
    }

    def test_validInputData(self):
        uut = formify.Choice(self.options, key_type=int, standalone=True)

        self.assertIs(uut.python_type, int)

        uut('1')
        self.assertEqual(1, uut.value)
        self.assertTrue(uut.is_valid())

        uut(2)
        self.assertEqual(2, uut.value)
        self.assertTrue(uut.is_valid())

    def test_invalidInputData(self):
        uut = formify.Choice(self.options, key_type=int, standalone=True)

        uut('3')
        self.assertEqual(3, uut.value)
        self.assertFalse(uut.is_valid())
        self.assertIn('Invalid option: 3', uut.errors)


class TestMultiChoice(unittest.TestCase):
    options = {
        1: 'One',
        2: 'Two',
        3: 'Thre'
    }

    def test_validInputData(self):
        uut = formify.MultiChoice(self.options, key_type=int, standalone=True)

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
        uut = formify.MultiChoice(self.options, key_type=int, standalone=True)

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


class TestEqualTo(unittest.TestCase):

    def setUp(self):
        self.uut = formify.Map({
            'a': formify.DateTime('%Y-%m-%d'),
            'b': formify.EqualTo('a')}, standalone=True)

    def test_doNotAllowStandaloneVersion(self):
        with self.assertRaises(TypeError):
            uut = formify.EqualTo('bar', standalone=True)

    def test_ifEqual_validationSucceeds(self):
        self.uut({'a': '2000-01-01', 'b': '2000-01-01'})

        self.assertIsInstance(self.uut['b'].validator, formify.DateTime)
        self.assertTrue(self.uut.is_valid())
        self.assertIs(self.uut['b'].python_type, self.uut['a'].python_type)
        self.assertEqual(self.uut['b'].value, self.uut['a'].value)

    def test_ifNotEqual_validationFails(self):
        self.uut({'a': '2000-01-01', 'b': '2000-02-02'})

        self.assertFalse(self.uut.is_valid())
        self.assertNotEqual(self.uut['b'].value, self.uut['a'].value)
        self.assertIn('Values are not equal', self.uut['b'].errors)


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

        class Schema(formify.Schema):
            a = formify.Integer()
            b = formify.String()

        self.Schema = Schema
        self.uut = formify.Map(self.Schema, standalone=True)

    def test_createFromEntity(self):
        uut = formify.Map(self.Schema, standalone=True)

        uut({'a': '1', 'b': 2})

        self.assertEqual({'a': 1, 'b': '2'}, uut.value)

    def test_createFromDict(self):
        uut = formify.Map({'a': formify.Integer, 'b': formify.String}, standalone=True)

        uut({'a': '1', 'b': 2})

        self.assertEqual({'a': 1, 'b': '2'}, uut.value)

    def test_ifAllInnerValidatorsAreValid_validatorIsValid(self):
        self.assertFalse(self.uut.is_valid())

        self.uut({'a': 1, 'b': 2})
        self.assertTrue(self.uut.is_valid())

        self.uut.value.a = 'abc'
        self.assertFalse(self.uut.is_valid())

        self.uut.value.a = '1'
        self.assertTrue(self.uut.is_valid())

    def test_ifContainsErrors_validationFails(self):
        uut = formify.Map({'a': formify.Integer(optional=True)}, standalone=True)
        self.assertTrue(uut.is_valid())

        uut('abc')
        self.assertEqual(1, len(uut.errors))
        self.assertFalse(uut.is_valid())

    def test_ifUnableToConvertToDict_processingFails(self):
        self.assertIs(self.uut(123), None)
        self.assertFalse(self.uut.is_valid())

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

    def test_ifStrictProcessingEnabled_extraKeysInInputDataWillCauseExceptionToBeRaised(self):
        with self.assertRaises(KeyError):
            self.uut({'a': 1, 'b': 2, 'c': 3})

    def test_ifStrictProcessingDisabled_extraKeysInInputDataAreIgnored(self):
        uut = formify.Map({'a': formify.Integer}, strict_processing=False, standalone=True)

        self.assertEqual({'a': 123}, uut({'a': '123'}))
        self.assertEqual({'a': 456}, uut({'a': '456', 'b': 1}))

    def test_processedValueIsNotTheSameObjectAsInputValue(self):
        data = {}
        self.assertIsNot(data, self.uut(data))

    def test_returnedValueCanBeUsedToInteractWithInnerValidators(self):
        value = self.uut({'a': '1', 'b': 2})

        self.assertEqual({'a': '1', 'b': 2}, self.uut.raw_value)
        self.assertEqual({'a': 1, 'b': '2'}, value)
        self.assertEqual(1, value.a)
        self.assertEqual('2', value['b'])

        value.a = '10'
        self.assertEqual(10, value.a)
        self.assertEqual(10, self.uut['a'].value)

        value['b'] = 3
        self.assertEqual('3', value.b)
        self.assertEqual('3', self.uut['b'].value)

        self.assertEqual({'a': 10, 'b': '3'}, dict(value))

    def test_defaultValue(self):
        self.assertEqual({'a': None, 'b': None}, self.uut.value)

    def test_processValueUsingNestedValidator(self):
        self.uut['a'](123)
        self.assertEqual({'a': 123, 'b': None}, self.uut.value)

        self.uut['b'](456)
        self.assertEqual({'a': 123, 'b': '456'}, self.uut.value)
