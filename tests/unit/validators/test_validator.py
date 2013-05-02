import random
import unittest

from formify import exc
from formify.undefined import Undefined
from formify.validators import Validator


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
