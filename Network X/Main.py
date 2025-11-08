
import networkx as nx
import matplotlib.pyplot as plt

# Step 1: Create Graph
G = nx.Graph()

# Step 2: Add Routers (Nodes)
routers = ["R1", "R2", "R3", "R4", "R5", "R6"]
G.add_nodes_from(routers)

# Step 3: Define Edges (connections) with weights
edges = [
    ("R1", "R2", 1),
    ("R2", "R3", 2),
    ("R3", "R4", 3),
    ("R4", "R5", 2),
    ("R5", "R6", 4),
    ("R6", "R1", 5),
]

G.add_weighted_edges_from(edges)

# Step 4: Define node positions (hexagon / circular layout)
positions = {
    "R1": (0, 1),       # top
    "R2": (0.87, 0.5),  # upper-right
    "R3": (0.87, -0.5), # lower-right
    "R4": (0, -1),      # bottom
    "R5": (-0.87, -0.5),# lower-left
    "R6": (-0.87, 0.5), # upper-left
}

# Step 5: Compute Shortest Path Example
source = "R1"
target = "R4"
shortest_path = nx.shortest_path(G, source=source, target=target, weight="weight")

# Step 6: Draw the Graph
plt.figure(figsize=(7, 7))
nx.draw(
    G,
    pos=positions,
    with_labels=True,
    node_size=1500,
    node_color="skyblue",
    font_size=10,
    font_weight="bold",
    edge_color="black"
)

# Highlight the shortest path in red
path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))
nx.draw_networkx_edges(G, pos=positions, edgelist=path_edges, edge_color="red", width=2)

# Add edge weights
edge_labels = nx.get_edge_attributes(G, "weight")
formatted_labels = {edge: f"C = {weight}" for edge, weight in edge_labels.items()}
nx.draw_networkx_edge_labels(G, pos=positions, edge_labels=formatted_labels, font_size=8)

plt.title(f"Router Topology (Shortest Path: {shortest_path})", fontsize=12)
plt.axis("off")
plt.show()

# Step 7: Print Path Info
print(f"Shortest path from {source} to {target}: {shortest_path}")

