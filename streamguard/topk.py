
"""Track the most frequent items using a Count-Min Sketch."""

from collections.abc import Hashable


class TopK:
    """Maintain candidate items and rank them by estimated frequency."""

    def __init__(self, sketch, k: int = 10):
        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer")

        self.sketch = sketch
        self.k = k
        self.candidates: set[Hashable] = set()

    def add(self, item: Hashable, count: int = 1) -> None:
        """Add occurrences of an item to the sketch and candidate set."""
        if count < 0:
            raise ValueError("count must be non-negative")

        if count == 0:
            return

        self.sketch.update(item, count)
        self.candidates.add(item)

    def get_top_k(self, k: int | None = None) -> list[tuple[Hashable, int]]:
        """Return up to k items, sorted by estimated frequency."""
        if k is None:
            k = self.k

        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer")

        ranked = [
            (item, self.sketch.estimate(item))
            for item in self.candidates
        ]

        ranked.sort(key=lambda pair: (-pair[1], str(pair[0])))
        return ranked[:k]
