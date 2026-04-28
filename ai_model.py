import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(G):
    data = []
    edges = list(G.edges())

    for u, v in edges:
        attrs = G[u][v]
        data.append([
            attrs["latency"],
            attrs["packet_loss"],
            attrs["throughput"]
        ])

    model = IsolationForest(contamination=0.25)
    preds = model.fit_predict(data)

    anomalies = []
    explanations = []

    for i, p in enumerate(preds):
        if p == -1:
            edge = edges[i]
            anomalies.append(edge)
            G[edge[0]][edge[1]]["anomaly"] = True

            explanations.append(
                f"Edge {edge} shows abnormal latency/packet loss pattern"
            )

    return anomalies, explanations