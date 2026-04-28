def calculate_metrics(G):
    lat = []
    loss = []
    thr = []

    for u, v in G.edges():
        lat.append(G[u][v]["latency"])
        loss.append(G[u][v]["packet_loss"])
        thr.append(G[u][v]["throughput"])

    return {
        "avg_latency": sum(lat)/len(lat),
        "avg_loss": sum(loss)/len(loss),
        "avg_throughput": sum(thr)/len(thr)
    }