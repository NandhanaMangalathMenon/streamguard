"""Evaluate Top-K accuracy on a synthetic stream."""

from collections import Counter

from streamguard.count_min_sketch import CountMinSketch
from streamguard.topk import TopK


def main():
    # Create a sample stream with known item frequencies
    stream = (
        ["apple"] * 100
        + ["banana"] * 70
        + ["orange"] * 50
        + ["grape"] * 30
        + ["pear"] * 10
        + ["kiwi"] * 5
    )

    k = 3

    # Calculate the actual frequencies
    actual_counts = Counter(stream)

    # Create the Count-Min Sketch and TopK tracker
    sketch = CountMinSketch(width=500, depth=5, seed=42)
    tracker = TopK(sketch, k=k)

    # Process the stream
    for item in stream:
        tracker.add(item)

    # Compare actual and estimated top-k items
    actual_top_k = [
        item for item, _ in actual_counts.most_common(k)
    ]

    estimated_top_k = [
        item for item, _ in tracker.get_top_k(k)
    ]

    # Calculate precision
    overlap = len(set(actual_top_k) & set(estimated_top_k))
    precision = overlap / k

    print("Total stream items:", len(stream))
    print("K:", k)
    print("Actual Top-K:", actual_top_k)
    print("Estimated Top-K:", estimated_top_k)
    print(f"Top-K precision: {precision:.2f}")


if __name__ == "__main__":
    main()