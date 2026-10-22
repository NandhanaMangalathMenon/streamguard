"""StreamGuard dashboard: main page, sidebar controls and tab layout.

Run from the repository root:
    streamlit run dashboard/app.py
"""
import os
import sys

# Make `streamguard` and `dashboard` importable when launched by Streamlit.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from streamguard.count_min_sketch import CountMinSketch
from streamguard.exact_counter import ExactCounter
from streamguard.topk import TopK
from streamguard.traffic_generator import generate_stream
from dashboard import accuracy_tab, anomaly_tab, memory_tab, performance_tab

st.set_page_config(page_title="StreamGuard", page_icon="🛡️", layout="wide")
st.title("🛡️ StreamGuard: Network Traffic Heavy-Hitter Monitor")
st.caption("Count-Min Sketch vs exact counting: accuracy, speed and memory")

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Sketch parameters")
epsilon = st.sidebar.number_input(
    "epsilon (error factor)", min_value=0.0001, max_value=0.5,
    value=0.001, step=0.0005, format="%.4f")
delta = st.sidebar.number_input(
    "delta (failure probability)", min_value=0.0001, max_value=0.5,
    value=0.01, step=0.005, format="%.4f")
conservative = st.sidebar.checkbox("Conservative update", value=False)
k = st.sidebar.slider("Top-k size", 3, 20, 10)

st.sidebar.header("Traffic stream")
n_events = st.sidebar.number_input(
    "Stream size", min_value=1000, max_value=500_000, value=50_000, step=5_000)
unique_ips = st.sidebar.number_input(
    "Unique source IPs", min_value=10, max_value=200_000, value=5_000, step=500)
skew = st.sidebar.slider("Zipf skew (higher = more concentrated)", 0.5, 2.0, 1.2, 0.1)
seed = st.sidebar.number_input("Random seed", min_value=0, value=42, step=1)

st.sidebar.header("Anomaly (DDoS) injection")
inject = st.sidebar.checkbox("Inject flood", value=False)
anomaly_ip = st.sidebar.text_input("Flooding IP", "203.0.113.9")
anomaly_count = st.sidebar.number_input(
    "Flood size", min_value=0, max_value=500_000, value=10_000, step=1_000)

run = st.sidebar.button("▶ Run stream", type="primary")


# ---------------------------------------------------------------- pipeline
def run_pipeline():
    """Generate a stream and feed it to the sketch, the exact counter and top-k."""
    stream = generate_stream(
        n=int(n_events), unique=int(unique_ips), skew=float(skew), seed=int(seed),
        anomaly_ip=anomaly_ip if inject else None,
        anomaly_count=int(anomaly_count) if inject else 0,
    )
    sketch = CountMinSketch(epsilon, delta, seed=int(seed), conservative=conservative)
    exact = ExactCounter()
    topk = TopK(int(k))

    progress = st.progress(0.0, text="Processing stream...")
    total = len(stream)
    for i, ip in enumerate(stream, start=1):
        sketch.update(ip)
        exact.update(ip)
        topk.update(ip, sketch.query(ip))
        if i % 5000 == 0 or i == total:
            progress.progress(i / total, text=f"Processed {i:,} / {total:,} events")
    progress.empty()

    return {
        "sketch": sketch, "exact": exact, "topk": topk, "stream": stream,
        "epsilon": epsilon, "delta": delta, "k": int(k), "seed": int(seed),
        "conservative": conservative,
        "anomaly_ip": anomaly_ip if inject else None,
        "anomaly_count": int(anomaly_count) if inject else 0,
    }


if run:
    try:
        st.session_state["state"] = run_pipeline()
    except Exception as exc:  # show a friendly message instead of a crash
        st.error(f"Could not run the stream: {exc}")

state = st.session_state.get("state")

# ---------------------------------------------------------------- main area
if state is None:
    st.info("Set the parameters in the sidebar and click **Run stream**.")
    st.stop()

sketch, exact = state["sketch"], state["exact"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events processed", f"{sketch.total:,}")
c2.metric("Unique IPs (exact)", f"{len(exact.counts):,}")
c3.metric("Sketch size", f"w={sketch.w}, d={sketch.d}")
c4.metric("Sketch memory", f"{sketch.memory_bytes() / 1024:.1f} KB")

tab_live, tab_acc, tab_perf, tab_mem, tab_anom = st.tabs(
    ["Live Top-k", "Accuracy", "Performance", "Memory", "Anomaly"])

with tab_live:
    st.subheader("Top heavy hitters (estimated vs exact)")
    rows = [
        {"Rank": i, "Source IP": ip, "Estimated": est,
         "Exact": exact.counts.get(ip, 0), "Overcount": est - exact.counts.get(ip, 0)}
        for i, (ip, est) in enumerate(state["topk"].top(), start=1)
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.bar_chart({r["Source IP"]: r["Estimated"] for r in rows})

with tab_acc:
    accuracy_tab.render(state)
with tab_perf:
    performance_tab.render(state)
with tab_mem:
    memory_tab.render(state)
with tab_anom:
    anomaly_tab.render(state)
