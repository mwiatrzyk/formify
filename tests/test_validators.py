import unittest

import formify


class TestValidator(unittest.TestCase):

    def setUp(self):

        class Entity(formify.Entity):
            pass

        class UUT(formify.Validator):
            messages = dict(formify.Validator.messages)
            messages.update({
                'conversion_error': 'Not a valid integer number',
                'required_error': 'This field is required',
            })
            python_type = int

        self.Entity = Entity
        self.UUT = UUT
        self.uut = UUT(owner=self.Entity())

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

    def setUp(self):

        class Entity(formify.Entity):
            pass

        self.entity = Entity()

    def test_conversion(self):
        uut = formify.String(owner=self.entity)

        uut(123)

        self.assertIsInstance(uut.value, unicode)
        self.assertEqual(u'123', uut.value)

    def test_minimalStringLengthConstraint(self):
        uut = formify.String(owner=self.entity, min_length=4)

        uut('spam')
        self.assertTrue(uut.is_valid())

        uut('foo')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting at least 4 characters', uut.errors[0])

    def test_maximalStringLengthConstraint(self):
        uut = formify.String(owner=self.entity, max_length=3)

        uut('foo')
        self.assertTrue(uut.is_valid())

        uut('spam')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting at most 3 characters', uut.errors[0])

    def test_lengthRange(self):
        uut = formify.String(owner=self.entity, min_length=3, max_length=4)

        uut('foo')
        self.assertTrue(uut.is_valid())

        uut('spam')
        self.assertTrue(uut.is_valid())

        uut('wonderful spam')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expected number of characters is between 3 and 4', uut.errors[0])


class TestNumeric(unittest.TestCase):

    def setUp(self):

        class Entity(formify.Entity):
            pass

        class UUT(formify.Numeric):
            python_type = int

        self.entity = Entity()
        self.UUT = UUT

    def test_conversion(self):
        uut = self.UUT(owner=self.entity)

        uut('123')

        self.assertIsInstance(uut.value, int)
        self.assertEqual(123, uut.value)

    def test_minimalValueConstraint(self):
        uut = self.UUT(owner=self.entity, min_value=4)

        uut('4')
        self.assertTrue(uut.is_valid())

        uut('3')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting value greater or equal to 4', uut.errors[0])

    def test_maximalValueConstraint(self):
        uut = self.UUT(owner=self.entity, max_value=5)

        uut('5')
        self.assertTrue(uut.is_valid())

        uut('6')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting value less or equal to 5', uut.errors[0])

    def test_valueRange(self):
        uut = self.UUT(owner=self.entity, min_value=4, max_value=6)

        uut('4')
        self.assertTrue(uut.is_valid())

        uut('5')
        self.assertTrue(uut.is_valid())

        uut('6')
        self.assertTrue(uut.is_valid())

        uut('3')
        self.assertFalse(uut.is_valid())
        self.assertEqual('Expecting value between 4 and 6', uut.errors[0])


class TestRegex(unittest.TestCase):

    def setUp(self):

        class Entity(formify.Entity):
            pass

        self.entity = Entity()
        self.uut = formify.Regex(r'^[0-9]+$', owner=Entity())

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

        class Entity(formify.Entity):
            pass

        self.Entity = Entity
        self.uut = formify.ListOf(formify.Integer(min_value=2, max_value=3), owner=Entity())

    def test_whenScalarGiven_itIsConvertedToSingleElementList(self):
        self.uut('123')

        self.assertEqual([123], self.uut.value)

    def test_whenListGiven_itIsProcessed(self):
        self.uut(['123'])

        self.assertEqual([123], self.uut.value)

    def test_whenConversionOfSomeElementsFails_theseElementsAreSetToNoneAndMapOfErrorsContainsThoseElements(self):
        self.uut(['1', 'a', '2', 'b'])

        self.assertEqual([1, None, 2, None], self.uut.value)
        self.assertEqual(2, len(self.uut.errors))
        self.assertIn(1, self.uut.errors)
        self.assertIn(3, self.uut.errors)

    def test_whenValidationOfSomeElementsFails_mapOfErrorsContainsThoseElements(self):
        self.uut([1, 2, 3, 4])

        self.assertFalse(self.uut.is_valid())
        self.assertEqual([1, 2, 3, 4], self.uut.value)
        self.assertEqual(2, len(self.uut.errors))
        self.assertIn(0, self.uut.errors)
        self.assertIn(3, self.uut.errors)

    def whenMinLengthSpecified_validationFailsIfNumberOfListItemsIsLessThanMinLength(self):
        uut = formify.ListOf(formify.Integer, min_length=2, owner=self.Entity())

        uut([1, 2])
        self.assertTrue(uut.is_valid())

        uut([1])
        self.assertFalse(uut.is_valid())
