"""Anomaly tab: flags sources that take an unusually large share of traffic."""
import streamlit as st

ALERT_SHARE = 0.10  # alert if one source exceeds 10% of all traffic.


def render(state):
    sketch, exact = state["sketch"], state["exact"]
    total = sketch.total
    st.subheader("Anomaly detection")
    st.write(
        f"A source is flagged when its estimated traffic exceeds "
        f"**{ALERT_SHARE:.0%}** of all {total:,} events."
    )

    threshold = st.slider("Alert threshold (% of traffic)", 1, 50, int(ALERT_SHARE * 100)) / 100
    flagged = [(ip, est) for ip, est in state["topk"].top() if est / total >= threshold]

    if flagged:
        for ip, est in flagged:
            st.error(
                f"🚨 ALERT: {ip} sent about {est:,} events "
                f"({est / total:.1%} of traffic). Exact count: {exact.counts.get(ip, 0):,}"
            )
    else:
        st.success("✅ No source exceeds the threshold. Traffic looks normal.")

    injected = state.get("anomaly_ip")
    if injected:
        top = state["topk"].top()
        ranked = [ip for ip, _ in top]
        if injected in ranked:
            st.info(f"Injected flood from {injected} detected at rank "
                    f"#{ranked.index(injected) + 1} in the top-{state['k']}.")
        else:
            st.warning(f"Injected flood from {injected} was NOT in the top-{state['k']}. "
                       "Try a larger flood size or a smaller epsilon.")
    else:
        st.caption("Tip: enable 'Inject flood' in the sidebar and rerun to see an alert.")
