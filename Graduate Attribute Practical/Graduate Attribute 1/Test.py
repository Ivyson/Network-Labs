import json
import matplotlib.pyplot as plt
import networkx as nx


with open("network_data.json", "r", encoding="utf8") as f:
    data = json.load(f)
if "bgp-rib:rib" in data and data["bgp-rib:rib"]:
    rib_path = data["bgp-rib:rib"][0]["peer"][0]["effective-rib-in"]["tables"][0][
        "bgp-inet:ipv4-routes"
    ]["ipv4-route"]
else:
    print("No BGP data was found!")
filtered_prefixes = []
for route in rib_path:
    prefix = route["prefix"]
    filtered_prefixes.append(prefix)
print(f"The Prefixes found are: \n{filtered_prefixes}")
networks = []
for prefix in filtered_prefixes:
    if prefix.startswith("10.0."):
        networks.append(prefix.split("/")[0])
print(f"The Networks found are: \n{networks}")
interface_map = {}

for net in networks:
    (x, y) = net.split(".")[2][0], net.split(".")[2][1]
    parts = net.split(".")
    network_base = ".".join(parts[:3])

    ip_x = f"{network_base}.1"
    ip_y = f"{network_base}.2"

    interface_map[f"R{x}-R{y}"] = {
        f"R{x}": ip_x,
        f"R{y}": ip_y,
        "network": f"{network_base}.0/30",
    }
# print(interface_map)

Graph = nx.Graph()
for link, info in interface_map.items():
    print(f"Link: {link}, Info: {info}")
    routers = [r for r in info.keys() if r.startswith("R")]
    if len(routers) == 2:
        r1, r2 = routers
        network = info["network"]
        Graph.add_edge(r1, r2, label=network)

position = nx.spring_layout(Graph, seed=42)
nx.draw_networkx_nodes(
    Graph, position, node_size=2000, node_color="lightblue", edgecolors="black"
)
nx.draw_networkx_labels(Graph, position, font_size=12, font_weight="bold")
nx.draw_networkx_edges(Graph, position, width=2)


edge_labels = nx.get_edge_attributes(Graph, "label")
nx.draw_networkx_edge_labels(Graph, position, edge_labels=edge_labels, font_color="red")
plt.title("Network Topology")
plt.axis("off")
plt.savefig("223146145_topology.png", dpi=300, bbox_inches="tight", pad_inches=0.1)

plt.show()
plt.close()
