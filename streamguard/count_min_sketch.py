"""
Count-Min Sketch (M1)
---------------------
A probabilistic data structure for estimating item frequencies.

Features:
- Configurable width and depth
- Epsilon and delta constructor support
- Standard and conservative updates
- Stable hashing using BLAKE2b
- Memory usage calculation
- Theoretical error bounds
- Compatible sketch merging
- Protection against counter overflow
"""

import hashlib
import math
import random
from typing import Callable, Iterable, List, Optional, Tuple

import numpy as np


_PRIME = (1 << 61) - 1
_MAX_COUNT = (1 << 32) - 1

HashFn = Callable[[object, int, int], int]


class CountMinSketch:

    def __init__(
        self,
        epsilon=None,
        delta=None,
        *,
        width=None,
        depth=None,
        conservative=False,
        seed=42,
        hash_fn=None,
    ):
        """
        Create a Count-Min Sketch.

        Examples:
            CountMinSketch(width=2000, depth=5)
            CountMinSketch(epsilon=0.01, delta=0.01)
            CountMinSketch(0.01, 0.01)
        """

        if epsilon is not None or delta is not None:

            if epsilon is None or delta is None:
                raise ValueError(
                    "Both epsilon and delta must be provided"
                )

            if (
                not isinstance(epsilon, (int, float))
                or isinstance(epsilon, bool)
                or not math.isfinite(epsilon)
                or not 0 < epsilon < 1
            ):
                raise ValueError(
                    "epsilon must be between 0 and 1"
                )

            if (
                not isinstance(delta, (int, float))
                or isinstance(delta, bool)
                or not math.isfinite(delta)
                or not 0 < delta < 1
            ):
                raise ValueError(
                    "delta must be between 0 and 1"
                )

            calculated_width = math.ceil(math.e / epsilon)
            calculated_depth = math.ceil(
                math.log(1.0 / delta)
            )

            if width is not None and width != calculated_width:
                raise ValueError(
                    "width conflicts with epsilon"
                )

            if depth is not None and depth != calculated_depth:
                raise ValueError(
                    "depth conflicts with delta"
                )

            width = calculated_width
            depth = calculated_depth

        else:
            if width is None:
                width = 2000

            if depth is None:
                depth = 5

        if (
            not isinstance(width, (int, np.integer))
            or isinstance(width, bool)
            or width < 1
        ):
            raise ValueError(
                "width must be a positive integer"
            )

        if (
            not isinstance(depth, (int, np.integer))
            or isinstance(depth, bool)
            or depth < 1
        ):
            raise ValueError(
                "depth must be a positive integer"
            )

        self.width = int(width)
        self.depth = int(depth)

        # Compatibility aliases used by existing project tests.
        self.w = self.width
        self.d = self.depth

        self.conservative = bool(conservative)
        self.seed = seed
        self.hash_fn = hash_fn

        self.table = np.zeros(
            (self.depth, self.width),
            dtype=np.int64
        )

        self.total = 0

        rng = random.Random(seed)

        self._a = [
            rng.randrange(1, _PRIME)
            for _ in range(self.depth)
        ]

        self._b = [
            rng.randrange(0, _PRIME)
            for _ in range(self.depth)
        ]

    @classmethod
    def from_error_bounds(
        cls,
        epsilon,
        delta,
        **kwargs
    ):
        """Create a sketch using the requested error parameters."""

        return cls(
            epsilon=epsilon,
            delta=delta,
            **kwargs
        )

    @staticmethod
    def _to_int(item) -> int:
        """Convert an item into a stable integer."""

        if isinstance(item, bytes):
            data = item
        else:
            data = str(item).encode("utf-8")

        digest = hashlib.blake2b(
            data,
            digest_size=8
        ).digest()

        return int.from_bytes(digest, "big")

    def _indices(self, item) -> List[int]:
        """Calculate one table index for each row."""

        if self.hash_fn is not None:
            return [
                self.hash_fn(item, row, self.width) % self.width
                for row in range(self.depth)
            ]

        value = self._to_int(item)

        return [
            ((a * value + b) % _PRIME) % self.width
            for a, b in zip(self._a, self._b)
        ]

    def update(self, item, count=1) -> None:
        """Add a positive number of occurrences of an item."""

        if (
            not isinstance(count, (int, np.integer))
            or isinstance(count, bool)
            or count <= 0
        ):
            raise ValueError(
                "count must be a positive integer"
            )

        count = int(count)
        indices = self._indices(item)

        if self.conservative:

            current = [
                int(self.table[row, column])
                for row, column in enumerate(indices)
            ]

            target = min(
                _MAX_COUNT,
                min(current) + count
            )

            for row, (column, value) in enumerate(
                zip(indices, current)
            ):
                if value < target:
                    self.table[row, column] = target

        else:

            for row, column in enumerate(indices):

                current = int(self.table[row, column])

                new_value = min(
                    _MAX_COUNT,
                    current + count
                )

                self.table[row, column] = new_value

        self.total += count

    add = update

    def update_many(self, items: Iterable[object]) -> None:
        """Update the sketch using an iterable of items."""

        for item in items:
            self.update(item)

    def estimate(self, item) -> int:
        """Estimate the frequency of an item."""

        indices = self._indices(item)

        return min(
            int(self.table[row, column])
            for row, column in enumerate(indices)
        )

    query = estimate

    def __getitem__(self, item) -> int:
        return self.estimate(item)

    def clear(self) -> None:
        """Reset all counters and the total."""

        self.table.fill(0)
        self.total = 0

    def merge(self, other):
        """Merge another compatible sketch into this sketch."""

        if not isinstance(other, CountMinSketch):
            raise TypeError(
                "other must be a CountMinSketch"
            )

        if self.width != other.width or self.depth != other.depth:
            raise ValueError(
                "Cannot merge sketches with different dimensions"
            )

        if self.seed != other.seed:
            raise ValueError(
                "Cannot merge sketches with different seeds"
            )

        if self.conservative != other.conservative:
            raise ValueError(
                "Cannot merge sketches with different update modes"
            )

        if self.hash_fn is not other.hash_fn:
            raise ValueError(
                "Cannot merge sketches with different hash functions"
            )

        if self._a != other._a or self._b != other._b:
            raise ValueError(
                "Cannot merge sketches with different hash parameters"
            )

        # Saturating addition prevents counter overflow.
        safe_first = np.minimum(
            self.table,
            _MAX_COUNT - other.table
        )

        self.table[:] = safe_first + other.table
        self.total += other.total

        return self

    def memory_bytes(self) -> int:
        """Return the memory occupied by the counter table."""

        return int(self.table.nbytes)

    @staticmethod
    def theoretical_memory(
        width,
        depth,
        bytes_per_counter=8
    ) -> int:
        """Calculate theoretical counter-table memory."""

        if (
            width < 1
            or depth < 1
            or bytes_per_counter < 1
        ):
            raise ValueError(
                "All arguments must be positive"
            )

        return width * depth * bytes_per_counter

    @property
    def epsilon(self) -> float:
        return math.e / self.width

    @property
    def delta(self) -> float:
        return math.exp(-self.depth)

    def error_bound(self) -> Tuple[float, float]:
        """Return the additive error bound and confidence."""

        return (
            self.epsilon * self.total,
            1.0 - self.delta
        )

    def __repr__(self) -> str:

        mode = (
            "conservative"
            if self.conservative
            else "standard"
        )

        return (
            f"CountMinSketch(width={self.width}, "
            f"depth={self.depth}, mode={mode}, "
            f"N={self.total}, "
            f"mem={self.memory_bytes()}B)"
        )
