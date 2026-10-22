
import streamlit as st
import pandas as pd

from streamguard.metrics import (
    absolute_error,
    relative_error,
    mean_absolute_error,
    top_k_precision
)


def show_accuracy_tab(exact_counts, estimated_counts):
    st.header("Accuracy Evaluation")

    # Combine the exact and estimated frequencies for comparison.
    items = sorted(set(exact_counts) | set(estimated_counts))

    rows = []

    for item in items:
        exact = exact_counts.get(item, 0)
        estimated = estimated_counts.get(item, 0)

        rows.append({
            "Source IP": item,
            "Exact Count": exact,
            "Estimated Count": estimated,
            "Absolute Error": absolute_error(exact, estimated),
            "Relative Error": relative_error(exact, estimated)
        })

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info("No traffic data available.")
        return

    # Display overall accuracy metrics.
    mae = mean_absolute_error(exact_counts, estimated_counts)
    precision = top_k_precision(
        exact_counts, estimated_counts,
        min(5, len(exact_counts))
    ) if exact_counts else 0.0

    col1, col2 = st.columns(2)
    col1.metric("Mean Absolute Error", f"{mae:.3f}")
    col2.metric("Top-K Precision", f"{precision:.1%}")

    # Show individual frequencies and their estimation errors.
    st.subheader("Exact vs Estimated Frequencies")
    st.dataframe(dataframe, use_container_width=True)

    st.subheader("Frequency Comparison")
    chart_data = dataframe.set_index("Source IP")[
        ["Exact Count", "Estimated Count"]
    ]
    st.bar_chart(chart_data.head(20))

    st.subheader("Estimation Error")
    st.bar_chart(
        dataframe.set_index("Source IP")[["Absolute Error"]].head(20)
    )
