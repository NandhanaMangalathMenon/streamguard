"""
Experiment: Standard vs Conservative Count-Min Sketch Update.

Conservative update is order-dependent, so both sketches receive
the same ordered stream.

Usage from the repository root:
    python experiments/conservative_vs_standard.py
    python experiments/conservative_vs_standard.py --n 50000 --distinct 5000

Outputs:
    experiments/results/conservative_vs_standard.csv
    experiments/results/conservative_vs_standard.png
"""

import argparse
import csv
import os
import sys
import time
from collections import Counter

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


# Locate the project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from streamguard.count_min_sketch import CountMinSketch


# Output directory
OUT = os.path.join(ROOT, "experiments", "results")


def zipf_stream(n, distinct, skew, seed):
    """Generate a stream with a Zipf-like frequency distribution."""

    rng = np.random.default_rng(seed)

    probabilities = (
        1.0 / np.arange(1, distinct + 1, dtype=float) ** skew
    )

    probabilities /= probabilities.sum()

    indices = rng.choice(
        distinct,
        size=n,
        replace=True,
        p=probabilities
    )

    return [f"item_{i}" for i in indices]


def run(stream, truth, width, depth, conservative, seed):
    """
    Run one Count-Min Sketch configuration.

    Returns estimation accuracy, memory usage, and update throughput.
    """

    cms = CountMinSketch(
        width=width,
        depth=depth,
        conservative=conservative,
        seed=seed
    )

    start_time = time.perf_counter()

    # Process the original stream in its original order
    for item in stream:
        cms.update(item)

    elapsed = time.perf_counter() - start_time

    # Estimate each observed item's frequency
    errors = np.array(
        [
            cms.estimate(item) - count
            for item, count in truth.items()
        ],
        dtype=float
    )

    # Protect calculations against an empty stream
    if len(errors) == 0:
        mean_error = 0.0
        max_error = 0
        pct_exact = 0.0
    else:
        mean_error = float(errors.mean())
        max_error = int(errors.max())
        pct_exact = float(100.0 * np.mean(errors == 0))

    updates_per_sec = (
        len(stream) / elapsed if elapsed > 0 else 0.0
    )

    return {
        "mean_error": mean_error,
        "max_error": max_error,
        "pct_exact": pct_exact,
        "updates_per_sec": updates_per_sec,
        "memory_bytes": cms.memory_bytes()
    }


def validate_args(args):
    """Validate command-line arguments."""

    if args.n < 1:
        raise ValueError("--n must be at least 1.")

    if args.distinct < 1:
        raise ValueError("--distinct must be at least 1.")

    if args.skew < 0:
        raise ValueError("--skew cannot be negative.")

    if args.depth < 1:
        raise ValueError("--depth must be at least 1.")

    if args.seed < 0:
        raise ValueError("--seed cannot be negative.")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Compare standard and conservative "
            "Count-Min Sketch updates."
        )
    )

    parser.add_argument(
        "--n",
        type=int,
        default=50000,
        help="Number of items in each generated stream."
    )

    parser.add_argument(
        "--distinct",
        type=int,
        default=5000,
        help="Number of possible distinct items."
    )

    parser.add_argument(
        "--skew",
        type=float,
        default=1.1,
        help="Zipf skew for the width experiment."
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=4,
        help="Count-Min Sketch depth."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as error:
        parser.error(str(error))

    os.makedirs(OUT, exist_ok=True)

    rows = []

    # --------------------------------------------------
    # Experiment 1: Compare update variants across widths
    # --------------------------------------------------

    print("Generating stream for width experiment...")

    stream = zipf_stream(
        args.n,
        args.distinct,
        args.skew,
        args.seed
    )

    truth = Counter(stream)

    widths = [100, 200, 500, 1000, 2000, 5000]

    print("\nRunning width experiment...\n")

    for width in widths:

        for conservative in (False, True):

            result = run(
                stream,
                truth,
                width,
                args.depth,
                conservative,
                args.seed
            )

            variant = (
                "conservative" if conservative else "standard"
            )

            rows.append({
                "experiment": "width",
                "width": width,
                "skew": args.skew,
                "depth": args.depth,
                "variant": variant,
                **result
            })

            print(
                f"width={width:5d} "
                f"{variant:12s} "
                f"mean_error={result['mean_error']:8.2f} "
                f"max_error={result['max_error']:6d} "
                f"exact={result['pct_exact']:5.1f}% "
                f"throughput={result['updates_per_sec']:9.0f} updates/sec"
            )

    # --------------------------------------------------
    # Experiment 2: Compare update variants across skews
    # --------------------------------------------------

    fixed_width = 500

    skews = [0.6, 0.8, 1.0, 1.2, 1.5]

    print("\nRunning skew experiment...\n")

    for skew in skews:

        skew_stream = zipf_stream(
            args.n,
            args.distinct,
            skew,
            args.seed
        )

        skew_truth = Counter(skew_stream)

        for conservative in (False, True):

            result = run(
                skew_stream,
                skew_truth,
                fixed_width,
                args.depth,
                conservative,
                args.seed
            )

            variant = (
                "conservative" if conservative else "standard"
            )

            rows.append({
                "experiment": "skew",
                "width": fixed_width,
                "skew": skew,
                "depth": args.depth,
                "variant": variant,
                **result
            })

            print(
                f"skew={skew:.1f} "
                f"{variant:12s} "
                f"mean_error={result['mean_error']:8.2f} "
                f"max_error={result['max_error']:6d} "
                f"exact={result['pct_exact']:5.1f}% "
                f"throughput={result['updates_per_sec']:9.0f} updates/sec"
            )

    # --------------------------------------------------
    # Save results to CSV
    # --------------------------------------------------

    csv_path = os.path.join(
        OUT,
        "conservative_vs_standard.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV saved to: {csv_path}")

    # --------------------------------------------------
    # Generate comparison graphs
    # --------------------------------------------------

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    # Graph 1: Mean error versus width
    for variant, style in (
        ("standard", "o-"),
        ("conservative", "s--")
    ):

        selected = [
            row for row in rows
            if row["experiment"] == "width"
            and row["variant"] == variant
        ]

        selected.sort(key=lambda row: row["width"])

        axes[0].plot(
            [row["width"] for row in selected],
            [
                max(row["mean_error"], 1e-3)
                for row in selected
            ],
            style,
            label=variant
        )

    axes[0].set_xscale("log")
    axes[0].set_yscale("log")

    axes[0].set_xlabel("Width")
    axes[0].set_ylabel("Mean Overestimation")

    axes[0].set_title(
        f"Error vs Width (Depth = {args.depth})"
    )

    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Graph 2: Mean error versus skew
    for variant, style in (
        ("standard", "o-"),
        ("conservative", "s--")
    ):

        selected = [
            row for row in rows
            if row["experiment"] == "skew"
            and row["variant"] == variant
        ]

        selected.sort(key=lambda row: row["skew"])

        axes[1].plot(
            [row["skew"] for row in selected],
            [row["mean_error"] for row in selected],
            style,
            label=variant
        )

    axes[1].set_xlabel("Zipf Skew")
    axes[1].set_ylabel("Mean Overestimation")

    axes[1].set_title(
        f"Error vs Traffic Skew (Width = {fixed_width})"
    )

    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()

    image_path = os.path.join(
        OUT,
        "conservative_vs_standard.png"
    )

    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"Graph saved to: {image_path}")
    print("\nAll experiments completed successfully.")


if __name__ == "__main__":
    main()
    
