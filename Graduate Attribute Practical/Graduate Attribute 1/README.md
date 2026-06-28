# OpenDaylight SDN Network Analysis Application

This folder contains MY Graduate Attribute 1 practical solution for the SDN integration project using OpenDaylight (ODL) in Network Systems 3. The main application is in `main.py` and performs the following operations:
- BGP RIB retrieval from ODL
- BGP peer and route analysis
- Topology inference from BGP/OSPF route prefixes
- Network metrics calculation (connectivity, diameter, average degree, shortest path)
- Visual topology graph generation (`.png` output)
Bare in mind that the `main.py` file does not provide real time changes of the Network topology, If real time chanegs are require, change the implimantation from a static drawing to a continious animation, which makes use of `Matplotlib`'s animation to refresh the data after a second and if the router stops replying, then we assume its down or disconnected(Either intentionally or not).

> Note: This repo uses the my student details for confirming identity and to ensure that i ddi not copy the work of my peers, If you would like to change it, Do so. Also, an ODL connection was assigned to Port `192.168.56.104:8181` with credentials `admin/admin`.

## Requirements
This was implemented in `Python 3.13` and should work well with Previous Python up to `Python 3.12/10`. And the packages heavily used in this implementation, are:
- `httplib2`
- `networkx`
- `matplotlib`
To test the code, you can clone the repo to your environment, and navigate to the repository,Then Install dependencies:
```bash
git clone https://github.com/Ivyson/Network-Labs.git
cd "Graduate Attribute Practical"
cd "Graduate Attribute 1"
uv sync
uv run main.py
```
Luckily if you are using `uv`, it will automatically pull the imports into your virtual environment and execute the code instantly.
Sadly, this will have to pull all of the codebase in this repo...
## Files
- `main.py`: main script and implementation classes
- `network_data.json`: runtime artifact (saved JSON BGP RIB data)

## Architecture
`main.py` contains:
1. `NetworkDataRetriever` - HTTP requests to ODL RESTCONF
   - `get_bgp_rib_data(rib_name='bgp-to-r1')`
   - `get_topology_data()` (present but not used in this version)
2. `BGPAnalyser` - parse BGP JSON
   - `extract_peer_information()`
   - `extract_route_information()`
   - `calculate_statistics()`
3. `NetworkVisualiser` - infer topology from `10.0.x.0/30` prefixes
   - `build_topology()`
   - `calculate_network_metrics()`
   - `visualise_topology(output_file='223146145_topology.png')`
4. `OutputFormatter` - friendly CLI reporting
   - BGP neighbours, routes, statistics, network metrics
5. `main()` - orchestrates steps (retrieve, analyse, build, print, visualise)

## Usage
1. Start OpenDaylight controller and ensure it can reach your GNS3 routers.
2. Set up the controller with BGP route leakage into `bgp-to-r1` RIB.
3. Launch:
```bash
uv run main.py
```
4. The app writes `network_data.json` and topology image `223146145_topology.png`.

## Expected output
- Console sections: BGP NEIGHBOUR INFORMATION, BGP ROUTING INFORMATION, NETWORK STATISTICS, NETWORK TOPOLOGY METRICS
- Summary includes peer (R5) BGP session status, route counts, router count.
- If no BGP data available, exits gracefully.

## Troubleshooting
- If unable to connect: verify ODL host/port, credentials, and that RESTCONF service is reachable.
- If BGP RIB is empty: inspect ODL `bgp-rib` datastore and verify `rib=bgp-to-r1` exists.
- If visualisation fails: ensure route prefixes include `10.0.x.0/30` to infer links.

## Extending the project
- Add topology discovery from `get_topology_data()` and `network-topology` model.
- Support IPv6 (`bgp-inet:ipv6-routes`) in analyser.
- Add CLI args for ODL host/port, credentials, and output names.
