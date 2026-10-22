
import streamlit as st
import pandas as pd


def show_performance_tab(results):
    st.header("Performance Benchmark")

    # The experiment should supply these measurements.
    required_columns = {
        "Method",
        "Packets",
        "Time (seconds)",
        "Throughput (items/sec)",
        "Memory (bytes)"
    }

    if not required_columns.issubset(results.columns):
        st.error("Benchmark results are missing required columns.")
        return

    if results.empty:
        st.info("Run an experiment to display performance results.")
        return

    # Display the benchmark results.
    st.dataframe(results, use_container_width=True)

    # Compare processing speed.
    st.subheader("Throughput Comparison")
    st.bar_chart(
        results.set_index("Method")[["Throughput (items/sec)"]]
    )

    # Compare memory requirements.
    st.subheader("Memory Usage Comparison")
    st.bar_chart(
        results.set_index("Method")[["Memory (bytes)"]]
    )

    # Display execution time.
    st.subheader("Processing Time")
    st.bar_chart(
        results.set_index("Method")[["Time (seconds)"]]
    )

