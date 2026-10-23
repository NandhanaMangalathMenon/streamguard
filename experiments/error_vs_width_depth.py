"""
Experiment: How estimation error depends on sketch width and depth.

Usage (from repository root):
    python experiments/error_vs_width_depth.py
    python experiments/error_vs_width_depth.py --n 100000 --distinct 5000 --skew 1.1

Outputs:
    experiments/results/error_vs_width_depth.csv
    experiments/results/error_vs_width_depth.png
"""

import argparse
import csv
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


# Project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from streamguard.count_min_sketch import CountMinSketch


# Directory for experiment results
OUT = os.path.join(ROOT, "experiments", "results")


def zipf_stream(n, distinct, skew, seed):
    """
    Generate a stream with Zipf-like frequency distribution.

    Parameters:
        n       : Number of items in the stream
        distinct: Number of unique possible items
        skew    : Controls how uneven item frequencies are
        seed    : Random seed for reproducibility

    Returns:
        A list containing the generated stream.
    """

    rng = np.random.default_rng(seed)

    probabilities = 1.0 / (
        np.arange(1, distinct + 1, dtype=float) ** skew
    )

    probabilities /= probabilities.sum()

    indices = rng.choice(
        distinct,
        size=n,
        replace=True,
        p=probabilities
    )

    return [f"item_{i}" for i in indices]


def validate_arguments(args):
    """Validate command-line arguments."""

    if args.n < 1:
        raise ValueError("--n must be at least 1.")

    if args.distinct < 1:
        raise ValueError("--distinct must be at least 1.")

    if args.skew < 0:
        raise ValueError("--skew cannot be negative.")

    if args.seed < 0:
        raise ValueError("--seed cannot be negative.")


def run_experiment(truth, widths, depths, seed):
    """
    Test multiple Count-Min Sketch configurations.

    Returns:
        A list of dictionaries containing experimental results.
    """

    rows = []

    total_count = sum(truth.values())

    for depth in depths:
        for width in widths:

            # Create a Count-Min Sketch
            cms = CountMinSketch(
                width=width,
                depth=depth,
                seed=seed
            )

            # Insert each item using its exact frequency.
            # This is valid for the standard Count-Min Sketch.
            for item, count in truth.items():
                cms.update(item, count)

            # Calculate estimation errors for every distinct item
            errors = np.array(
                [
                    cms.estimate(item) - true_count
                    for item, true_count in truth.items()
                ],
                dtype=float
            )

            mean_error = float(errors.mean())
            max_error = int(errors.max())

            # Get the additive error bound and confidence parameter
            bound, confidence = cms.error_bound()

            # Percentage of distinct items within the additive bound
            within_bound = float(
                100.0 * np.mean(errors <= bound)
            )

            result = {
                "depth": depth,
                "width": width,
                "memory_bytes": cms.memory_bytes(),
                "mean_error": mean_error,
                "max_error": max_error,
                "bound_eps_N": bound,
                "confidence": confidence,
                "pct_within_bound": within_bound,
                "total_stream_count": total_count,
                "distinct_observed": len(truth)
            }

            rows.append(result)

            print(
                f"depth={depth}, "
                f"width={width:5d}, "
                f"memory={cms.memory_bytes():7d} bytes, "
                f"mean_error={mean_error:9.2f}, "
                f"max_error={max_error:8d}, "
                f"within_bound={within_bound:6.2f}%"
            )

    return rows


def save_results(rows):
    """Save experimental results to a CSV file."""

    os.makedirs(OUT, exist_ok=True)

    csv_path = os.path.join(
        OUT,
        "error_vs_width_depth.csv"
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV results saved to: {csv_path}")


def plot_results(rows, widths, depths, args):
    """Generate and save error comparison graphs."""

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5)
    )

    # Graph 1: Mean estimation error versus width
    ax = axes[0]

    for depth in depths:

        selected = [
            row for row in rows
            if row["depth"] == depth
        ]

        selected.sort(key=lambda row: row["width"])

        mean_errors = [
            max(row["mean_error"], 1e-3)
            for row in selected
        ]

        ax.plot(
            [row["width"] for row in selected],
            mean_errors,
            marker="o",
            label=f"Depth = {depth}"
        )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xlabel("Width")
    ax.set_ylabel("Mean Overestimation")

    ax.set_title("Mean Error vs Width")

    ax.legend()
    ax.grid(True, alpha=0.3)

    # Graph 2: Mean estimation error versus depth
    ax = axes[1]

    selected_widths = [
        width for width in [200, 1000]
        if width in widths
    ]

    for width in selected_widths:

        selected = [
            row for row in rows
            if row["width"] == width
        ]

        selected.sort(key=lambda row: row["depth"])

        ax.plot(
            [row["depth"] for row in selected],
            [row["mean_error"] for row in selected],
            marker="s",
            label=f"Width = {width}"
        )

    ax.set_xlabel("Depth")
    ax.set_ylabel("Mean Overestimation")

    ax.set_title("Mean Error vs Depth")

    ax.legend()
    ax.grid(True, alpha=0.3)

    # Overall title
    fig.suptitle(
        f"Count-Min Sketch Error "
        f"(N={args.n:,}, "
        f"Distinct={args.distinct:,}, "
        f"Zipf Skew={args.skew})"
    )

    fig.tight_layout()

    image_path = os.path.join(
        OUT,
        "error_vs_width_depth.png"
    )

    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"Graph saved to: {image_path}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Study the effect of Count-Min Sketch "
            "width and depth on estimation error."
        )
    )

    parser.add_argument(
        "--n",
        type=int,
        default=100000,
        help="Number of items in the stream."
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
        help="Zipf distribution skew; must be non-negative."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    try:
        validate_arguments(args)

    except ValueError as error:
        parser.error(str(error))

    print("Generating stream...")

    stream = zipf_stream(
        args.n,
        args.distinct,
        args.skew,
        args.seed
    )

    # Exact frequencies serve as the ground truth
    truth = Counter(stream)

    print(f"Stream length: {args.n:,}")
    print(f"Distinct observed items: {len(truth):,}")
    print("\nRunning experiments...\n")

    # Configuration values to compare
    widths = [50, 100, 200, 500, 1000, 2000, 5000]
    depths = [1, 2, 3, 5, 7]

    rows = run_experiment(
        truth,
        widths,
        depths,
        args.seed
    )

    if not rows:
        print("No experiment results were generated.")
        return

    # Save CSV results and comparison graphs
    save_results(rows)

    plot_results(
        rows,
        widths,
        depths,
        args
    )

    print("\nAll experiments completed successfully.")


if __name__ == "__main__":
    main()
    
