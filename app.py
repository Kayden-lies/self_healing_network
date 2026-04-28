import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import numpy as np
import time
import random

from network import create_topology, shortest_path
from faults import inject_fault
from ai_model import detect_anomalies
from metrics import calculate_metrics
from utils import log_event

st.set_page_config(layout="wide")

# ---------------- UI STYLE ---------------- #
st.markdown("""
<style>
html, body {
    background: radial-gradient(circle at 20% 20%, #0f172a, #020617);
    color: #e2e8f0;
}

.stButton > button {
    background: linear-gradient(135deg, #06b6d4, #3b82f6);
    color: white;
    border-radius: 12px;
    padding: 10px 14px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ---------------- #
if "G" not in st.session_state:
    st.session_state.G = create_topology("Mesh")
    st.session_state.logs = []
    st.session_state.path = []
    st.session_state.explanation = ""

G = st.session_state.G

# ---------------- DEMO MODE ---------------- #
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    <div style="font-weight:600; font-size:16px;">
        Demo Mode
    </div>
    <div style="font-size:13px; color:#94a3b8; margin-top:4px;">
        Forces faults on active path to demonstrate visible rerouting behavior
    </div>
    """, unsafe_allow_html=True)

with col2:
    demo_mode = st.toggle("", label_visibility="collapsed")

# ---------------- HEALTH ---------------- #
def get_network_health(G):
    faults = sum(1 for u,v in G.edges() if G[u][v].get("fault"))
    anomalies = sum(1 for u,v in G.edges() if G[u][v].get("anomaly"))
    score = faults*2 + anomalies
    if score == 0:
        return "Healthy", "#22c55e"
    elif score < 3:
        return "Degraded", "#facc15"
    else:
        return "Critical", "#ef4444"

# ---------------- SAFE GRAPH ---------------- #
def get_safe_graph(G):
    H = G.copy()
    for u, v in H.edges():
        if H[u][v].get("fault") or H[u][v].get("anomaly"):
            H[u][v]["latency"] *= 10
    return H

# ---------------- FAULT ---------------- #
def inject_fault_on_path(G, path):
    if len(path) < 2:
        return None
    edge = random.choice(list(zip(path, path[1:])))
    G[edge[0]][edge[1]]["latency"] *= 5
    G[edge[0]][edge[1]]["packet_loss"] = 30
    G[edge[0]][edge[1]]["throughput"] *= 0.3
    G[edge[0]][edge[1]]["fault"] = True
    return edge

# ---------------- SIDEBAR ---------------- #
with st.sidebar:
    st.markdown("## Monitoring Console")

    metrics = calculate_metrics(G)

    st.metric("Latency", f"{metrics['avg_latency']:.1f} ms")
    st.metric("Packet Loss", f"{metrics['avg_loss']:.1f}%")
    st.metric("Throughput", f"{metrics['avg_throughput']:.1f}")

    status, color = get_network_health(G)
    st.markdown(f"<div style='color:{color};font-weight:600'>Status: {status}</div>", unsafe_allow_html=True)

    st.markdown("### Logs")
    for log in st.session_state.logs[:10]:
        st.caption(log)

# ---------------- HEADER ---------------- #
st.markdown("""
<h1>Network Self-Healing Dashboard</h1>
<p style='color:#94a3b8;'>AI-powered anomaly detection & autonomous rerouting</p>
""", unsafe_allow_html=True)

# ---------------- CONTROLS ---------------- #
nodes = list(G.nodes())

c1, c2, c3 = st.columns(3)

with c1:
    topology = st.selectbox("Topology", ["Mesh","Star","Ring","Tree","Random"])
    if st.button("Load Topology"):
        st.session_state.G = create_topology(topology)
        log_event(st.session_state.logs, f"{topology} loaded")
        st.session_state.path = []
        st.rerun()

with c2:
    source = st.selectbox("Source", nodes)
    target = st.selectbox("Destination", nodes)

with c3:
    st.write("")

a1, a2, a3, a4 = st.columns(4)

with a1:
    if st.button("Find Path"):
        safe_G = get_safe_graph(G)
        try:
            st.session_state.path = shortest_path(safe_G, source, target)
        except:
            st.session_state.path = []
        log_event(st.session_state.logs, "Path computed")
        st.rerun()

with a2:
    if st.button("Inject Fault"):
        if demo_mode and st.session_state.path:
            inject_fault_on_path(G, st.session_state.path)
        else:
            inject_fault(G, 2)
        log_event(st.session_state.logs, "Fault injected")
        st.rerun()

with a3:
    if st.button("Detect Anomaly"):
        anomalies, explanations = detect_anomalies(G)
        st.session_state.explanation = "\n".join(explanations)
        log_event(st.session_state.logs, f"Anomalies: {anomalies}")
        st.rerun()

with a4:
    if st.button("Self Heal"):
        G.remove_edges_from([(u,v) for u,v in G.edges() if G[u][v].get("fault")])
        log_event(st.session_state.logs, "Network healed")
        st.rerun()

# ---------------- AUTO PATH ---------------- #
safe_G = get_safe_graph(G)
try:
    st.session_state.path = shortest_path(safe_G, source, target)
except:
    st.session_state.path = []

# ---------------- GRAPH ---------------- #
pos = nx.spring_layout(G, seed=42)

def draw_graph(packet_positions=None):
    traces = []

    for u,v in G.edges():
        x0,y0 = pos[u]
        x1,y1 = pos[v]

        color = "gray"
        width = 2

        if G[u][v].get("fault"):
            color = "red"
            width = 5

        traces.append(go.Scatter(x=[x0,x1], y=[y0,y1], mode="lines", line=dict(color=color,width=width)))

    traces.append(go.Scatter(
        x=[pos[n][0] for n in G.nodes()],
        y=[pos[n][1] for n in G.nodes()],
        mode="markers+text",
        text=list(G.nodes()),
        textposition="middle center",
        marker=dict(size=25,color="#22d3ee")
    ))

    if packet_positions and st.session_state.path:
        path = st.session_state.path
        for p in packet_positions:
            i = int(p*(len(path)-1))
            t = (p*(len(path)-1))%1
            if i < len(path)-1:
                n1,n2 = path[i], path[i+1]
                x = pos[n1][0]*(1-t)+pos[n2][0]*t
                y = pos[n1][1]*(1-t)+pos[n2][1]*t
                traces.append(go.Scatter(x=[x],y=[y],mode="markers",marker=dict(size=10,color="#00ffff")))

    return go.Figure(traces)

st.markdown('<div class="glass">', unsafe_allow_html=True)
st.plotly_chart(draw_graph(), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- SIMULATION ---------------- #
if st.session_state.path:

    st.markdown("### Network Traffic Simulation")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        speed = st.slider("Speed", 0.01, 0.2, 0.05)

    with col2:
        step = st.slider("Step", 0.0, 1.0, 0.0)

    with col3:
        autoplay = st.toggle("Auto")

    placeholder = st.empty()
    base = np.linspace(0,1,5)

    if autoplay:
        for t in np.arange(0, 1, speed):
            packets = [(p + t) % 1 for p in base]

            with placeholder.container():
                st.plotly_chart(
                    draw_graph(packets),
                    use_container_width=True,
                    key=f"anim_{t}"
                )

            time.sleep(0.1)

    else:
        packets = [(p + step) % 1 for p in base]

        with placeholder.container():
            st.plotly_chart(
                draw_graph(packets),
                use_container_width=True,
                key=f"step_{step}"
            )
# ---------------- AI PANEL ---------------- #
st.markdown("### AI Analysis")
st.write(st.session_state.explanation or "No anomalies")

faults = sum(1 for u,v in G.edges() if G[u][v].get("fault"))
anomalies = sum(1 for u,v in G.edges() if G[u][v].get("anomaly"))
score = max(0,100-(faults*15+anomalies*10))

st.progress(score/100)
st.caption(f"Network Stability: {score}%")

# ---------------- LEGEND ---------------- #
st.markdown("""
### Legend
- Cyan → Packet flow  
- Red → Fault  
- Yellow → Anomaly  
""")
