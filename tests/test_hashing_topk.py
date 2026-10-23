
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
class FakeSketch:
    """Simple sketch substitute for testing TopK independently."""

    def __init__(self):
        self.counts = {}

    def update(self, item, count=1):
        self.counts[item] = self.counts.get(item, 0) + count

    def estimate(self, item):
        return self.counts.get(item, 0)


class TestTopK(unittest.TestCase):

    def setUp(self):
        self.sketch = FakeSketch()
        self.topk = TopK(self.sketch, k=2)

    def test_add_updates_sketch(self):
        self.topk.add("apple")
        self.assertEqual(self.sketch.estimate("apple"), 1)

    def test_repeated_items_increase_count(self):
        self.topk.add("apple")
        self.topk.add("apple")
        self.topk.add("apple")
        self.assertEqual(self.sketch.estimate("apple"), 3)

    def test_returns_top_k_items(self):
        self.topk.add("apple", 5)
        self.topk.add("banana", 3)
        self.topk.add("orange", 1)

        result = self.topk.get_top_k()

        self.assertEqual(
            result,
            [("apple", 5), ("banana", 3)]
        )

    def test_custom_k(self):
        self.topk.add("apple", 5)
        self.topk.add("banana", 3)
        self.topk.add("orange", 1)

        result = self.topk.get_top_k(1)

        self.assertEqual(result, [("apple", 5)])

    def test_zero_count_does_not_add_candidate(self):
        self.topk.add("apple", 0)

        self.assertEqual(self.topk.get_top_k(), [])

    def test_negative_count_raises_error(self):
        with self.assertRaises(ValueError):
            self.topk.add("apple", -1)

    def test_invalid_k_raises_error(self):
        with self.assertRaises(ValueError):
            self.topk.get_top_k(0)

if __name__ == "__main__":
    unittest.main()
