import json
import time

from backend.lldp_collect import collect_lldp
from backend.ip_collect import collect_interface_ips
from backend.graph_utils import build_graph, build_global_routing_table
from backend.install_routes import install_routes


def run_controller(inventory_path):
    """
    Main SDN controller orchestration function.

    Steps:
    1. Load inventory (router → mgmt IP)
    2. Collect LLDP topology
    3. Collect interface IPs
    4. Build graph
    5. Build Global Routing Table (GRT)
    6. Install static routes
    """

    # ----------------------------
    # 1️⃣ Load inventory
    # ----------------------------
    with open(inventory_path) as f:
        router_mgmt_ips = json.load(f)

    print("Inventory loaded:")
    print(router_mgmt_ips)

    # ----------------------------
    # 2️⃣ Wait for routers to stabilize
    # ----------------------------
    time.sleep(5)

    # ----------------------------
    # 3️⃣ Collect LLDP topology
    # ----------------------------
    lldp_topology = collect_lldp(router_mgmt_ips)
    print("lldp topology:")
    print(lldp_topology)

    # ----------------------------
    # 4️⃣ Collect interface IPs
    # ----------------------------
    ip_map = collect_interface_ips(router_mgmt_ips)
    print("IP MAP:")
    print(ip_map)

    # ----------------------------
    # 5️⃣ Build graph
    # ----------------------------
    graph = build_graph(lldp_topology)
    print("GRAPH:")
    print(graph)

    # ----------------------------
    # 6️⃣ Build Global Routing Table
    # ----------------------------
    grt = build_global_routing_table(graph, ip_map)
    print("GLOBAL ROUTE TABLE:")
    print(grt)

    # ----------------------------
    # 7️⃣ Install static routes
    # ----------------------------
    install_routes(router_mgmt_ips,lldp_topology,ip_map,grt)

    return {
        "routers_processed": len(router_mgmt_ips),
        "topology_nodes": list(graph.keys()),
        "status": "routes_installed"
    }
