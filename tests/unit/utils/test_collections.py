import unittest

from formify.utils import collections


class TestOrderedDict(unittest.TestCase):

    def setUp(self):
        self.d = collections.OrderedDict([(1, 'one'), (2, 'two'), (3, 'three')])

    def test_init(self):
        # Given
        d = collections.OrderedDict()
        # When / Then
        self.assertEqual(len(d), 0)

    def test_init_iterable(self):
        # Given
        d = collections.OrderedDict([(1, 'one'), (2, 'two')])
        # When / Then
        self.assertEqual(len(d), 2)
        self.assertEqual(d[1], 'one')
        self.assertEqual(d[2], 'two')

    def test_setitem(self):
        # When
        self.d[4] = 'four'
        # Then
        self.assertIn(4, self.d._storage)
        self.assertIn(4, self.d._order)

    def test_getitem(self):
        # When / Then
        self.assertEqual(self.d[1], 'one')
        self.assertRaises(KeyError, lambda: self.d['one'])

    def test_delitem_invalid(self):
        # Given
        def remove():
            del self.d['fake']
        # When / Then
        self.assertRaises(KeyError, remove)

    def test_delitem_valid(self):
        # When
        del self.d[1]
        # Then
        self.assertNotIn(1, self.d._storage)
        self.assertNotIn(1, self.d._order)

    def test_contains(self):
        # When / Then
        self.assertIn(1, self.d)
        self.assertNotIn('one', self.d)

    def test_repr(self):
        # When
        r = repr(self.d)
        # Then
        self.assertEqual(r, "{1: 'one', 2: 'two', 3: 'three'}")

    def test_clear(self):
        # When
        self.d.clear()
        # Then
        self.assertEqual(self.d._storage, {})
        self.assertEqual(self.d._order, [])

    def test_copy(self):
        # When
        c = self.d.copy()
        # Then
        self.assertIsNot(c, self.d)
        self.assertIsNot(c._storage, self.d._storage)
        self.assertIsNot(c._order, self.d._order)

    def test_iterkeys(self):
        # When
        r = list(self.d.iterkeys())
        # Then
        self.assertEqual(r, [1, 2, 3])

    def test_itervalues(self):
        # When
        r = list(self.d.itervalues())
        # Then
        self.assertEqual(r, ['one', 'two', 'three'])

    def test_iteritems(self):
        # When
        r = list(self.d.iteritems())
        # Then
        self.assertEqual(r, [(1, 'one'), (2, 'two'), (3, 'three')])

    def test_keys(self):
        # When
        r = self.d.keys()
        # Then
        self.assertEqual(r, [1, 2, 3])

    def test_values(self):
        # When
        r = self.d.values()
        # Then
        self.assertEqual(r, ['one', 'two', 'three'])

    def test_iteritems(self):
        # When
        r = self.d.items()
        # Then
        self.assertEqual(r, [(1, 'one'), (2, 'two'), (3, 'three')])

    def test_get_valid(self):
        # When
        r = self.d.get(1)
        # Then
        self.assertEqual(r, 'one')

    def test_get_invalid(self):
        # When
        r = self.d.get('fake', 'fake')
        # Then
        self.assertEqual(r, 'fake')

    def test_pop_invalid_number_of_args(self):
        # When / Then
        self.assertRaises(TypeError, lambda: self.d.pop(1, 2, 3))
        self.assertRaises(TypeError, lambda: self.d.pop())

    def test_pop_valid(self):
        # When
        r = self.d.pop(2)
        # Then
        self.assertEqual(r, 'two')

    def test_pop_invalid_with_default(self):
        # When
        r = self.d.pop('fake', 'missing')
        # Then
        self.assertEqual(r, 'missing')

    def test_pop_invalid(self):
        # When / Then
        self.assertRaises(KeyError, lambda: self.d.pop('fake'))

    def test_popitem_empty_dict(self):
        # Given
        self.d.clear()
        # When / Then
        self.assertRaises(KeyError, lambda: self.d.popitem())

    def test_popitem(self):
        # When
        item = self.d.popitem()
        # Then
        self.assertEqual(item, (3, 'three'))

    def test_setdefault(self):
        # When
        r = self.d.setdefault(4, 'four')
        # Then
        self.assertEqual(r, 'four')

    def test_update(self):
        # When
        self.d.update([(5, 'five')])
        # Then
        self.assertIn(5, self.d)
