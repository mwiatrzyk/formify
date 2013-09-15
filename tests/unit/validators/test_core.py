import decimal
import unittest

from formify import exc
from formify.schema import Schema
from formify.validators import (
    String, Regex, Numeric, Integer, Float, Decimal, Boolean)


class TestString(unittest.TestCase):

    def setUp(self):
        self.validator = String()

    def test_ok(self):
        # When
        value = self.validator.process('123')
        # Then
        self.assertEqual(value, u'123')

    def test_ok_acceptable(self):
        # When
        value = self.validator.process(u'abc')
        # Then
        self.assertEqual(value, u'abc')

    def test_nok_non_string_input(self):
        # When
        def process():
            self.validator.process(None)
        # Then
        self.assertRaises(TypeError, process)

    def test_lmin_and_lmax(self):
        # Given
        validator = String(10, 5)
        # When
        def process_less():
            validator.process('foo')
        def process_greater():
            validator.process('foo bar baz spam')
        # Then
        self.assertRaises(exc.ValidationError, process_less)
        self.assertRaises(exc.ValidationError, process_greater)

    def test_lmin(self):
        # Given
        validator = String(length_min=2)
        # When
        def process():
            validator.process('1')
        # Then
        self.assertRaises(exc.ValidationError, process)

    def test_lmax(self):
        # Given
        validator = String(5)
        # When
        def process():
            validator.process('foobar')
        # Then
        self.assertRaises(exc.ValidationError, process)


class TestRegex(unittest.TestCase):

    def setUp(self):
        self.validator = Regex('[A-Z]{3}')

    def test_match(self):
        # When
        value = self.validator.process('ABC')
        # Then
        self.assertEqual(value, u'ABC')

    def test_not_match(self):
        # When
        def process():
            self.validator.process('abc')
        # Then
        self.assertRaises(exc.ValidationError, process)


class TestNumeric(unittest.TestCase):

    def setUp(self):
        class DummyInt(Numeric):
            python_type = int
        self.DummyInt = DummyInt

    def test(self):
        # Given
        validator = self.DummyInt()
        # When
        value = validator.process('123')
        # Then
        self.assertEqual(value, 123)

    def test_vmin_vmax(self):
        # Given
        validator = self.DummyInt(0, 10)
        # When
        def process_less():
            validator.process('-1')
        def process_greater():
            validator.process('11')
        # Then
        self.assertRaises(exc.ValidationError, process_less)
        self.assertRaises(exc.ValidationError, process_greater)

    def test_vmin(self):
        # Given
        validator = self.DummyInt(0)
        # When
        def process():
            validator.process('-1')
        # Then
        self.assertRaises(exc.ValidationError, process)

    def test_vmax(self):
        # Given
        validator = self.DummyInt(value_max=10)
        # When
        def process():
            validator.process('11')
        # Then
        self.assertRaises(exc.ValidationError, process)


class TestInteger(unittest.TestCase):

    def setUp(self):
        self.validator = Integer()

    def test_ok(self):
        # When
        value = self.validator.process('-123')
        # Then
        self.assertEqual(value, -123)

    def test_ok_acceptable(self):
        # When
        value = self.validator.process(-123)
        # Then
        self.assertEqual(value, -123)

    def test_nok(self):
        # When
        def process():
            self.validator.process('abc')
        # Then
        self.assertRaises(exc.ConversionError, process)

    def test_nok_non_string_input(self):
        # When
        def process():
            self.validator.process(123.5)
        # Then
        self.assertRaises(TypeError, process)


class TestFloat(unittest.TestCase):

    def setUp(self):
        self.validator = Float()

    def test_ok(self):
        # When
        value = self.validator.process('3.14')
        # Then
        self.assertEqual(value, 3.14)

    def test_ok_acceptable(self):
        # When
        value = self.validator.process(3.14)
        # Then
        self.assertEqual(value, 3.14)

    def test_nok(self):
        # When
        def process():
            self.validator.process('abc')
        # Then
        self.assertRaises(exc.ConversionError, process)

    def test_nok_non_string_input(self):
        # When
        def process():
            self.validator.process(3)
        # Then
        self.assertRaises(TypeError, process)


class TestDecimal(unittest.TestCase):

    def setUp(self):
        self.validator = Decimal()

    def test_ok(self):
        # Given
        n = decimal.Decimal('3.14')
        # When
        value = self.validator.process('3.14')
        # Then
        self.assertEqual(value, n)

    def test_ok_acceptable(self):
        # Given
        n = decimal.Decimal('3.14')
        # When
        value = self.validator.process(n)
        # Then
        self.assertEqual(value, n)

    def test_nok(self):
        # When
        def process():
            self.validator.process('abc')
        # Then
        self.assertRaises(exc.ConversionError, process)

    def test_nok_non_string_input(self):
        # When
        def process():
            self.validator.process(3)
        # Then
        self.assertRaises(TypeError, process)


class TestBool(unittest.TestCase):

    def setUp(self):
        self.validator = Boolean()

    def test_ok_true(self):
        # When
        value = self.validator.process('true')
        # Then
        self.assertTrue(value)

    def test_ok_false(self):
        # When
        value = self.validator.process('off')
        # Then
        self.assertFalse(value)

    def test_ok_acceptable(self):
        # When
        value = self.validator.process(False)
        # Then
        self.assertFalse(value)

    def test_nok(self):
        # When
        def process():
            self.validator.process('abc')
        # Then
        self.assertRaises(exc.ConversionError, process)

    def test_nok_empty_string(self):
        # When
        def processor():
            self.validator.process('')
        # Then
        self.assertRaises(exc.ConversionError, processor)

    def test_nok_non_string_input(self):
        # When
        def process():
            self.validator.process(3)
        # Then
        self.assertRaises(TypeError, process)

    def test_custom_trues_falses(self):
        # Given
        validator = Boolean(trues=['1'], falses=['0'])
        # When / Then
        self.assertTrue(validator.process('1'))
        self.assertFalse(validator.process('0'))
        self.assertRaises(exc.ConversionError, lambda: validator.process('true'))
        self.assertRaises(exc.ConversionError, lambda: validator.process('false'))
