# SDN Global Routing Controller (LLDP-Based)

## Overview

This project implements a **Software-Defined Networking (SDN) controller** that builds **global routing tables** and installs **static routes** across a network of routers using a centralized control plane.

The controller discovers network topology using **LLDP**, computes **shortest paths** using a graph-based algorithm, and programs **static routes** on all routers so that every router can reach every configured network prefix.

The design follows a **link-state routing model** (similar to OSPF), but is implemented entirely in Python as a centralized SDN controller.  
The project is validated using **Arista cEOS routers** deployed with **Containerlab**.

---

## Features

- LLDP-based topology discovery  
- Interface and prefix discovery using EOS JSON output  
- Global routing table construction  
- Shortest-path computation (hop-count based)  
- Static route installation on all routers  
- Robust CLI automation for cEOS environments  

---

## High-Level Architecture

Routers (cEOS)  
  |  
  | LLDP + Interface State  
  v  
SDN Controller (Python)  
  |  
  v  
Static Routes Installed

---

## Routing Model

- All routers learn routes to **all non-local prefixes**
- Connected networks are detected automatically
- Routes are installed based on **shortest paths** in the topology
- Link costs are assumed equal (hop-count metric)
- Static routes are used for transparency and control

This mirrors the behavior of **link-state routing protocols**, but uses a centralized controller instead of distributed routing processes.

---

## Repository Contents

```
.
├── controller.py # Main SDN controller (orchestration logic)
├── lldp_collect.py # LLDP-based topology discovery
├── ip_collect.py # Interface IP and prefix discovery
├── graph_utils.py # Graph construction + BFS shortest path
├── install_routes.py # Static route installation (CLI-based)
├── topology.clab.yaml # Containerlab topology (cEOS)
└── README.md

---

## Environment Requirements

### Software
- Python 3.10+
- Docker
- Containerlab
- Arista cEOS (tested on EOS 4.35.x)

### Python Dependencies
```
pip install netmiko
```

---

## How It Works

1. **Topology Discovery**
   - Uses `show lldp neighbors detail`
   - Builds router adjacency graph

2. **Prefix Discovery**
   - Uses `show interfaces | json`
   - Extracts interface IPs and converts them into network prefixes

3. **Shortest Path Computation**
   - Builds a graph of routers
   - Uses BFS to compute shortest paths (equal-cost links)

4. **Global Route Table Construction**
   - Determines reachability to all prefixes
   - Selects next hops based on shortest paths

5. **Static Route Installation**
   - Enters configuration mode once per router
   - Installs static routes using timing-based CLI commands
   - Saves configuration

---

## Running the Project

### 1. Deploy the topology
```
sudo containerlab deploy -t topology.clab.yaml
```

### 2. Verify containers
```
containerlab inspect
```

### 3. Activate Python environment
```
source sdn-venv/bin/activate
```

### 4. Run the controller
```
python3 sdn_global_routing_controller.py
```

---

## Verification

On each router:
```
show ip route
show ip route static
```

You should see:
- Connected routes for local interfaces
- Static routes for all other network prefixes

---

## Design Decisions

- Centralized SDN controller for clarity and control
- BFS used instead of Dijkstra (equal link costs)
- Static routing for deterministic behavior
- Timing-based CLI commands for reliability on cEOS
- Single-file implementation for simplicity

---

## Limitations

- No weighted links
- No ECMP
- No dynamic failure recovery
- CLI-based configuration only

---

## Future Enhancements

- Weighted shortest-path routing
- Failure detection and re-routing
- Route reconciliation
- eAPI-based configuration

---

## License

Educational use only.
