import json

with open("network_data.json", "r") as file:
    data = json.load(file)
# print(data)
rib_session = data["bgp-rib:rib"]
# print(rib_session[0])
peer = rib_session[0]["peer"][0]["effective-rib-in"]
# print(peer)
tables = peer["tables"][0]
# print(tables)
inet = tables["bgp-inet:ipv4-routes"]
# print(inet)
ipv4 = inet["ipv4-route"]
# print(len(ipv4))
# print(ipv4[1])
networks = []
for network in ipv4:
    networks.append(network["prefix"])

final_networks = [net for net in networks if net.startswith("10.0")]
print(final_networks)
