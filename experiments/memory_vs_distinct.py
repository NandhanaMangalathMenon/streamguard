
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from streamguard.traffic_generator import generate_traffic
from streamguard.exact_counter import count_items
from streamguard.metrics import estimate_exact_counter_memory
from streamguard.metrics import estimate_sketch_memory


def run_experiment():
    distinct_counts = [10, 50, 100, 500, 1000, 5000]
    num_packets = 10000

    # Fixed sketch dimensions allow us to demonstrate fixed table size.
    width = 500
    depth = 5

    results = []

    for distinct in distinct_counts:
        # Generate traffic with the requested number of distinct sources.
        traffic = generate_traffic(
            num_packets=num_packets,
            num_sources=distinct,
            heavy_hitter_count=min(5, distinct),
            heavy_hitter_probability=0.60,
            seed=42
        )

        # Exact counting stores an entry for every distinct source.
        exact_counts = count_items(traffic)
        exact_memory = estimate_exact_counter_memory(exact_counts)

        # Sketch table memory is fixed for these dimensions.
        sketch_memory = estimate_sketch_memory(width, depth)

        results.append({
            "Distinct Sources": distinct,
            "Exact Memory (bytes)": exact_memory,
            "Sketch Memory (bytes)": sketch_memory
        })

    dataframe = pd.DataFrame(results)

    # Save the measurements for reports and presentations.
    os.makedirs("results", exist_ok=True)
    dataframe.to_csv(
        "results/memory_vs_distinct.csv",
        index=False
    )

    print(dataframe.to_string(index=False))

    # Generate a graph for the project report.
    plt.figure()
    plt.plot(
        dataframe["Distinct Sources"],
        dataframe["Exact Memory (bytes)"],
        marker="o",
        label="Exact Counter"
    )
    plt.plot(
        dataframe["Distinct Sources"],
        dataframe["Sketch Memory (bytes)"],
        marker="s",
        label="Count-Min Sketch"
    )

    plt.xlabel("Number of Distinct Sources")
    plt.ylabel("Estimated Memory (bytes)")
    plt.title("Memory Usage vs Distinct Sources")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/memory_vs_distinct.png")
    plt.show()


if __name__ == "__main__":
    run_experiment()
