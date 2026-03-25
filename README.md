# SDN Controller Platform

A full-stack Software-Defined Networking (SDN) orchestration platform that automates the deployment, configuration, and management of containerized network topologies.


## 🎯 Overview

This SDN controller provides end-to-end automation for network fabric deployment, from topology design through route installation. Users design network topologies via an interactive web interface, and the controller automatically:

- Deploys containerized routers using ContainerLab
- Discovers network topology using LLDP
- Allocates IP addresses dynamically
- Computes shortest paths using graph algorithms
- Installs optimal static routes across all devices

**Deployment Time:** Manual configuration (~30 minutes) → Automated deployment (~2-3 minutes) — **90% time reduction**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Frontend (JavaScript)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Topology   │  │     SVG      │  │    JSON      │      │
│  │   Builder    │  │  Visualizer  │  │   Preview    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Backend (Python/FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Topology    │  │  Addressing  │  │   Fabric     │      │
│  │  Generator   │  │   Engine     │  │   Config     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     LLDP     │  │  IP Address  │  │    Graph     │      │
│  │  Collector   │  │  Collector   │  │   Builder    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    Route     │  │  Controller  │                         │
│  │  Installer   │  │ Orchestrator │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                            │ SSH/Netmiko
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Containerized Network (ContainerLab/Docker)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Router 1 │──│ Router 2 │──│ Router 3 │──│ Router N │   │
│  │ (cEOS)   │  │ (cEOS)   │  │ (cEOS)   │  │ (cEOS)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Frontend
- 🎨 **Interactive Topology Builder** - Drag-and-drop interface for network design
- 📊 **Real-time SVG Visualization** - Dynamic network diagram with circular layout
- ✅ **Input Validation** - Prevents invalid topologies (duplicate routers, self-links)
- 📋 **JSON Preview** - Live payload inspection before deployment
- 🚦 **Status Feedback** - Color-coded deployment progress indicators

### Backend
- 🔍 **LLDP Topology Discovery** - Automatic neighbor detection via Link Layer Discovery Protocol
- 🧮 **BFS Shortest Path Algorithm** - Optimal route computation using graph theory
- 📍 **Dynamic IP Allocation** - Automatic /30 subnet generation for point-to-point links
- 🔧 **Zero-Touch Provisioning** - Automated interface configuration via SSH
- 📡 **SSH Automation** - Netmiko-based CLI configuration management
- 🔄 **Async Operations** - Non-blocking deployment pipeline with FastAPI
- 🐳 **Container Orchestration** - ContainerLab integration for router deployment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker
- ContainerLab
- Arista cEOS image (`ceos:4.35.1F` or similar)
- `sudo` access (for ContainerLab)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/sdn-controller.git
cd sdn-controller
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Ensure ContainerLab is installed**
```bash
# Install ContainerLab (if not already installed)
bash -c "$(curl -sL https://get.containerlab.dev)"
```

4. **Load Arista cEOS Docker image**
```bash
docker import cEOS64-lab-4.35.1F.tar.xz ceos:4.35.1F
```

### Running the Application

1. **Start the backend server**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

2. **Open the frontend**
```bash
# Open index.html in your browser
# Or serve it with a simple HTTP server:
cd frontend
python3 -m http.server 8080
```

3. **Access the application**
- Frontend: `http://localhost:8080`
- API docs: `http://localhost:5000/docs`

---

## 📖 Usage

### Building a Topology

1. **Add Routers**
   - Enter router name (e.g., `r1`, `r2`, `r3`)
   - Click "Add Router"
   - Repeat for all routers (max 8)

2. **Add Links**
   - Select two routers from dropdowns
   - Click "Add Link"
   - Links appear in the topology diagram

3. **Review Configuration**
   - Check the SVG topology visualization
   - Verify JSON payload in preview panel

4. **Deploy**
   - Click "Deploy" button
   - Wait 2-3 minutes for automated deployment
   - Success message shows routes installed

### Example Topology

```javascript
{
  "name": "sdn-lab",
  "mgmt_subnet": "172.20.20.0/24",
  "routers": ["r1", "r2", "r3"],
  "links": [
    ["r1", "r2"],
    ["r1", "r3"]
  ],
  "ceos_image": "ceos:4.35.1F"
}
```

This creates:
- 3 routers: r1, r2, r3
- 2 links: r1↔r2, r1↔r3
- Management IPs: 172.20.20.11, .12, .13
- Data plane IPs: 10.0.1.0/30, 10.0.2.0/30

---

## 🔧 Technical Details

### Deployment Pipeline

1. **Topology Generation** (`topology_gen.py`)
   - Generates ContainerLab YAML from user input
   - Assigns management IPs deterministically
   - Creates node and link definitions

2. **Container Deployment**
   - Destroys existing lab (cleanup)
   - Deploys new containers with `containerlab deploy`
   - Waits 40 seconds for initialization

3. **IP Address Allocation** (`addressing.py`)
   - Generates /30 subnets starting from 10.0.1.0/30
   - Maps interfaces (Ethernet1, Ethernet2, etc.) to IPs
   - Returns structured interface map

4. **Fabric Configuration** (`fabric_config.py`)
   - SSH into each router via management IP
   - Pushes interface configurations:
     - `no switchport` (Layer 3 mode)
     - `ip address <IP>/<mask>`
     - `no shutdown`

5. **LLDP Discovery** (`lldp_collect.py`)
   - Collects `show lldp neighbors detail` from all routers
   - Parses output with regex to extract:
     - Local interface
     - Neighbor router name
     - Remote interface
   - Builds topology dictionary

6. **IP Collection** (`ip_collect.py`)
   - Runs `show interfaces | json` on all routers
   - Parses JSON output to extract interface IPs
   - Creates IP mapping table

7. **Graph Construction** (`graph_utils.py`)
   - Converts LLDP topology to adjacency list
   - Runs BFS to find shortest paths between all router pairs
   - Builds Global Routing Table (GRT) with path and cost

8. **Route Installation** (`install_routes.py`)
   - For each router and each destination subnet:
     - Skip directly-connected networks
     - Lookup shortest path from GRT
     - Find next-hop router's interface IP
     - Push `ip route <prefix> <next-hop-ip>`
   - Saves configuration with `write memory`

### Key Algorithms

**BFS Shortest Path:**
```python
def bfs_shortest_path(graph, start, goal):
    visited = set()
    queue = deque([[start]])
    
    while queue:
        path = queue.popleft()
        node = path[-1]
        
        if node not in visited:
            neighbors = graph.get(node, [])
            for neighbor in neighbors:
                new_path = list(path)
                new_path.append(neighbor)
                if neighbor == goal:
                    return new_path
                queue.append(new_path)
            visited.add(node)
    
    return None
```

**IP Allocation:**
```python
def generate_interface_map(routers, links):
    interface_map = {router: {} for router in routers}
    interface_counter = {router: 1 for router in routers}
    subnet_counter = 1
    
    for router_a, router_b in links:
        subnet = ipaddress.ip_network(f"10.0.{subnet_counter}.0/30")
        hosts = list(subnet.hosts())
        
        iface_a = f"Ethernet{interface_counter[router_a]}"
        interface_map[router_a][iface_a] = f"{hosts[0]}/{subnet.prefixlen}"
        interface_counter[router_a] += 1
        
        iface_b = f"Ethernet{interface_counter[router_b]}"
        interface_map[router_b][iface_b] = f"{hosts[1]}/{subnet.prefixlen}"
        interface_counter[router_b] += 1
        
        subnet_counter += 1
    
    return interface_map
```

---

## 📁 Project Structure

```
sdn-controller/
├── backend/
│   ├── main.py                 # FastAPI application & REST endpoints
│   ├── controller.py           # Main orchestration logic
│   ├── topology_gen.py         # ContainerLab YAML generator
│   ├── addressing.py           # IP allocation engine
│   ├── fabric_config.py        # Interface configuration pusher
│   ├── lldp_collect.py         # LLDP topology discovery
│   ├── ip_collect.py           # IP address collector
│   ├── graph_utils.py          # Graph algorithms & routing table
│   ├── install_routes.py       # Route installation engine
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # Web interface
│   └── app.js                  # Frontend logic & API calls
├── generated/                  # Auto-generated files (gitignored)
│   ├── topology.clab.yaml      # ContainerLab topology
│   ├── inventory.json          # Router management IPs
│   └── clab-sdn-lab/           # ContainerLab working directory
└── README.md                   # This file
```

---

## 🔌 API Reference

### POST `/deploy`

Deploy a network topology.

**Request Body:**
```json
{
  "name": "sdn-lab",
  "mgmt_subnet": "172.20.20.0/24",
  "routers": ["r1", "r2", "r3"],
  "links": [["r1", "r2"], ["r1", "r3"]],
  "ceos_image": "ceos:4.35.1F"
}
```

**Response (Success):**
```json
{
  "status": "deployed_and_configured",
  "router_count": 3,
  "controller_result": {
    "routers_processed": 3,
    "topology_nodes": ["r1", "r2", "r3"],
    "status": "routes_installed"
  }
}
```

**Response (Error):**
```json
{
  "detail": "Maximum 8 routers allowed."
}
```

**Validation Rules:**
- Minimum 2 routers
- Maximum 8 routers
- No duplicate router names
- No self-links
- Links must reference existing routers

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 🛠️ Technologies Used

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Core language |
| FastAPI | REST API framework |
| Netmiko | SSH automation for network devices |
| Pydantic | Request validation & data modeling |
| PyYAML | YAML file generation |
| ipaddress | IP subnet calculations |
| asyncio | Asynchronous operations |

### Frontend
| Technology | Purpose |
|------------|---------|
| HTML5/CSS3 | User interface |
| Vanilla JavaScript | Frontend logic |
| SVG | Dynamic topology visualization |
| Fetch API | Async HTTP requests |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| ContainerLab | Network topology emulation |
| Docker | Container runtime |
| Arista cEOS | Containerized network OS |
| LLDP | Topology discovery protocol |

---

## 🧪 Testing

### Manual Testing

1. **Test Simple Topology (3 routers)**
```json
{
  "routers": ["r1", "r2", "r3"],
  "links": [["r1", "r2"], ["r2", "r3"]]
}
```

2. **Verify Routes**
```bash
# SSH into a router
ssh admin@172.20.20.11

# Check routing table
show ip route

# Expected: Routes to all /30 subnets via correct next-hops
```

3. **Test Connectivity**
```bash
# From r1, ping r3's interface
ping 10.0.2.2
```

### Test Complex Topology (Full Mesh)
```json
{
  "routers": ["r1", "r2", "r3", "r4"],
  "links": [
    ["r1", "r2"], ["r1", "r3"], ["r1", "r4"],
    ["r2", "r3"], ["r2", "r4"], ["r3", "r4"]
  ]
}
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** Deployment hangs during route installation
```bash
# Solution: Check SSH connectivity
ssh admin@172.20.20.11

# Verify LLDP is running
show lldp neighbors
```

**Issue:** Routes not installed
```bash
# Check controller logs
# Verify GRT was built correctly
# Ensure LLDP discovered all neighbors
```

**Issue:** ContainerLab deployment fails
```bash
# Clean up existing lab
sudo containerlab destroy -t generated/topology.clab.yaml

# Remove orphaned containers
docker rm -f $(docker ps -aq --filter name=clab-sdn-lab)

# Retry deployment
```

**Issue:** Frontend can't connect to backend
```bash
# Check CORS settings in main.py
# Verify backend is running on port 5000
# Check browser console for errors
```

---

## 🚧 Known Limitations

1. **CLI Parsing with Regex**
   - Fragile to output format changes
   - Not as robust as structured APIs

2. **Static Routes Only**
   - No dynamic routing protocols (OSPF, BGP)
   - No automatic failover

3. **No Authentication**
   - Hardcoded credentials (admin/admin)
   - No user management

4. **No Persistence**
   - Topology data not saved to database
   - No deployment history

5. **Single Vendor Support**
   - Arista-specific commands
   - Would need modification for Cisco/Juniper

---

## 🎯 Future Enhancements

### Phase 1: API Migration
- [ ] Refactor to use Arista eAPI instead of SSH/CLI
- [ ] Structured JSON responses instead of regex parsing
      
### Phase 2: Self-Healing
- [ ] Automatic link failure detection (<2 seconds)
- [ ] Dynamic path recalculation
- [ ] Traffic rerouting on failures
- [ ] Health monitoring and auto-remediation
 
### Phase 3: Production Features
- [ ] PostgreSQL database for topology persistence
- [ ] Configuration rollback on failure
- [ ] Automated backups before changes

### Phase 5: Monitoring & Observability
- [ ] Grafana dashboards for network metrics
- [ ] Historical performance tracking

---

## 📊 Performance Metrics

| Metric | Manual | Automated | Improvement |
|--------|--------|-----------|-------------|
| Deployment Time (3 routers) | ~30 min | ~2 min | 93% faster |
| Configuration Errors | Common | Zero | 100% reduction |
| Route Installation Time | ~5 min/router | ~30 sec total | 95% faster |
| Topology Discovery | Manual documentation | Automated LLDP | Eliminated |

---

---

## 📚 Additional Resources

- [ContainerLab Documentation](https://containerlab.dev/)
- [Netmiko Documentation](https://github.com/ktbyers/netmiko)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Arista EOS Documentation](https://www.arista.com/en/support/software-download)

