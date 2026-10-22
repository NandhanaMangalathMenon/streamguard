
import unittest

from streamguard.hashing import hash_item, hash_index


class TestHashing(unittest.TestCase):

    def test_same_item_same_hash(self):
        self.assertEqual(
            hash_item("apple"),
            hash_item("apple")
        )

    def test_different_seeds(self):
        self.assertNotEqual(
            hash_item("apple", seed=1),
            hash_item("apple", seed=2)
        )

    def test_hash_index_in_range(self):
        width = 100
        index = hash_index("apple", width)
        self.assertGreaterEqual(index, 0)
        self.assertLess(index, width)

    def test_invalid_width(self):
        with self.assertRaises(ValueError):
            hash_index("apple", 0)

    def test_invalid_item_type(self):
        with self.assertRaises(TypeError):
            hash_item(123)


if __name__ == "__main__":
    unittest.main()
