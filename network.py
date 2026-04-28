import networkx as nx
import random
import string

def generate_labels(n):
    return list(string.ascii_uppercase[:n])

def create_topology(topology, n=8):
    labels = generate_labels(n)

    if topology == "Star":
        G = nx.star_graph(n-1)
    elif topology == "Mesh":
        G = nx.complete_graph(n)
    elif topology == "Ring":
        G = nx.cycle_graph(n)
    elif topology == "Tree":
        G = nx.balanced_tree(2, 3)
    elif topology == "Random":
        G = nx.erdos_renyi_graph(n, 0.4)
    else:
        G = nx.path_graph(n)

    mapping = {node: labels[i] for i, node in enumerate(G.nodes())}
    G = nx.relabel_nodes(G, mapping)

    for u, v in G.edges():
        G[u][v]["latency"] = random.randint(5, 50)
        G[u][v]["packet_loss"] = random.uniform(0, 5)
        G[u][v]["throughput"] = random.randint(50, 100)

    return G


def shortest_path(G, source, target):
    return nx.dijkstra_path(G, source, target, weight="latency")