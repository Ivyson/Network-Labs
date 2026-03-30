"""
While the main File is responsible for Querying the ODL
and getting the metadata from it, then printing the topology, we were then required to 
make the matplotlib graph to be interactive; that it, reflect the topological changes 
and reflect them on our plot immediately. This update does all of that natively without
importing from the main function. This is because, the implementation was done in a fast
paced environment, and the main code was not touched as at least it was a fail safe, which was working.
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyBboxPatch
import httplib2
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import deque


class NetworkDataRetriever:
    """Handles retrieval of network data from OpenDaylight controller"""

    def __init__(self, odl_host: str = "192.168.56.104", odl_port: str = "8181",password="admin", name="admin"):
        self.odl_host = odl_host
        self.odl_port = odl_port
        self.password = password
        self.name = name
        self.base_url = f"http://{odl_host}:{odl_port}/rests"
        self.http = httplib2.Http(".cache")
        self.http.add_credentials(name=self.name, password=self.password)

    def get_bgp_rib_data(self, rib_name: str = "bgp-to-r1") -> dict:
        """Retrieve BGP RIB data from ODL controller"""
        uri = f"{self.base_url}/data/bgp-rib:bgp-rib/rib={rib_name}?content=nonconfig"
        try:
            response, content = self.http.request(
                uri=uri, method="GET", headers={"content-type": "application/json"}
            )
            if response.status == 200:
                return json.loads(content)
            else:
                print(f"Error retrieving BGP RIB data: HTTP {response.status}")
                return {}
        except Exception as e:
            print(f"Exception found while retrieving BGP RIB data: {e}")
            return {}

    def get_topology_data(self) -> dict:
        """Retrieve network topology data"""
        uri = f"{self.base_url}/data/network-topology:network-topology"
        try:
            response, content = self.http.request(
                uri=uri, method="GET", headers={"content-type": "application/json"}
            )
            if response.status == 200:
                return json.loads(content)
            else:
                print(f"Error retrieving topology data: HTTP {response.status}")
                return {}
        except Exception as e:
            print(f"Exception while retrieving topology data: {e}")
            return {}


class BGPAnalyser:
    """Analyses BGP data and extracts meaningful information"""

    def __init__(self, bgp_data: dict):
        self.bgp_data = bgp_data
        self.peers = []
        self.routes = []

    def extract_peer_information(self) -> List[Dict]:
        """Extract BGP peer (neighbour) information"""
        peers_info = []

        try:
            if "bgp-rib:rib" in self.bgp_data and self.bgp_data["bgp-rib:rib"]:
                rib = self.bgp_data["bgp-rib:rib"][0]

                if "peer" in rib:
                    for peer in rib["peer"]:
                        peer_id = peer.get("peer-id", "Unknown")
                        peer_info = {
                            "peer_id": peer_id,
                            "peer_role": peer.get("peer-role", "Unknown"),
                            "stats": peer.get("stats", {}),
                        }

                        if "supported-tables" in peer:
                            peer_info["supported_tables"] = peer["supported-tables"]

                        peers_info.append(peer_info)

            self.peers = peers_info
            return peers_info
        except Exception as e:
            print(f"Error extracting peer information: {e}")
            return []

    def extract_route_information(self) -> List[Dict]:
        """Extract BGP route information"""
        routes_info = []

        try:
            if "bgp-rib:rib" in self.bgp_data and self.bgp_data["bgp-rib:rib"]:
                rib = self.bgp_data["bgp-rib:rib"][0]

                if "peer" in rib and len(rib["peer"]) > 0:
                    peer = rib["peer"][0]

                    if "effective-rib-in" in peer:
                        rib_in = peer["effective-rib-in"]

                        if "tables" in rib_in and len(rib_in["tables"]) > 0:
                            tables = rib_in["tables"][0]

                            if "bgp-inet:ipv4-routes" in tables:
                                ipv4_routes = tables["bgp-inet:ipv4-routes"]

                                if "ipv4-route" in ipv4_routes:
                                    for route in ipv4_routes["ipv4-route"]:
                                        route_info = {
                                            "prefix": route.get("prefix", "Unknown"),
                                            "path_id": route.get("path-id", 0),
                                        }

                                        if "attributes" in route:
                                            attrs = route["attributes"]
                                            route_info["origin"] = attrs.get(
                                                "origin", {}
                                            ).get("value", "Unknown")

                                            if "ipv4-next-hop" in attrs:
                                                route_info["next_hop"] = attrs[
                                                    "ipv4-next-hop"
                                                ].get("global", "Unknown")

                                            if "local-pref" in attrs:
                                                route_info["local_pref"] = attrs[
                                                    "local-pref"
                                                ].get("pref", 0)

                                            if "as-path" in attrs:
                                                route_info["as_path"] = attrs["as-path"]

                                        routes_info.append(route_info)

            self.routes = routes_info
            return routes_info
        except Exception as e:
            print(f"Error extracting route information: {e}")
            return []

    def calculate_statistics(self) -> Dict:
        """Calculate network statistics from BGP data"""
        stats = {
            "total_peers": len(self.peers),
            "total_routes": len(self.routes),
            "route_types": {},
            "prefix_types": {
                "loopback": 0,
                "point_to_point": 0,
                "management": 0,
                "other": 0,
            },
        }

        for route in self.routes:
            origin = route.get("origin", "unknown")
            stats["route_types"][origin] = stats["route_types"].get(origin, 0) + 1

            prefix = route.get("prefix", "")
            if "/32" in prefix:
                stats["prefix_types"]["loopback"] += 1
            elif "/30" in prefix and prefix.startswith("10.0."):
                stats["prefix_types"]["point_to_point"] += 1
            elif "192.168.56" in prefix:
                stats["prefix_types"]["management"] += 1
            else:
                stats["prefix_types"]["other"] += 1

        return stats


class DynamicNetworkVisualiser:
    """Handles real-time network topology visualisation with animation"""

    def __init__(self, retriever: NetworkDataRetriever, update_interval: int = 30):
        self.retriever = retriever
        self.update_interval = update_interval
        self.graph = nx.Graph()
        self.interface_map = {}
        self.position = None

        # Track metrics over time
        self.route_history = deque(maxlen=20)
        self.peer_history = deque(maxlen=20)
        self.timestamp_history = deque(maxlen=20)

        # Animation state
        self.last_update = datetime.now()
        self.update_counter = 0
        self.connection_status = "Initializing..."

        # Figure setup
        self.fig = plt.figure(figsize=(16, 10))
        self.gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Main topology plot
        self.ax_topo = self.fig.add_subplot(self.gs[:2, :2])

        # Statistics plots
        self.ax_routes = self.fig.add_subplot(self.gs[0, 2])
        self.ax_peers = self.fig.add_subplot(self.gs[1, 2])
        self.ax_info = self.fig.add_subplot(self.gs[2, :])
        self.ax_info.axis("off")

    def build_topology(self, routes: List[Dict]) -> nx.Graph:
        """Build network topology graph from route data"""
        self.graph.clear()
        self.interface_map.clear()

        networks = []
        for route in routes:
            prefix = route.get("prefix", "")
            if prefix.startswith("10.0.") and "/30" in prefix:
                networks.append(prefix.split("/")[0])

        for net in networks:
            parts = net.split(".")
            if len(parts) >= 3 and len(parts[2]) >= 2:
                x, y = parts[2][0], parts[2][1]
                network_base = ".".join(parts[:3])
                ip_x = f"{network_base}.1"
                ip_y = f"{network_base}.2"

                self.interface_map[f"R{x}-R{y}"] = {
                    f"R{x}": ip_x,
                    f"R{y}": ip_y,
                    "network": f"{network_base}.0/30",
                }

        for link, info in self.interface_map.items():
            routers = [r for r in info.keys() if r.startswith("R")]
            if len(routers) == 2:
                r1, r2 = routers
                network = info["network"]
                self.graph.add_edge(r1, r2, label=network)

        # Initialize or maintain consistent layout
        if self.position is None and self.graph.number_of_nodes() > 0:
            self.position = nx.spring_layout(self.graph, seed=42, k=2)

        return self.graph

    def update_plot(self, frame):
        """Animation update function called at each interval"""
        current_time = datetime.now()
        time_since_update = (current_time - self.last_update).total_seconds()

        # Update data every interval
        if time_since_update >= self.update_interval or frame == 0:
            print(
                f"\n[Update {self.update_counter + 1}] Fetching data at {current_time.strftime('%H:%M:%S')}..."
            )

            # Retrieve fresh data
            bgp_data = self.retriever.get_bgp_rib_data()

            if bgp_data:
                analyser = BGPAnalyser(bgp_data)
                peers = analyser.extract_peer_information()
                routes = analyser.extract_route_information()
                stats = analyser.calculate_statistics()

                # Update history
                self.route_history.append(stats["total_routes"])
                self.peer_history.append(stats["total_peers"])
                self.timestamp_history.append(current_time)

                # Build topology
                self.build_topology(routes)

                self.connection_status = (
                    f"✓ Connected - Last Update: {current_time.strftime('%H:%M:%S')}"
                )
                self.last_update = current_time
                self.update_counter += 1

                print(
                    f"    Routes: {stats['total_routes']}, Peers: {stats['total_peers']}, Routers: {self.graph.number_of_nodes()}"
                )
            else:
                self.connection_status = (
                    f"✗ Connection Failed - {current_time.strftime('%H:%M:%S')}"
                )

        # Clear all axes
        self.ax_topo.clear()
        self.ax_routes.clear()
        self.ax_peers.clear()
        self.ax_info.clear()
        self.ax_info.axis("off")

        # Draw topology
        self._draw_topology()

        # Draw statistics
        self._draw_route_history()
        self._draw_peer_history()

        # Draw info panel
        self._draw_info_panel()

        return []

    def _draw_topology(self):
        """Draw the network topology"""
        if not self.graph or self.graph.number_of_nodes() == 0:
            self.ax_topo.text(
                0.5,
                0.5,
                "No Topology Data\nWaiting for BGP updates...",
                ha="center",
                va="center",
                fontsize=14,
                color="gray",
            )
            self.ax_topo.set_xlim(0, 1)
            self.ax_topo.set_ylim(0, 1)
            self.ax_topo.axis("off")
            return

        # Calculate node colors based on degree (connectivity)
        node_degrees = dict(self.graph.degree())
        max_degree = max(node_degrees.values()) if node_degrees else 1
        node_colors = [
            "#FF6B6B" if node_degrees[node] == max_degree else "#4ECDC4"
            for node in self.graph.nodes()
        ]

        # Draw nodes with pulsing effect
        pulse = 1.0 + 0.1 * abs(plt.np.sin(self.update_counter * 0.5))
        nx.draw_networkx_nodes(
            self.graph,
            self.position,
            node_size=3000 * pulse,
            node_color=node_colors,
            edgecolors="black",
            linewidths=2.5,
            ax=self.ax_topo,
        )

        # Draw labels
        nx.draw_networkx_labels(
            self.graph, self.position, font_size=12, font_weight="bold", ax=self.ax_topo
        )

        # Draw edges with gradient effect
        edge_colors = [
            "#95E1D3" if i % 2 == 0 else "#A8E6CF"
            for i in range(self.graph.number_of_edges())
        ]
        nx.draw_networkx_edges(
            self.graph,
            self.position,
            width=2.5,
            edge_color=edge_colors,
            ax=self.ax_topo,
        )

        # Draw edge labels
        edge_labels = nx.get_edge_attributes(self.graph, "label")
        nx.draw_networkx_edge_labels(
            self.graph,
            self.position,
            edge_labels=edge_labels,
            font_color="red",
            font_size=8,
            ax=self.ax_topo,
        )

        self.ax_topo.set_title(
            f"Live Network Topology - OSPF Domain\nUpdate #{self.update_counter}",
            fontsize=14,
            fontweight="bold",
            pad=20,
        )
        self.ax_topo.axis("off")

    def _draw_route_history(self):
        """Draw route count history chart"""
        if len(self.route_history) < 2:
            self.ax_routes.text(
                0.5, 0.5, "Collecting Data...", ha="center", va="center", fontsize=10
            )
            self.ax_routes.set_xlim(0, 1)
            self.ax_routes.set_ylim(0, 1)
            return

        x = range(len(self.route_history))
        self.ax_routes.plot(
            x,
            list(self.route_history),
            marker="o",
            color="#FF6B6B",
            linewidth=2,
            markersize=6,
        )
        self.ax_routes.fill_between(
            x, list(self.route_history), alpha=0.3, color="#FF6B6B"
        )
        self.ax_routes.set_title("Routes Over Time", fontsize=11, fontweight="bold")
        self.ax_routes.set_ylabel("Route Count", fontsize=9)
        self.ax_routes.grid(True, alpha=0.3)
        self.ax_routes.set_xlabel("Updates", fontsize=9)

    def _draw_peer_history(self):
        """Draw peer count history chart"""
        if len(self.peer_history) < 2:
            self.ax_peers.text(
                0.5, 0.5, "Collecting Data...", ha="center", va="center", fontsize=10
            )
            self.ax_peers.set_xlim(0, 1)
            self.ax_peers.set_ylim(0, 1)
            return

        x = range(len(self.peer_history))
        self.ax_peers.plot(
            x,
            list(self.peer_history),
            marker="s",
            color="#4ECDC4",
            linewidth=2,
            markersize=6,
        )
        self.ax_peers.fill_between(
            x, list(self.peer_history), alpha=0.3, color="#4ECDC4"
        )
        self.ax_peers.set_title("BGP Peers Over Time", fontsize=11, fontweight="bold")
        self.ax_peers.set_ylabel("Peer Count", fontsize=9)
        self.ax_peers.grid(True, alpha=0.3)
        self.ax_peers.set_xlabel("Updates", fontsize=9)

    def _draw_info_panel(self):
        """Draw information panel with current statistics"""
        info_text = f"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  OPENDAYLIGHT SDN NETWORK MONITOR - Student ID: 223146145                                           │
│  Status: {self.connection_status:<82} │
│  Next Update In: {max(0, self.update_interval - int((datetime.now() - self.last_update).total_seconds()))} seconds{" " * 68}│
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Current Statistics:                                                                                 │
│    • Active Routers: {self.graph.number_of_nodes():<3}  • Network Links: {self.graph.number_of_edges():<3}  • Total Routes: {self.route_history[-1] if self.route_history else 0:<3}  • BGP Peers: {self.peer_history[-1] if self.peer_history else 0:<3}{" " * 29}│
│    • Updates Completed: {self.update_counter:<3}  • Monitoring Since: {self.timestamp_history[0].strftime("%H:%M:%S") if self.timestamp_history else "N/A":<8}{" " * 37}│
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
        """

        self.ax_info.text(
            0.05,
            0.5,
            info_text,
            fontfamily="monospace",
            fontsize=9,
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="#F0F0F0", alpha=0.8),
        )

    def start_monitoring(self):
        """Start the dynamic monitoring visualization"""
        print("\n" + "=" * 80)
        print(" STARTING DYNAMIC SDN NETWORK MONITOR")
        print(f" Update Interval: {self.update_interval} seconds")
        print("=" * 80)

        # Create animation
        anim = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            interval=1000,  # Update display every second
            blit=False,
            cache_frame_data=False,
        )

        plt.tight_layout()
        plt.show()

        return anim


def main():
    """Main application execution"""
    print("\n" + "=" * 80)
    print(" DYNAMIC OPENDAYLIGHT SDN NETWORK ANALYSIS")
    print(" Student ID: 223146145")
    print("=" * 80)

    # Initialize retriever
    retriever = NetworkDataRetriever()

    # Create and start dynamic visualiser
    # Update every 30 seconds
    visualiser = DynamicNetworkVisualiser(retriever, update_interval=30)
    visualiser.start_monitoring()


if __name__ == "__main__":
    main()
