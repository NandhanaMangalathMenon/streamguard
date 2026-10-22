
import sys
from time import perf_counter


def absolute_error(exact, estimated):
    # Calculate the absolute difference between two counts.
    return abs(exact - estimated)


def relative_error(exact, estimated):
    # Avoid division by zero when the true count is zero.
    if exact == 0:
        return 0.0 if estimated == 0 else float("inf")

    return abs(exact - estimated) / exact


def mean_absolute_error(exact_counts, estimated_counts):
    # Compare estimates over all items in the ground truth.
    if not exact_counts:
        return 0.0

    total_error = 0

    for item, exact in exact_counts.items():
        estimated = estimated_counts.get(item, 0)
        total_error += absolute_error(exact, estimated)

    return total_error / len(exact_counts)


def top_k_precision(exact_counts, estimated_counts, k):
    # Measure the fraction of predicted top-K items that are correct.
    if k <= 0:
        raise ValueError("K must be positive")

    exact_top_k = {
        item for item, _ in sorted(
            exact_counts.items(),
            key=lambda pair: (-pair[1], pair[0])
        )[:k]
    }

    estimated_top_k = {
        item for item, _ in sorted(
            estimated_counts.items(),
            key=lambda pair: (-pair[1], pair[0])
        )[:k]
    }

    if not estimated_top_k:
        return 1.0 if not exact_top_k else 0.0

    return len(exact_top_k & estimated_top_k) / len(estimated_top_k)


def measure_throughput(num_items, elapsed_seconds):
    # Return the number of processed items per second.
    if elapsed_seconds <= 0:
        return 0.0

    return num_items / elapsed_seconds


def measure_processing_time(function, items):
    # Measure how long a counting function takes to process a stream.
    start = perf_counter()
    result = function(items)
    elapsed = perf_counter() - start

    return result, elapsed


def estimate_exact_counter_memory(counter):
    # Estimate memory used by the Python dictionary and its entries.
    total = sys.getsizeof(counter)

    for item, count in counter.items():
        total += sys.getsizeof(item)
        total += sys.getsizeof(count)

    return total


def estimate_sketch_memory(width, depth, bytes_per_counter=8):
    # Estimate raw sketch-table memory, excluding Python object overhead.
    if width <= 0 or depth <= 0:
        raise ValueError("Width and depth must be positive")

    if bytes_per_counter <= 0:
        raise ValueError("Counter size must be positive")

    return width * depth * bytes_per_counter
