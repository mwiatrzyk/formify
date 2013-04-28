import unittest

from formify.utils import helpers


class TestMaybeCallable(unittest.TestCase):

    def test_callable(self):
        # When
        result = helpers.maybe_callable(lambda: 'test')
        # Then
        self.assertEqual(result, 'test')

    def test_no_callable(self):
        # When
        result = helpers.maybe_callable('test')
        # Then
        self.assertEqual(result, 'test')
