"""Unit tests for streamguard.count_min_sketch (M1)."""

import math
import os
import sys
from collections import Counter

import numpy as np
import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from streamguard.count_min_sketch import CountMinSketch  # noqa: E402


def zipf_stream(n=5000, distinct=500, s=1.1, seed=0):
    """Generate a reproducible stream with a Zipf-like distribution."""
    rng = np.random.default_rng(seed)
    probabilities = 1.0 / np.arange(1, distinct + 1) ** s
    probabilities /= probabilities.sum()

    return [
        f"ip_{i}"
        for i in rng.choice(distinct, size=n, p=probabilities)
    ]


@pytest.mark.parametrize("conservative", [False, True])
def test_never_underestimates(conservative):
    stream = zipf_stream()
    truth = Counter(stream)

    cms = CountMinSketch(
        width=100,
        depth=4,
        conservative=conservative
    )
    cms.update_many(stream)

    for item, count in truth.items():
        assert cms.estimate(item) >= count


@pytest.mark.parametrize("conservative", [False, True])
def test_exact_when_no_collisions(conservative):
    cms = CountMinSketch(
        width=100_000,
        depth=5,
        conservative=conservative
    )

    items = {"a": 5, "b": 3, "c": 10}

    for item, count in items.items():
        cms.update(item, count)

    for item, count in items.items():
        assert cms.estimate(item) == count


def test_unseen_item_is_zero_in_empty_sketch():
    cms = CountMinSketch()

    assert cms.estimate("nothing") == 0


def test_error_within_theoretical_bound():
    stream = zipf_stream(n=10_000, distinct=1000)
    truth = Counter(stream)

    cms = CountMinSketch(width=500, depth=5)
    cms.update_many(stream)

    bound, _ = cms.error_bound()

    within_bound = sum(
        cms.estimate(item) - count <= bound
        for item, count in truth.items()
    )

    assert within_bound / len(truth) >= 0.99


def test_conservative_updates_do_not_underestimate():
    stream = zipf_stream(n=8000, distinct=800)
    truth = Counter(stream)

    cms = CountMinSketch(
        width=150,
        depth=4,
        conservative=True
    )
    cms.update_many(stream)

    for item, count in truth.items():
        assert cms.estimate(item) >= count


def test_more_width_reduces_error():
    stream = zipf_stream(n=8000, distinct=800)
    truth = Counter(stream)

    def mean_error(width):
        cms = CountMinSketch(width=width, depth=4)
        cms.update_many(stream)

        errors = [
            cms.estimate(item) - count
            for item, count in truth.items()
        ]

        return np.mean(errors)

    assert mean_error(2000) < mean_error(100)


def test_memory_is_fixed_and_matches_formula():
    cms = CountMinSketch(width=1000, depth=5)
    memory_before = cms.memory_bytes()

    cms.update_many(f"x{i}" for i in range(20_000))

    assert cms.memory_bytes() == memory_before
    assert memory_before == CountMinSketch.theoretical_memory(
        1000, 5, 8
    )


def test_from_error_bounds():
    cms = CountMinSketch.from_error_bounds(
        epsilon=0.01,
        delta=0.01
    )

    assert cms.width == math.ceil(math.e / 0.01)
    assert cms.depth == math.ceil(math.log(100))
    assert cms.epsilon <= 0.01
    assert cms.delta <= 0.01


def test_deterministic_with_seed():
    first = CountMinSketch(seed=7)
    second = CountMinSketch(seed=7)

    stream = zipf_stream(n=1000)

    first.update_many(stream)
    second.update_many(stream)

    assert np.array_equal(first.table, second.table)


def test_clear_and_total():
    cms = CountMinSketch()

    cms.update("a", 3)

    assert cms.total == 3

    cms.clear()

    assert cms.total == 0
    assert cms.estimate("a") == 0


def test_item_types():
    cms = CountMinSketch(width=10_000)

    cms.update(42)
    cms.update(b"bytes")
    cms.update("192.168.0.1", 2)

    assert cms.estimate(42) >= 1
    assert cms.estimate(b"bytes") >= 1
    assert cms["192.168.0.1"] >= 2


def test_custom_hash_fn():
    calls = []

    def custom_hash(item, row, width):
        calls.append(row)
        return (
            sum(str(item).encode()) + row * 31
        ) % width

    cms = CountMinSketch(
        width=50,
        depth=3,
        hash_fn=custom_hash
    )

    cms.update("z", 2)

    assert cms.estimate("z") >= 2
    assert set(calls) == {0, 1, 2}


@pytest.mark.parametrize(
    "width,depth",
    [(0, 3), (3, 0), (-1, 2)]
)
def test_invalid_dimensions(width, depth):
    with pytest.raises(ValueError):
        CountMinSketch(width=width, depth=depth)


def test_invalid_counts_and_bounds():
    cms = CountMinSketch()

    with pytest.raises(ValueError):
        cms.update("a", -1)

    with pytest.raises(ValueError):
        cms.update("a", 0)

    assert cms.total == 0

    with pytest.raises(ValueError):
        CountMinSketch.from_error_bounds(0, 0.1)
