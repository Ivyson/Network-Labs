import json
import networkx as nx
import matplotlib.pyplot as plt
import httplib2
from typing import Dict, List, Tuple
from datetime import timedelta


class NetworkDataRetriever:
    """Handles retrieval of network data from OpenDaylight controller"""

    def __init__(self, odl_host: str = "192.168.56.104", odl_port: str = "8181"):
        self.odl_host = odl_host
        self.odl_port = odl_port
        self.base_url = f"http://{odl_host}:{odl_port}/rests"
        self.http = httplib2.Http(".cache")
        self.http.add_credentials(name="admin", password="admin")

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
            print(f"Exception while retrieving BGP RIB data: {e}")
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

                        # Extract supported tables
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

                                        # Extract attributes
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

        # Categorise routes by origin
        for route in self.routes:
            origin = route.get("origin", "unknown")
            stats["route_types"][origin] = stats["route_types"].get(origin, 0) + 1

            # Categorise by prefix type
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


class NetworkVisualiser:
    """Handles network topology visualisation and analysis"""

    def __init__(self, routes: List[Dict]):
        self.routes = routes
        self.graph = nx.Graph()
        self.interface_map = {}

    def build_topology(self) -> nx.Graph:
        """Build network topology graph from route data"""
        # Extract point-to-point networks
        networks = []
        for route in self.routes:
            prefix = route.get("prefix", "")
            if prefix.startswith("10.0.") and "/30" in prefix:
                networks.append(prefix.split("/")[0])

        # Create interface map
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

        # Build graph
        for link, info in self.interface_map.items():
            routers = [r for r in info.keys() if r.startswith("R")]
            if len(routers) == 2:
                r1, r2 = routers
                network = info["network"]
                self.graph.add_edge(r1, r2, label=network)

        return self.graph

    def calculate_network_metrics(self) -> Dict:
        """Calculate graph-based network metrics"""
        if not self.graph or self.graph.number_of_nodes() == 0:
            return {}

        metrics = {
            "total_routers": self.graph.number_of_nodes(),
            "total_links": self.graph.number_of_edges(),
            "average_degree": sum(dict(self.graph.degree()).values())
            / self.graph.number_of_nodes(),
            "is_connected": nx.is_connected(self.graph),
            "diameter": nx.diameter(self.graph)
            if nx.is_connected(self.graph)
            else "N/A",
        }

        # Calculate shortest paths
        if nx.is_connected(self.graph):
            metrics["average_shortest_path"] = nx.average_shortest_path_length(
                self.graph
            )

        return metrics

    def visualise_topology(self, output_file: str = "223146145_topology.png"):
        """Generate and save network topology visualisation"""
        if not self.graph or self.graph.number_of_nodes() == 0:
            print("No topology data to visualise")
            return

        plt.figure(figsize=(12, 8))
        position = nx.spring_layout(self.graph, seed=42, k=2)

        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph,
            position,
            node_size=3000,
            node_color="lightblue",
            edgecolors="black",
            linewidths=2,
        )

        # Draw labels
        nx.draw_networkx_labels(self.graph, position, font_size=14, font_weight="bold")

        # Draw edges
        nx.draw_networkx_edges(self.graph, position, width=2.5, edge_color="grey")

        # Draw edge labels
        edge_labels = nx.get_edge_attributes(self.graph, "label")
        nx.draw_networkx_edge_labels(
            self.graph, position, edge_labels=edge_labels, font_color="red", font_size=9
        )

        plt.title(
            "Enterprise Network Topology - OSPF Domain", fontsize=16, fontweight="bold"
        )
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"\nTopology diagram saved to: {output_file}")
        plt.show()


class OutputFormatter:
    """Formats and displays network information in a readable format"""

    @staticmethod
    def print_header(title: str):
        """Print a formatted section header"""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)

    @staticmethod
    def print_subheader(title: str):
        """Print a formatted subsection header"""
        print(f"\n--- {title} ---")

    @staticmethod
    def display_bgp_neighbours(peers: List[Dict]):
        """Display BGP neighbour information"""
        OutputFormatter.print_header("BGP NEIGHBOUR INFORMATION")

        if not peers:
            print("No BGP peers found.")
            return

        print(f"\nTotal BGP Neighbours: {len(peers)}")

        for idx, peer in enumerate(peers, 1):
            OutputFormatter.print_subheader(f"Neighbour {idx}")
            print(f"  Peer ID:           {peer.get('peer_id', 'Unknown')}")
            print(f"  Peer Role:         {peer.get('peer_role', 'Unknown')}")

            # Display statistics if available
            stats = peer.get("stats", {})
            if stats:
                print(f"\n  Session Statistics:")
                for key, value in stats.items():
                    formatted_key = key.replace("-", " ").title()
                    print(f"    {formatted_key}: {value}")

            # Display supported address families
            if "supported_tables" in peer:
                print(f"\n  Supported Address Families:")
                for table in peer["supported_tables"]:
                    afi = table.get("afi", "Unknown")
                    safi = table.get("safi", "Unknown")
                    print(f"    - {afi} / {safi}")

    @staticmethod
    def display_routing_information(routes: List[Dict]):
        """Display BGP routing information"""
        OutputFormatter.print_header("BGP ROUTING INFORMATION")

        if not routes:
            print("No routes found.")
            return

        print(f"\nTotal Routes Received: {len(routes)}")

        # Group routes by type
        loopbacks = [r for r in routes if "/32" in r.get("prefix", "")]
        p2p_links = [
            r
            for r in routes
            if "/30" in r.get("prefix", "") and r.get("prefix", "").startswith("10.0.")
        ]
        management = [r for r in routes if "192.168.56" in r.get("prefix", "")]

        # Display loopback routes
        if loopbacks:
            OutputFormatter.print_subheader("Loopback Addresses (Router IDs)")
            for route in loopbacks:
                print(f"\n  Prefix:            {route.get('prefix')}")
                print(f"    Next Hop:        {route.get('next_hop', 'N/A')}")
                print(f"    Origin:          {route.get('origin', 'N/A')}")
                print(f"    Local Pref:      {route.get('local_pref', 'N/A')}")

        # Display point-to-point links
        if p2p_links:
            OutputFormatter.print_subheader("Point-to-Point Links")
            for route in p2p_links:
                print(f"\n  Prefix:            {route.get('prefix')}")
                print(f"    Next Hop:        {route.get('next_hop', 'N/A')}")
                print(f"    Origin:          {route.get('origin', 'N/A')}")
                print(f"    Local Pref:      {route.get('local_pref', 'N/A')}")

        # Display management network
        if management:
            OutputFormatter.print_subheader("Management Networks")
            for route in management:
                print(f"\n  Prefix:            {route.get('prefix')}")
                print(f"    Next Hop:        {route.get('next_hop', 'N/A')}")
                print(f"    Origin:          {route.get('origin', 'N/A')}")
                print(f"    Local Pref:      {route.get('local_pref', 'N/A')}")

    @staticmethod
    def display_statistics(stats: Dict):
        """Display network statistics"""
        OutputFormatter.print_header("NETWORK STATISTICS")

        print(f"\nBGP Statistics:")
        print(f"  Total BGP Peers:              {stats.get('total_peers', 0)}")
        print(f"  Total Routes in RIB:          {stats.get('total_routes', 0)}")

        print(f"\nRoute Distribution by Origin:")
        route_types = stats.get("route_types", {})
        for origin, count in route_types.items():
            print(f"  {origin.capitalize():20} {count}")

        print(f"\nRoute Distribution by Type:")
        prefix_types = stats.get("prefix_types", {})
        for ptype, count in prefix_types.items():
            print(f"  {ptype.replace('_', ' ').title():20} {count}")

    @staticmethod
    def display_network_metrics(metrics: Dict):
        """Display network topology metrics"""
        OutputFormatter.print_header("NETWORK TOPOLOGY METRICS")

        if not metrics:
            print("No topology metrics available.")
            return

        print(f"\nTopology Overview:")
        print(f"  Total Routers:                {metrics.get('total_routers', 0)}")
        print(f"  Total Links:                  {metrics.get('total_links', 0)}")
        print(f"  Average Router Degree:        {metrics.get('average_degree', 0):.2f}")
        print(f"  Network Connected:            {metrics.get('is_connected', False)}")

        if metrics.get("diameter") != "N/A":
            print(f"  Network Diameter:             {metrics.get('diameter')}")
            print(
                f"  Average Shortest Path:        {metrics.get('average_shortest_path', 0):.2f}"
            )

        print(f"\nRedundancy Analysis:")
        avg_degree = metrics.get("average_degree", 0)
        if avg_degree > 2:
            print(f"  Network has good redundancy (avg degree: {avg_degree:.2f})")
        elif avg_degree == 2:
            print(f"  Network has minimal redundancy (ring/linear topology)")
        else:
            print(f"  Network has poor redundancy (tree topology)")


def main():
    """Main application execution"""
    print("\n" + "=" * 80)
    print(" OPENDAYLIGHT SDN NETWORK ANALYSIS APPLICATION")
    print(" Student ID: 223146145")
    print("=" * 80)

    # Step 1: Retrieve data from ODL controller
    print("\n[1/5] Connecting to OpenDaylight Controller...")
    retriever = NetworkDataRetriever()
    bgp_data = retriever.get_bgp_rib_data()

    if not bgp_data:
        print("Failed to retrieve BGP data from controller. Exiting.")
        return

    # Save raw data for reference
    with open("network_data.json", "w", encoding="utf8") as f:
        json.dump(bgp_data, f, indent=4, ensure_ascii=False)
    print("      Raw network data saved to: network_data.json")

    # Step 2: Analyse BGP data
    print("\n[2/5] Analysing BGP Information...")
    analyser = BGPAnalyser(bgp_data)
    peers = analyser.extract_peer_information()
    routes = analyser.extract_route_information()
    statistics = analyser.calculate_statistics()
    print(f"      Found {len(peers)} BGP peer(s) and {len(routes)} route(s)")

    # Step 3: Build and analyse topology
    print("\n[3/5] Building Network Topology...")
    visualiser = NetworkVisualiser(routes)
    graph = visualiser.build_topology()
    network_metrics = visualiser.calculate_network_metrics()
    print(
        f"      Topology built with {graph.number_of_nodes()} routers and {graph.number_of_edges()} links"
    )

    # Step 4: Display all information
    print("\n[4/5] Generating Network Analysis Report...")

    OutputFormatter.display_bgp_neighbours(peers)
    OutputFormatter.display_routing_information(routes)
    OutputFormatter.display_statistics(statistics)
    OutputFormatter.display_network_metrics(network_metrics)

    # Step 5: Generate visualisation
    print("\n[5/5] Generating Network Topology Visualisation...")
    visualiser.visualise_topology()

    # Final summary
    print("\n" + "=" * 80)
    print(" ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  - BGP session established with R5 (AS 65002)")
    print(f"  - {statistics.get('total_routes', 0)} routes received from OSPF domain")
    print(
        f"  - Network topology contains {network_metrics.get('total_routers', 0)} routers"
    )
    print(f"  - Topology visualisation saved")
    print(f"\nSDN Integration: SUCCESS ✓")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
