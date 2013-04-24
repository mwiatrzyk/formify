import copy
import unittest

from formify.undefined import Undefined


class TestUndefined(unittest.TestCase):

    def test_repr(self):
        self.assertIs(repr(Undefined), 'Undefined')

    def test_unicode(self):
        self.assertIs(unicode(Undefined), u'')

    def test_nonzero(self):
        self.assertFalse(Undefined)

    def test_copy(self):
        # When
        tmp = copy.copy(Undefined)
        # Then
        self.assertIs(tmp, Undefined)

    def test_deepcopy(self):
        # When
        tmp = copy.deepcopy(Undefined)
        # Then
        self.assertIs(tmp, Undefined)
