import random
import decimal
import unittest

from formify import exc
from formify.undefined import Undefined
from formify.validators import *


class TestValidator(unittest.TestCase):

    def test_creation_order(self):
        # Given
        validators = [
            Validator(),
            Validator(),
            Validator(),
        ]
        # When
        random.shuffle(validators)
        validators.sort(key=lambda x: x._creation_order)
        # Then
        self.assertTrue(validators[0]._creation_order < validators[1]._creation_order)
        self.assertTrue(validators[1]._creation_order < validators[2]._creation_order)

    def test_is_bound_false(self):
        # Given
        test = Validator()
        # When / Then
        self.assertFalse(test.is_bound())

    def test_is_bound_true(self):
        # Given
        test = Validator()
        # When
        test._schema = object
        # Then
        self.assertTrue(test.is_bound())

    def test_bind(self):
        # Given
        class Schema(object):
            _bound_validators = {}
        schema = Schema()
        test = Validator(foo='foo', key='test')
        test.bar = 123
        test.default = True
        # When
        bound = test.bind(schema)
        # Then
        self.assertIn('test', schema._bound_validators)
        self.assertIs(bound.schema, schema)
        self.assertTrue(bound.is_bound())
        self.assertEqual(bound.key, 'test')
        self.assertEqual(bound.foo, 'foo')
        self.assertEqual(bound.bar, 123)
        self.assertEqual(bound.default, True)

    def test_bind_twice(self):
        # Given
        class Schema(object):
            _bound_validators = {}
        schema = Schema()
        test = Validator(key='test')
        # When
        def binder():
            test.bind(schema).bind(schema)
        # Then
        self.assertRaises(exc.AlreadyBound, binder)

    def test_unbind(self):
        # Given
        class Schema(object):
            _bound_validators = {}
        schema = Schema()
        test = Validator(key='test')
        # When
        bound = test.bind(schema)
        bound.unbind()
        # Then
        self.assertFalse(bound.is_bound())

    def test_unbind_unbound(self):
        # Given
        test = Validator()
        # When
        def unbinder():
            test.unbind()
        # Then
        self.assertRaises(exc.NotBound, unbinder)

    def test_process(self):
        # Given
        test = Validator()
        # When
        def processor():
            test.process('test value')
        # Then
        self.assertRaises(NotImplementedError, processor)

    def test_process_with_python_type_from_string(self):
        # Given
        class Int(Validator):
            python_type = int
        test = Int()
        # When
        value = test.process('123')
        # Then
        self.assertIs(value, 123)

    def test_process_with_python_type_valid_type(self):
        # Given
        class Int(Validator):
            python_type = int
        test = Int()
        # When
        value = test.process(123)
        # Then
        self.assertIs(value, 123)

    def test_process_with_python_type_invalid_type(self):
        # Given
        class Int(Validator):
            python_type = int
        test = Int()
        # When
        def processor():
            value = test.process(123.5)
        # Then
        self.assertRaises(TypeError, processor)

    def test_process_with_python_type_conversion_error(self):
        # Given
        class Int(Validator):
            python_type = int
        test = Int()
        # When
        def processor():
            value = test.process('foo')
        # Then
        self.assertRaises(exc.ConversionError, processor)

    def test_process_with_python_type_bound(self):
        # Given
        class Schema(object):
            _bound_validators = {}
        class Int(Validator):
            python_type = int
        test = Int()
        schema = Schema()
        bound = test.bind(schema)
        # When
        value = bound.process(u'123')
        # Then
        self.assertIs(bound.raw_value, u'123')
        self.assertIs(bound.value, 123)
        self.assertEqual(bound.value, value)

    def test_default_value_and_raw_value(self):
        # Gven
        test = Validator()
        # When / Then
        self.assertIs(test.value, Undefined)
        self.assertIs(test.raw_value, Undefined)

    def test_default_default(self):
        # Given
        test = Validator()
        # When / Then
        self.assertIs(test.default, Undefined)

    def test_label_None(self):
        # Given
        test = Validator(key='foo_bar_baz')
        # When
        test.label = None
        # Then
        self.assertEqual(test.label, 'Foo bar baz')

    def test_label_Undefined(self):
        # Given
        test = Validator()
        # When
        test.label = Undefined
        # Then
        self.assertIs(test.label, Undefined)

    def test_label_str(self):
        # Given
        test = Validator()
        # When
        test.label = 'foo bar baz'
        # Then
        self.assertTrue(isinstance(test.label, unicode))
        self.assertEqual(test.label, u'foo bar baz')

    def test_is_valid_unbound(self):
        # Given / When
        test = Validator()
        # Then
        self.assertTrue(test.is_valid())

    def test_is_valid_false(self):
        # Given
        test = Validator()
        # When
        test._schema = object
        test._value = 'a value'
        test.errors.append('an error')
        # Then
        self.assertFalse(test.is_valid())

    def test_prevalidation_error_in_bound_validator(self):
        # Given
        class Test(Validator):
            python_type = unicode

            def prevalidate(self, value):
                raise ValueError("an error: %s" % value)

        test = Test()
        test._schema = object
        # When
        result = test.process('123')
        # Then
        self.assertIs(result, Undefined)
        self.assertIn('an error: 123', test.errors)


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

    def test_ok_empty_string(self):
        # When
        value = self.validator.process('')
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
