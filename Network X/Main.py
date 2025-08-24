"""
This will sketch the router topology that we used for Dijsktra (Or whatever..)
"""

import networkx as nx
import matplotlib.pyplot as plt

# Step 1. Create the graph instance
Graph = nx.Graph()
# Step 2. Build the network Topology
"""
Add nodes from 0 to 5, connect them in a way shown in the practical manual. 
Asocciate each edge to a certain weight
Ensure that each node has a name attach to itself
"""
# Step 2.1 Add Nodes
Graph.add_nodes_from(range(6))
# Step 2.2. Add the edges
"""
0 Connected to 2, 5, 4
1 Connected to 3, 4
2 Connedcted to 5 and 0
3 Connected to 1 
4 Connected to 0, 1, 5
5 Connected to 0, 2, 4
"""
# Parameters: From point, To Point, Weight of the edge
# Step 2.3. Add Weights to the Edges, Format is (point1, point 2, weight_of_connection)
edges = [(0, 2, 4), (1, 3, 3), (2, 5, 10), (4, 1, 8), (5, 4, 2), (0, 4, 1), (0, 5, 10)]
# Use weighted  edges instead of just edges, to attach weights to each thing
Graph.add_weighted_edges_from(edges)
# Step 2.4 Add Positions of each node
positions = {
    0: (0.25, 0.8),
    1: (0.675, 0.45),
    2: (0.0, 0.75),
    3: (1.1, 0.25),
    4: (0.45, 0.55),
    5: (0.2, 0.5),
}

# Compute the shortest path

path = nx.shortest_path(Graph, source=3, target=4, weight="weight")

# short_edges = list(zip())
# print(list(zip(path[:-1], path[:1])))
print(f"the path: {path}")
edge_list = list(zip(path[:-1], path[1:]))
nx.draw(
    G=Graph,
    pos=positions,
    with_labels=True,
    font_weight="bold",
    node_color="blue",
    edge_color="black",
    node_size=200,
)
edge_labels = nx.get_edge_attributes(Graph, "weight")  # Get edge labels
nx.draw_networkx_edges(
    Graph, pos=positions, edgelist=edge_list, edge_color="red", width=2
)
edge_labels = nx.get_edge_attributes(Graph, "weight")
# print(edge_labels)
fixed_labels = {edge: f"C = {weight}" for edge, weight in edge_labels.items()}
# print(fixed_labels)
nx.draw_networkx_edge_labels(Graph, pos=positions, edge_labels=fixed_labels)
plt.show()
# the shortest Path from 0, to 3 is:
print(f"Shortest Path : {path}")
