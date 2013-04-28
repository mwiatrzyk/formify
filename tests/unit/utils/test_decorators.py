import unittest

from formify.utils import decorators


class TestMemoizedProperty(unittest.TestCase):

    def setUp(self):

        class Test(object):

            @decorators.memoized_property
            def memoized(self):
                return [1, 2, 3]

        self.Test = Test

    def test_class_access(self):
        # When
        p = self.Test.memoized
        # Then
        self.assertTrue(isinstance(p, decorators.memoized_property))

    def test_instance_access(self):
        # Given
        test = self.Test()
        # When
        p1 = test.memoized
        p2 = test.memoized
        # Then
        self.assertEqual(p1, [1, 2, 3])
        self.assertIs(p1, p2)
