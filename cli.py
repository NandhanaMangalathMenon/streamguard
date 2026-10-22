
"""Command-line interface for StreamGuard."""

import argparse
import sys

from streamguard.count_min_sketch import CountMinSketch
from streamguard.topk import TopK


def build_parser():
    parser = argparse.ArgumentParser(
        description="StreamGuard: find frequent items in a data stream."
    )
    parser.add_argument(
        "items",
        nargs="*",
        help="Stream items to count, e.g. apple banana apple",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=5,
        help="Number of top items to display (default: 5)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=2000,
        help="Count-Min Sketch width (default: 2000)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Count-Min Sketch depth (default: 5)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.k <= 0:
        parser.error("-k must be positive")
    if args.width <= 0 or args.depth <= 0:
        parser.error("--width and --depth must be positive")
    if not args.items:
        parser.error("provide at least one stream item")

    sketch = CountMinSketch(width=args.width, depth=args.depth)
    tracker = TopK(sketch, k=args.k)

    try:
        for item in args.items:
            tracker.add(item)
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Top frequent items:")
    for rank, (item, count) in enumerate(tracker.get_top_k(), start=1):
        print(f"{rank}. {item}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

