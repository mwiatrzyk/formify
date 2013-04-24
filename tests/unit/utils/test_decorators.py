import unittest

from formify.utils import decorators


class TestSynchronized(unittest.TestCase):

    def setUp(self):

        class DummyLock(object):
            def __init__(self):
                self.nacq = 0
                self.nrel = 0

            def acquire(self):
                self.nacq += 1

            def release(self):
                self.nrel += 1


        self.lock = DummyLock()

    def test_lock_unlock(self):
        # Given
        @decorators.synchronized(lock=self.lock)
        def fun(a, b, c):
            return a + b + c
        # When
        result = fun(1, 2, 3)
        # Then
        self.assertEqual(self.lock.nacq, self.lock.nrel)
        self.assertEqual(result, 6)
