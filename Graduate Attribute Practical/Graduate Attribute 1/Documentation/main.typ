#align(center)[
= VyOS 5-Network Topology Configuration Notes
]

This document provides annotated configurations for a five-router GNS3 topology using VyOS.  
Routers R1–R4 form a single internal Autonomous System (AS) that runs OSPF.  
Router R5 belongs to an external AS and connects to R2 via BGP, redistributing routes between BGP and OSPF to facilitate communication with the Ubuntu VM hosting OpenDaylight (ODL).

== Topology Overview
#table(
  columns: 4,
  table.header([Router], [Protocol], [Peer Connections], [Description]),
  [R1], [OSPF], [R2, R3], [Internal router, AS: 65001],
  [R2], [OSPF + BGP], [R1, R4, R5], [AS border router, redistributes OSPF ↔ BGP],
  [R3], [OSPF], [R1, R4], [Internal router, AS: 65001],
  [R4], [OSPF], [R2, R3], [Internal router, AS: 65001],
  [R5], [BGP], [R2, Cloud (ODL)], [External router, AS: 65002],
)



== Address Plan

#table(
  columns: 4,
  table.header([Link], [Network], [Subnet], [Devices]),
  [R1–R2], [10.0.12.0/30], [10.0.12.1 ↔ 10.0.12.2], [Internal link],
  [R1–R3], [10.0.13.0/30], [10.0.31.2 ↔ 10.0.31.1], [Internal link],
  [R2–R4], [10.0.24.0/30], [10.0.24.1 ↔ 10.0.24.2], [Internal link],
  [R3–R4], [10.0.34.0/30], [10.0.34.1 ↔ 10.0.34.2], [Internal link],
  [R2–R5], [10.0.25.0/30], [10.0.25.1 ↔ 10.0.25.2], [External link],
  [R5–ODL], [192.168.100.0/30], [192.168.100.2 ↔ 192.168.100.1], [Cloud link],
)

== R1 Configuration

```bash
vyos@R1:~$ show configuration commands
set interfaces ethernet eth0 address '10.0.12.1/30'
set interfaces ethernet eth0 hw-id '08:00:27:65:13:a0'
set interfaces ethernet eth1 address '10.0.31.2/30'
set interfaces ethernet eth1 hw-id '08:00:27:2c:35:8f'
set interfaces ethernet eth2 hw-id '08:00:27:70:69:84'
set interfaces ethernet eth3 hw-id '08:00:27:df:01:2d'
set interfaces loopback lo address '192.168.2.1/32'
set protocols bgp address-family ipv4-unicast network 192.168.2.1/32
set protocols bgp neighbor 192.168.56.1 address-family ipv4-unicast
set protocols bgp neighbor 192.168.56.1 description 'R5 to eBGP'
set protocols bgp neighbor 192.168.56.1 ebgp-multihop '2'
set protocols bgp neighbor 192.168.56.1 remote-as '65002'
set protocols bgp neighbor 192.168.56.1 timers holdtime '90'
set protocols bgp neighbor 192.168.56.1 update-source 'lo'
set protocols bgp parameters router-id '192.168.2.1'
set protocols bgp system-as '65001'
set protocols ospf area 0 network '10.0.31.0/30'
set protocols ospf area 0 network '10.0.12.0/30'
set protocols ospf area 0 network '192.168.2.1/32'
set protocols ospf parameters router-id '192.168.2.1'
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R1'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGAL8rhVQxTg0oAG9/q11h/'
set system login user vyos authentication plaintext-password ''
set system option reboot-on-upgrade-failure '5'
set system syslog local facility all level 'info'
set system syslog local facility local7 level 'debug'
vyos@R1:~$

```

=== Annotation:
R1 acts as an internal router connected to R2 and R3.  
The configuration activates OSPF for the subnets linking R2 and R3, enabling intra-AS route exchange.

== R2 Configuration

```bash
vyos@R2:~$ show configuration commands
set interfaces ethernet eth0 address '10.0.24.1/30'
set interfaces ethernet eth0 hw-id '08:00:27:ed:01:11'
set interfaces ethernet eth1 address '10.0.12.2/30'
set interfaces ethernet eth1 hw-id '08:00:27:7b:74:b9'
set interfaces ethernet eth2 address '10.0.25.1/30'
set interfaces ethernet eth2 hw-id '08:00:27:86:6c:5c'
set interfaces ethernet eth3 hw-id '08:00:27:ec:b3:6f'
set interfaces loopback lo address '192.168.2.2/32'
set protocols bgp address-family ipv4-unicast network 192.168.2.2/32
set protocols bgp neighbor 10.0.25.2 address-family ipv4-unicast
set protocols bgp neighbor 10.0.25.2 remote-as '65002'
set protocols bgp neighbor 10.0.25.2 timers connect '10'
set protocols bgp neighbor 10.0.25.2 timers holdtime '90'
set protocols bgp parameters router-id '192.168.2.2'
set protocols bgp system-as '65001'
set protocols ospf area 0 network '10.0.12.0/30'
set protocols ospf area 0 network '10.0.24.0/30'
set protocols ospf area 0 network '10.0.25.0/30'
set protocols ospf area 0 network '192.168.2.2/32'
set protocols ospf parameters router-id '192.168.2.2'
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R2'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGAL8rhVQxTg0oAG9/q11h/'
set system login user vyos authentication plaintext-password ''
set system option reboot-on-upgrade-failure '5'
set system syslog local facility all level 'info'
set system syslog local facility local7 level 'debug'
vyos@R2:~$
```

=== Annotation:
R2 connects the internal OSPF domain (AS 65001) to external BGP (AS 65002).  
It redistributes OSPF routes into BGP for advertisement to R5 and receives BGP routes from R5 for internal redistribution.

== R3 Configuration

```bash
vyos@R3:~$ show configuration commands
set interfaces ethernet eth0 address '10.0.31.1/30'
set interfaces ethernet eth0 hw-id '08:00:27:81:89:47'
set interfaces ethernet eth1 address '10.0.34.1/30'
set interfaces ethernet eth1 hw-id '08:00:27:76:d3:ff'
set interfaces ethernet eth2 hw-id '08:00:27:64:7e:ac'
set interfaces ethernet eth3 hw-id '08:00:27:55:a3:03'
set interfaces loopback lo address '192.168.2.3/32'
set protocols bgp address-family ipv4-unicast network 192.168.2.3/32
set protocols bgp neighbor 192.168.56.1 address-family ipv4-unicast
set protocols bgp neighbor 192.168.56.1 description 'R5 eBGP'
set protocols bgp neighbor 192.168.56.1 ebgp-multihop '2'
set protocols bgp neighbor 192.168.56.1 remote-as '65002'
set protocols bgp neighbor 192.168.56.1 timers holdtime '90'
set protocols bgp neighbor 192.168.56.1 update-source 'lo'
set protocols bgp parameters router-id '192.168.2.3'
set protocols bgp system-as '65001'
set protocols ospf area 0 network '10.0.31.0/30'
set protocols ospf area 0 network '10.0.34.0/30'
set protocols ospf area 0 network '192.168.2.3/32'
set protocols ospf parameters router-id '192.168.2.3'
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R3'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGAL8rhVQxTg0oAG9/q11h/'
set system login user vyos authentication plaintext-password ''
set system option reboot-on-upgrade-failure '5'
set system syslog local facility all level 'info'
set system syslog local facility local7 level 'debug'
vyos@R3:~$
```

=== Annotation:
R3 forms part of the OSPF mesh, linking R1 and R4.  
It ensures redundancy within the internal AS for better convergence and route distribution.

== R4 Configuration

```bash
vyos@R4:~$ show configuration commands
set interfaces ethernet eth0 address '10.0.32.2/30'
set interfaces ethernet eth0 hw-id '08:00:27:81:df:a4'
set interfaces ethernet eth1 address '10.0.24.2/30'
set interfaces ethernet eth1 hw-id '08:00:27:4f:50:96'
set interfaces ethernet eth2 hw-id '08:00:27:fc:24:a2'
set interfaces ethernet eth3 hw-id '08:00:27:14:bf:a7'
set interfaces loopback lo address '192.168.2.4/32'
set protocols bgp address-family ipv4-unicast network 192.168.2.4/32
set protocols bgp neighbor 192.168.56.1 address-family ipv4-unicast
set protocols bgp neighbor 192.168.56.1 description 'R5 eBGP'
set protocols bgp neighbor 192.168.56.1 ebgp-multihop '2'
set protocols bgp neighbor 192.168.56.1 remote-as '65002'
set protocols bgp neighbor 192.168.56.1 timers holdtime '90'
set protocols bgp neighbor 192.168.56.1 update-source 'lo'
set protocols bgp parameters router-id '192.168.2.4'
set protocols bgp system-as '65001'
set protocols ospf area 0 network '10.0.24.0/30'
set protocols ospf area 0 network '10.0.34.0/30'
set protocols ospf area 0 network '192.168.2.4/32'
set protocols ospf parameters router-id '192.168.0.4'
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R4'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGAL8rhVQxTg0oAG9/q11h/'
set system login user vyos authentication plaintext-password ''
set system option reboot-on-upgrade-failure '5'
set system syslog local facility all level 'info'
set system syslog local facility local7 level 'debug'

```

=== Annotation:
R4 acts as an OSPF router connecting R2 and R3.  
This dual connection maintains link resilience and balanced path selection within the OSPF domain.

== R5 Configuration

```bash
vyos@R5:~$ show configuration commands
set interfaces ethernet eth0 address '10.0.25.2/30'
set interfaces ethernet eth0 hw-id '08:00:27:9c:c8:48'
set interfaces ethernet eth1 address '192.168.56.1/24'
set interfaces ethernet eth1 hw-id '08:00:27:f4:a8:fe'
set interfaces ethernet eth2 hw-id '08:00:27:03:ff:03'
set interfaces ethernet eth3 hw-id '08:00:27:23:db:14'
set interfaces loopback lo address '192.168.1.1/32'
set protocols bgp address-family ipv4-unicast network 192.168.1.1/32
set protocols bgp address-family ipv4-unicast redistribute connected
set protocols bgp address-family ipv4-unicast redistribute ospf
set protocols bgp neighbor 192.168.2.2 address-family ipv4-unicast
set protocols bgp neighbor 192.168.2.2 description 'R2 eBGP'
set protocols bgp neighbor 192.168.2.2 ebgp-multihop '2'
set protocols bgp neighbor 192.168.2.2 remote-as '65001'
set protocols bgp neighbor 192.168.2.2 timers holdtime '90'
set protocols bgp neighbor 192.168.2.2 update-source 'lo'
set protocols bgp neighbor 192.168.56.104 address-family ipv4-unicast
set protocols bgp neighbor 192.168.56.104 description 'ODL iBGP'
set protocols bgp neighbor 192.168.56.104 port '1790'
set protocols bgp neighbor 192.168.56.104 remote-as '65002'
set protocols bgp neighbor 192.168.56.104 timers connect '10'
set protocols bgp neighbor 192.168.56.104 timers holdtime '90'
set protocols bgp parameters router-id '192.168.56.1'
set protocols bgp system-as '65002'
set protocols ospf area 0 network '192.168.1.1/32'
set protocols ospf area 0 network '10.0.25.0/30'
set protocols ospf parameters router-id '192.168.56.1'
set protocols ospf redistribute bgp
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set service snmp community public authorization 'ro'
set service ssh
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R5'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGAL8rhVQxTg0oAG9/q1:
set protocols bgp system-as '65002'
set protocols ospf area 0 network '192.168.1.1/32'
set protocols ospf area 0 network '10.0.25.0/30'
set protocols ospf parameters router-id '192.168.56.1'
set protocols ospf redistribute bgp
set service ntp allow-client address '127.0.0.0/8'
set service ntp allow-client address '169.254.0.0/16'
set service ntp allow-client address '10.0.0.0/8'
set service ntp allow-client address '172.16.0.0/12'
set service ntp allow-client address '192.168.0.0/16'
set service ntp allow-client address '::1/128'
set service ntp allow-client address 'fe80::/10'
set service ntp allow-client address 'fc00::/7'
set service ntp server time1.vyos.net
set service ntp server time2.vyos.net
set service ntp server time3.vyos.net
set service snmp community public authorization 'ro'
set service ssh
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'R5'
set system login user vyos authentication encrypted-password '$6$QxPS.uk6mfo$9QBSo8u1FkH16gMyAVhus6fU3LOzvLR9Z9.82m3tiHFAxTtIkhaZSWssSgzt4v4dGA1h/'
set system login user vyos authentication plaintext-password ''
set system option reboot-on-upgrade-failure '5'
set system syslog local facility all level 'info'
set system syslog local facility local7 level 'debug'
vyos@R5:~$
```

=== Annotation:  
R5 belongs to AS 65002 and peers with R2 through BGP.  
It advertises the 192.168.100.0/30 network toward OSPF (via R2’s redistribution) so the internal routers can reach the external ODL.

== Verification Commands

```bash
# OSPF verification
show ip ospf neighbor
show ip ospf route

# BGP verification
show ip bgp summary
show ip bgp neighbors

# Routing table check
show ip route
```

==== Annotation:  
These commands verify adjacency formation and route propagation across OSPF and BGP domains.  
Successful results confirm inter-AS communication and connectivity to the ODL via R5.

=== Output
#figure(
  image("Images/topology.png"),
  caption: [Showing the topology view from python]
)