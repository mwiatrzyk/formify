import unittest

from formify.schema import Schema
from formify.undefined import Undefined
from formify.validators import Validator


# FAKE VALIDATORS

class FakeValidator(Validator):

    def process(self, value):
        self._value = value
        return value


class String(FakeValidator):
    pass


class Integer(FakeValidator):
    pass


class Bool(FakeValidator):
    pass


# TEST CASES

class TestSchemaMeta(unittest.TestCase):

    def setUp(self):

        class Test(Schema):
            _private_member = None
            not_a_validator = object()

            v1 = String()
            v2 = Integer()
            v3 = Bool(key='renamed_v3')
            v0 = String()
            v9 = Integer()
            v5 = Bool()

        self.Test = Test

    def test_Test_v1(self):
        # Given
        key = 'v1'
        type_ = String
        # When / Then
        self.assertIn(key, self.Test.__validators__)
        self.assertTrue(isinstance(self.Test.__validators__[key], type_))

    def test_Test_v2(self):
        # Given
        key = 'v2'
        type_ = Integer
        # When / Then
        self.assertIn(key, self.Test.__validators__)
        self.assertTrue(isinstance(self.Test.__validators__[key], type_))

    def test_Test_v3(self):
        # Given
        key = 'renamed_v3'
        type_ = Bool
        # When / Then
        self.assertIn(key, self.Test.__validators__)
        self.assertTrue(isinstance(self.Test.__validators__[key], type_))

    def test_Test_private_member(self):
        self.assertNotIn('_private_member', self.Test.__validators__)

    def test_Test_not_a_validator(self):
        self.assertNotIn('not_a_validator', self.Test.__validators__)

    def test_order(self):
        # Given
        expected = ['v1', 'v2', 'renamed_v3', 'v0', 'v9', 'v5']
        # When
        found = self.Test.__validators__.keys()
        # Then
        self.assertEqual(found, expected)


class TestSchemaInstance(unittest.TestCase):
    """Test case for :class:`formify.schema.Schema`."""

    def setUp(self):

        class Test(Schema):
            a = String(default='a')
            b_ = Integer(foo=1, bar=2, baz=3, key='b')
            c = Bool()

        self.Test = Test

    def test_constructor_without_args(self):
        # Given
        test = self.Test()
        # When / Then
        self.assertEqual(test.a, 'a')

    def test_constructor_with_args(self):
        # Given
        test = self.Test(b=1, c=True)
        # When / Then
        self.assertEqual(test.b, 1)
        self.assertEqual(test.c, True)

    def test_constructor_override_default(self):
        # Given
        test = self.Test(a='test')
        # When / Then
        self.assertEqual(test.a, 'test')
        self.assertEqual(test['a'].default, 'a')

    def test_setattr_private(self):
        # Given
        test = self.Test()
        # When
        test._foo = True
        # Then
        self.assertEqual(test._foo, True)

    def test_setattr_public_validator(self):
        # Given
        test = self.Test()
        # When
        test.b = 123
        # Then
        self.assertEqual(test.b, 123)

    def test_setattr_public_non_validator(self):
        # Given
        test = self.Test()
        # When
        def assign():
            test.foo = 'foo'
        # Then
        self.assertRaises(AttributeError, assign)

    def test_getattribute_set_by_default(self):
        # Given
        test = self.Test()
        # When / Then
        self.assertEqual(test.a, 'a')

    def test_getattribute_not_set(self):
        # Given
        test = self.Test()
        # When / Then
        self.assertIs(test.b, Undefined)

    def test_getattribute_private(self):
        # Given
        test = self.Test()
        test._private = 'test'
        # When / Then
        self.assertEqual(test._private, 'test')

    def test_getattribute_delattr_validator(self):
        """Deleting bound attribute is equal to initializing it with
        ``Undefined`` value."""
        # Given
        test = self.Test(a='a')
        # When
        del test.a
        # Then
        self.assertEqual(test.a, Undefined)

    def test_getattribute_deleted_validator(self):
        """Deleting bound attribute object (via ``__delitem__``) removes it
        completely from current schema object (not class!), so access will
        cause exception."""
        # Given
        test = self.Test()
        # When
        del test['a']
        def getter():
            return test.a
        # Then
        self.assertRaises(AttributeError, getter)

    def test_delattr_validator(self):
        # Given
        test = self.Test(a='test', b=123, c=False)
        # When
        del test.a
        del test.c
        # Then
        self.assertIs(test.a, Undefined)
        self.assertIs(test.c, Undefined)
        self.assertEqual(test.b, 123)

    def test_delattr_not_validator(self):
        # Given
        test = self.Test()
        test._foo = True
        # When
        del test._foo
        # Then
        self.assertFalse(hasattr(test, '_foo'))

    def test_getitem_valid(self):
        # Given
        test = self.Test()
        # When / Then
        self.assertTrue(isinstance(test['a'], String))
        self.assertTrue(isinstance(test['b'], Integer))
        self.assertTrue(isinstance(test['c'], Bool))

    def test_getitem_invalid(self):
        # Given
        test = self.Test()
        # When
        def getter():
            return test['bar']
        # Then
        self.assertRaises(KeyError, getter)

    def test_delitem_valid(self):
        # Given
        test = self.Test()
        # When
        del test['a']
        # Then
        self.assertNotIn('a', test)
        self.assertIn('b', test)
        self.assertIn('c', test)

    def test_delitem_invalid(self):
        # Given
        test = self.Test()
        # When
        def deleter():
            del test['spam']
        # Then
        self.assertRaises(KeyError, deleter)

    def test_delitem_and_setattr_of_deleted_item(self):
        # Given
        test = self.Test(b=123)
        # When
        del test['b']
        test.b = 124
        # Then
        self.assertEqual(test.b, 124)

    def test_iter(self):
        # Given
        test = self.Test()
        # When
        keys = list(test)
        # Then
        self.assertEqual(keys, ['a', 'b', 'c'])

    def test_iter_delattr(self):
        # Given
        test = self.Test()
        # When
        del test.a
        keys = list(test)
        # Then
        self.assertEqual(keys, ['a', 'b', 'c'])

    def test_iter_delitem(self):
        # Given
        test = self.Test()
        # When
        del test['b']
        keys = list(test)
        # Then
        self.assertEqual(keys, ['a', 'c'])

    def test_bound_vs_unbound(self):
        # Given
        test = self.Test()
        # When / Then
        self.assertFalse(self.Test.a is test['a'])

    def test_errors(self):
        # Given
        test = self.Test()
        test['a'].errors.append('error1')
        test['b'].errors.append('error2')
        # When
        errors = test.errors
        # Then
        self.assertIn('error1', errors['a'])
        self.assertIn('error2', errors['b'])
        self.assertNotIn('c', errors)

    def test_is_valid_true(self):
        # Given
        test = self.Test()
        # When
        test.a = 'foo'
        test.b = 123
        test.c = True
        # Then
        self.assertTrue(test.is_valid())

    def test_is_valid_false(self):
        # Given
        test = self.Test()
        # When
        status = test.is_valid()
        # Then
        self.assertFalse(status)
        self.assertIn('this field is required', test['b'].errors)
        self.assertIn('this field is required', test['c'].errors)
