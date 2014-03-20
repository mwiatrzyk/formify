# tests/test_types.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

import unittest

from formify import types


class TestDictMixin(unittest.TestCase):

    def setUp(self):

        class UUT(types.DictMixin):

            def __init__(self, data=None):
                self._storage = data or {}

            def __iter__(self):
                for k in self._storage:
                    yield k

            def __contains__(self, key):
                return key in self._storage

            def __setitem__(self, key, value):
                self._storage[key] = value

            def __getitem__(self, key):
                return self._storage[key]

            def __delitem__(self, key):
                del self._storage[key]

        self.UUT = UUT
        self.uut = UUT({1: 'one', 2: 'two', 3: 'three'})

    def test_itemSettingGettingAndDeleting(self):
        uut = self.UUT()

        uut[1] = 'one'
        self.assertEqual('one', uut[1])

        uut['two'] = 2
        self.assertEqual(2, uut['two'])

        del uut['two']
        with self.assertRaises(KeyError):
            a = uut['two']

    def test_keys(self):
        uut = self.UUT()

        uut[1] = 'one'
        uut[2] = 'two'
        uut[3] = 'three'

        self.assertEqual([1, 2, 3], sorted(uut.keys()))

    def test_hasKey(self):
        self.assertTrue(self.uut.has_key(1))
        self.assertFalse(self.uut.has_key(4))

    def test_contains(self):
        self.assertTrue(1 in self.uut)
        self.assertFalse(4 in self.uut)

    def test_iter(self):
        self.assertEqual([1, 2, 3], sorted(self.uut))

    def test_repr(self):
        self.assertEqual("{1: 'one', 2: 'two', 3: 'three'}", repr(self.uut))

    def test_compare(self):
        self.assertEqual({1: 'one', 2: 'two', 3: 'three'}, self.uut)
        self.assertNotEqual({}, self.uut)
        self.assertEqual(self.uut, self.uut)
        self.assertNotEqual(None, self.uut)
        self.assertNotEqual(object(), self.uut)

    def test_len(self):
        uut = self.UUT()
        self.assertEqual(0, len(uut))

        uut[1] = 'one'
        self.assertEqual(1, len(uut))

        uut[2] = 'two'
        self.assertEqual(2, len(uut))

        del uut[1]
        self.assertEqual(1, len(uut))

        del uut[2]
        self.assertEqual(0, len(uut))

    def test_iterkeys(self):
        self.assertEqual([1, 2, 3], sorted(self.uut.iterkeys()))

    def test_itervaluesAndValues(self):
        self.assertEqual(['one', 'two', 'three'], list(self.uut.itervalues()))
        self.assertEqual(['one', 'two', 'three'], self.uut.values())

    def test_iteritemsAndItems(self):
        self.assertEqual([(1, 'one'), (2, 'two'), (3, 'three')], list(self.uut.iteritems()))
        self.assertEqual([(1, 'one'), (2, 'two'), (3, 'three')], self.uut.items())

    def test_clear(self):
        self.assertEqual(3, len(self.uut))
        self.uut.clear()
        self.assertEqual(0, len(self.uut))

    def test_setdefault(self):
        self.assertEqual('one', self.uut.setdefault(1, 'two'))
        self.assertEqual(None, self.uut.setdefault(4))
        self.assertEqual('five', self.uut.setdefault(5, 'five'))
        self.assertEqual(None, self.uut[4])
        self.assertEqual('five', self.uut[5])

    def test_pop(self):
        self.assertEqual('one', self.uut.pop(1))
        self.assertEqual('five', self.uut.pop(5, 'five'))
        with self.assertRaises(TypeError):
            self.uut.pop(1, 2, 3)
        with self.assertRaises(KeyError):
            self.uut.pop(5)

    def test_popitem(self):
        uut = self.UUT({1: 'one'})

        self.assertEqual((1, 'one'), uut.popitem())
        with self.assertRaises(KeyError):
            uut.popitem()

    def test_update(self):
        uut = self.UUT()

        uut.update({1: 'one'})
        self.assertEqual({1: 'one'}, uut)

        uut.update([(2, 'two')])
        self.assertEqual({1: 'one', 2: 'two'}, uut)

        uut.update({3: 'three'}, foo='bar')
        self.assertEqual({1: 'one', 2: 'two', 3: 'three', 'foo': 'bar'}, uut)

    def test_get(self):
        self.assertEqual('one', self.uut.get(1))
        self.assertEqual('two', self.uut.get(2))
        self.assertEqual(None, self.uut.get(4))
        self.assertEqual('five', self.uut.get(5, 'five'))

    def test_convertToDict(self):
        self.assertEqual({1: 'one', 2: 'two', 3: 'three'}, dict(self.uut))
