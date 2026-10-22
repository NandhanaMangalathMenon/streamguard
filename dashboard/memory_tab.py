import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st

# Add the project root to Python's import path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from streamguard.count_min_sketch import CountMinSketch


def _fmt_bytes(n):
    """Convert bytes into a readable memory size."""
    n = float(n)

    for unit in ["B", "KB", "MB", "GB"]:
        if abs(n) < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024

    return f"{n:.2f} TB"


def exact_counter_bytes(counter):
    """Estimate memory used by an exact Counter."""
    total = sys.getsizeof(counter)

    for key, value in counter.items():
        total += sys.getsizeof(key)
        total += sys.getsizeof(value)

    return total


@st.cache_data
def _make_stream(n, distinct, skew, seed):
    """Generate a stream of items with controllable frequency skew."""
    rng = np.random.default_rng(seed)

    if distinct < 1:
        return []

    if skew <= 0:
        indices = rng.integers(0, distinct, size=n)
    else:
        probabilities = np.arange(1, distinct + 1, dtype=float) ** (-skew)
        probabilities /= probabilities.sum()

        indices = rng.choice(
            distinct,
            size=n,
            replace=True,
            p=probabilities
        )

    return [
        f"item_{i}"
        for i in indices
    ]


def render_memory_tab():
    """Display Count-Min Sketch memory usage and estimation errors."""

    st.header("Count-Min Sketch: Memory Efficiency")

    st.write(
        "Compare the memory used by an exact frequency counter "
        "with the memory used by a Count-Min Sketch."
    )

    # Count-Min Sketch settings
    st.subheader("1. Sketch Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        width = st.slider(
            "Width",
            min_value=100,
            max_value=10000,
            value=2000,
            step=100
        )

    with col2:
        depth = st.slider(
            "Depth",
            min_value=1,
            max_value=10,
            value=5
        )

    with col3:
        conservative = st.toggle(
            "Conservative Update",
            value=False
        )

    # Stream settings
    st.subheader("2. Stream Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        stream_length = st.slider(
            "Stream Length",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000
        )

    with col2:
        distinct_items = st.slider(
            "Distinct Items",
            min_value=100,
            max_value=10000,
            value=2000,
            step=100
        )

    with col3:
        skew = st.slider(
            "Frequency Skew",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1
        )

    seed = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=100000,
        value=42
    )

    # Generate data
    stream = _make_stream(
        stream_length,
        distinct_items,
        skew,
        seed
    )

    # Build the exact counter
    exact_counter = Counter(stream)

    # Build the Count-Min Sketch
    sketch = CountMinSketch(
        width=width,
        depth=depth,
        conservative=conservative,
        seed=seed
    )

    sketch.update_many(stream)

    # Calculate memory usage
    exact_memory = exact_counter_bytes(exact_counter)
    sketch_memory = sketch.memory_bytes()

    memory_saved = exact_memory - sketch_memory

    if exact_memory > 0:
        savings_percentage = (
            memory_saved / exact_memory
        ) * 100
    else:
        savings_percentage = 0.0

    # Calculate estimation errors
    errors = []

    for item, true_count in exact_counter.items():
        estimated_count = sketch.estimate(item)
        error = estimated_count - true_count
        errors.append(error)

    mean_error = float(np.mean(errors)) if errors else 0.0
    max_error = int(max(errors)) if errors else 0

    # Display results
    st.subheader("3. Memory and Accuracy Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Exact Counter Memory",
            _fmt_bytes(exact_memory)
        )

    with col2:
        st.metric(
            "Sketch Memory",
            _fmt_bytes(sketch_memory)
        )

    with col3:
        st.metric(
            "Memory Saved",
            f"{savings_percentage:.2f}%"
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Distinct Items",
            f"{len(exact_counter):,}"
        )

    with col2:
        st.metric(
            "Mean Overestimation",
            f"{mean_error:.3f}"
        )

    with col3:
        st.metric(
            "Maximum Overestimation",
            max_error
        )

    if memory_saved > 0:
        st.success(
            "The Count-Min Sketch uses less memory than "
            "the exact counter for this configuration."
        )
    else:
        st.warning(
            "The Count-Min Sketch does not save memory "
            "for this configuration. Try reducing its width "
            "or increasing the number of distinct items."
        )

    # Memory comparison chart
    st.subheader("4. Memory Comparison")

    memory_df = pd.DataFrame({
        "Method": [
            "Exact Counter",
            "Count-Min Sketch"
        ],
        "Memory (bytes)": [
            exact_memory,
            sketch_memory
        ]
    })

    st.bar_chart(
        memory_df.set_index("Method")
    )

    # Error distribution
    st.subheader("5. Overestimation Distribution")

    error_df = pd.DataFrame({
        "Overestimation": errors
    })

    if not error_df.empty:
        st.bar_chart(
            error_df["Overestimation"].value_counts().sort_index()
        )
    else:
        st.info("No items are available to compare.")

    # Theoretical memory
    st.subheader("6. Theoretical Sketch Memory")

    theoretical_memory = sketch.theoretical_memory()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Theoretical Table Memory",
            _fmt_bytes(theoretical_memory)
        )

    with col2:
        st.metric(
            "Actual NumPy Table Memory",
            _fmt_bytes(sketch.memory_bytes())
        )

    st.caption(
        "Exact Counter memory is an estimate based on Python object sizes. "
        "Sketch memory measures the NumPy counter table; it excludes "
        "additional Python object overhead and hash parameters. "
        "Actual results depend on the data and configuration."
    )


# Optional alias for compatibility with other dashboard modules
render = render_memory_tab