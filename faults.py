import random

def inject_fault(G, count=1):
    edges = list(G.edges())
    injected = []

    for _ in range(count):
        edge = random.choice(edges)
        G[edge[0]][edge[1]]["latency"] *= random.randint(3, 8)
        G[edge[0]][edge[1]]["packet_loss"] = random.uniform(15, 40)
        G[edge[0]][edge[1]]["fault"] = True
        injected.append(edge)

    return injected