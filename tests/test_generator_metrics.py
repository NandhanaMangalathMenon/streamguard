
import unittest

from streamguard.traffic_generator import generate_traffic
from streamguard.exact_counter import count_items, get_top_k
from streamguard.metrics import (
    absolute_error,
    relative_error,
    mean_absolute_error,
    top_k_precision,
    measure_throughput,
    estimate_sketch_memory
)


class TestTrafficGenerator(unittest.TestCase):

    def test_packet_count(self):
        traffic = generate_traffic(num_packets=100)
        self.assertEqual(len(traffic), 100)

    def test_reproducible_traffic(self):
        first = generate_traffic(num_packets=100, seed=10)
        second = generate_traffic(num_packets=100, seed=10)
        self.assertEqual(first, second)

    def test_number_of_distinct_sources(self):
        traffic = generate_traffic(
            num_packets=100,
            num_sources=10,
            heavy_hitter_count=2
        )
        self.assertLessEqual(len(set(traffic)), 10)

    def test_invalid_source_count(self):
        with self.assertRaises(ValueError):
            generate_traffic(num_sources=0)

    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            generate_traffic(heavy_hitter_probability=1.5)


class TestExactCounter(unittest.TestCase):

    def test_exact_frequency(self):
        counts = count_items(["A", "B", "A", "C", "A"])
        self.assertEqual(counts["A"], 3)
        self.assertEqual(counts["B"], 1)
        self.assertEqual(counts["C"], 1)

    def test_top_k(self):
        counts = count_items(["A", "B", "A", "C", "A", "B"])
        self.assertEqual(get_top_k(counts, 2), [("A", 3), ("B", 2)])

    def test_negative_k(self):
        with self.assertRaises(ValueError):
            get_top_k(count_items(["A"]), -1)


class TestMetrics(unittest.TestCase):

    def test_absolute_error(self):
        self.assertEqual(absolute_error(10, 13), 3)

    def test_relative_error(self):
        self.assertAlmostEqual(relative_error(10, 12), 0.2)

    def test_zero_frequency_error(self):
        self.assertEqual(relative_error(0, 0), 0.0)

    def test_mean_absolute_error(self):
        exact = {"A": 10, "B": 5}
        estimated = {"A": 12, "B": 4}
        self.assertEqual(mean_absolute_error(exact, estimated), 1.5)

    def test_top_k_precision(self):
        exact = {"A": 10, "B": 8, "C": 2}
        estimated = {"A": 9, "B": 7, "C": 3}
        self.assertEqual(top_k_precision(exact, estimated, 2), 1.0)

    def test_throughput(self):
        self.assertEqual(measure_throughput(100, 2), 50)

    def test_sketch_memory(self):
        self.assertEqual(estimate_sketch_memory(100, 5), 4000)

    def test_invalid_sketch_dimensions(self):
        with self.assertRaises(ValueError):
            estimate_sketch_memory(0, 5)


if __name__ == "__main__":
    unittest.main()
