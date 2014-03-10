# tests/test_schema.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import random
import unittest

import formify

from formify.decorators import preprocessor


class TestSchema(unittest.TestCase):

    def setUp(self):

        class UUT(formify.Schema):
            a = formify.String()
            b = formify.Integer()
            _c = formify.Integer(key='c')

        self.UUT = UUT
        self.uut = UUT()

    def test_create(self):
        uut = self.UUT(a='spam', b=1)

        self.assertEqual('spam', uut.a)
        self.assertEqual(1, uut.b)

    def test_accessUnboundValidatorsViaSpecialProperty(self):
        self.assertIs(self.UUT.__validators__['a'], self.UUT.a)
        self.assertIs(self.UUT.__validators__['b'], self.UUT.b)
        self.assertIs(self.UUT.__validators__['c'], self.UUT._c)

    def test_yieldsValidatorKeysInOrderOfCreation_onceIterated(self):
        self.assertEqual(['a', 'b', 'c'], list(self.uut))

    def test_allowSettingPrivatePropertiesAsIs(self):
        value = {}
        self.uut._foo = value
        self.assertIs(value, self.uut._foo)

    def test_whenSettingPublicPropertyDefinedInClass_invokeValidator(self):
        self.uut.a = 'spam'

        self.assertEqual('spam', self.uut.a)
        self.assertEqual('spam', self.uut['a'].raw_value)
        self.assertEqual('spam', self.uut['a'].value)

    def test_whenSettingPublicPropertyNotDefinedInClass_raiseException(self):
        with self.assertRaises(AttributeError):
            self.uut.foo = 1

    def test_whenGettingPublicPropertyDefinedInClassWithNoValueSet_returnNone(self):
        self.assertIs(self.uut.a, None)
        self.assertIs(self.uut.b, None)

    def test_whenGettingPublicPropertyWithNoValidatorSpecified_raiseException(self):
        with self.assertRaises(AttributeError):
            foo = self.uut.foo

    def test_ifExplicitKeyDefinedForValidator_itShouldOnlyBeAccessibleViaThatKey(self):
        with self.assertRaises(AttributeError):
            c = self.uut._c
        self.uut.c = 1
        self.assertEqual(1, self.uut.c)

    def test_whenDefaultValueSpecified_gettingThatPropertyReturnsItsDefaultValue(self):

        class UUT(formify.Schema):
            a = formify.Integer(default=123)

        uut = UUT()

        self.assertEqual(123, uut.a)

    def test_whenCallableGivenAsDefaultValue_itsReturnValueIsUsedAsDefault(self):

        class UUT(formify.Schema):
            a = formify.Integer(default=lambda: 123)

        uut = UUT()

        self.assertEqual(123, uut.a)

    def test_whenCallableGivenAsDefaultValue_itIsEvaluatedForEveryInstance(self):

        class UUT(formify.Schema):
            a = formify.Integer(default=lambda: random.random() * 100)

        uut1 = UUT()
        uut2 = UUT()

        self.assertNotEqual(uut1.a, uut2.a)

    def test_eachEntityHasItsOwnValidatorInstances(self):
        a = self.UUT()
        b = self.UUT()

        self.assertIsNot(a['a'], b['a'])

    def test_whenValidationFails_mapOfErrorsIsFilled(self):
        self.uut.b = '456'
        self.uut.c = 'abc'

        self.assertFalse(self.uut.is_valid())
        self.assertIn('a', self.uut.errors)  # required missing
        self.assertIn('c', self.uut.errors)  # conversion error

    def test_whenPreprocessorDefined_itIsInvokedOnceValueIsAssigned(self):

        class UUT(formify.Schema):
            a = formify.Integer()

            @preprocessor('a')
            def check_numeric(self, validator, value):
                if value.isdigit():
                    return value
                else:
                    return -1

        uut = UUT()

        uut.a = '123'
        self.assertEqual(123, uut.a)

        uut.a = 'abc'
        self.assertEqual(-1, uut.a)
