import unittest

from rum.registry import DefaultDict


class DefaultDictTests(unittest.TestCase):

    def setUp(self):
        self._dict = DefaultDict(list)

    def test_lenEmptyDefaultDict_isZero(self):
        self.assertEqual(0, len(self._dict))

    def test_lenNonEmptyDefaultDict_isCorrect(self):
        self._dict[3] = 4
        self._dict[4] = 4
        self.assertEqual(2, len(self._dict))

    def test_addToExistentKey_properlyOverwrites(self):
        self._dict[3] = 4
        self._dict[3] = 5
        self._dict[4] = 1
        self.assertEqual(5, self._dict[3])

    def test_addToNonExistentKey_properlyOverwrites(self):
        self._dict[3] = 4
        self._dict[4] = 1
        self.assertEqual(4, self._dict[3])
        self.assertEqual(1, self._dict[4])

    def test_getNonexistentKey_returnsDefault(self):
        self.assertEqual([], self._dict['asdf'])

    def test_delNonexistentKey_noEntry(self):
        self._dict[3] = 4
        self._dict[4] = 1
        del self._dict[5]
        self.assertEqual(2, len(self._dict))
        self.assertEqual(4, self._dict[3])
        self.assertEqual(1, self._dict[4])

    def test_delExistentKey_noEntry(self):
        self._dict[3] = 4
        self._dict[4] = 1
        del self._dict[3]
        self.assertEqual(1, len(self._dict))
        self.assertEqual(1, self._dict[4])
        self.assertEqual([], self._dict[3])

    def test_iterateDefaultDict_iteratesAllKeys(self):
        self._dict[3] = 4
        self._dict[4] = 1
        self.assertEqual([3, 4], list(self._dict))

    def test_containsNonExistentKey_returnsFalse(self):
        self.assertEqual(False, 0 in self._dict)
        self.assertEqual(False, '' in self._dict)
        self.assertEqual(False, None in self._dict)

    def test_containsExistentKey_returnsTrue(self):
        self._dict[3] = 4
        self._dict[4] = 1
        self.assertEqual(True, 4 in self._dict)

    def test_clearAfterPopulate_clearsEntries(self):
        self._dict[3] = 4
        self._dict[4] = 1
        self._dict.clear()
        self.assertEqual(False, 4 in self._dict)
        self.assertEqual(False, 3 in self._dict)
        self.assertEqual(0, len(self._dict))



if __name__ == '__main__':
    unittest.main()
