import ipaddress
from install_routes import install_routes
from graph_utils import bfs_shortest_path, build_adjacency
from lldp_collect import collect_lldp
from ip_collect import collect_ips


def build_link_db(lldp_topology, ip_map):
    """
    Build unique link records from LLDP + interface IPs.

    Returns list of dicts:
      {
        "a": "r1", "a_if": "Ethernet1", "a_ip": "10.0.12.1",
        "b": "r2", "b_if": "Ethernet1", "b_ip": "10.0.12.2",
        "prefix": "10.0.12.0/30"
      }
    """
    seen = set()
    links = []

    for a, nbrs in lldp_topology.items():
        for a_if, b, b_if in nbrs:
            # avoid duplicates (a-b vs b-a)
            key = tuple(sorted([(a, a_if), (b, b_if)]))
            if key in seen:
                continue
            seen.add(key)

            a_info = ip_map.get(a, {}).get(a_if)
            b_info = ip_map.get(b, {}).get(b_if)
            if not a_info or not b_info:
                continue

            # compute link prefix from either side
            net = ipaddress.ip_network(f'{a_info["ip"]}/{a_info["mask"]}', strict=False)

            links.append({
                "a": a, "a_if": a_if, "a_ip": a_info["ip"],
                "b": b, "b_if": b_if, "b_ip": b_info["ip"],
                "prefix": str(net),
            })

    return links


def build_global_route_table(routers, graph):
    """
    PDF-style Global Route Table:
    For each src, compute best path to every dst.
    Cost = hop count (all links cost 1).
    """
    grt = {}  # grt[src][dst] = {"path": [...], "cost": N}

    for src in routers:
        grt[src] = {}
        for dst in routers:
            if src == dst:
                continue
            path = bfs_shortest_path(graph, src, dst)
            if not path:
                continue
            cost = len(path) - 1
            grt[src][dst] = {"path": path, "cost": cost}

    return grt


def connected_prefixes(router, ip_map):
    """
    Prefixes directly connected on router interfaces.
    """
    prefs = set()
    for iface, data in ip_map.get(router, {}).items():
        net = ipaddress.ip_network(f'{data["ip"]}/{data["mask"]}', strict=False)
        prefs.add(str(net))
    return prefs


def choose_best_endpoint(router, prefix, links, grt):
    """
    For a given prefix (which belongs to a link between two routers),
    pick which endpoint router to route toward from 'router'.
    Uses GRT cost as primary metric (PDF: lower cost wins; tie → fewer hops).
    """
    # find the link that owns this prefix
    link = next((l for l in links if l["prefix"] == prefix), None)
    if not link:
        return None

    a = link["a"]
    b = link["b"]

    if router == a or router == b:
        return None  # directly connected; don't install

    ra = grt.get(router, {}).get(a)
    rb = grt.get(router, {}).get(b)

    if not ra and not rb:
        return None
    if ra and not rb:
        return a
    if rb and not ra:
        return b

    # both exist: pick lower cost; tie-break by hop count (same here)
    if ra["cost"] < rb["cost"]:
        return a
    if rb["cost"] < ra["cost"]:
        return b
    # tie → shorter path length (same as cost for BFS, but keep logic)
    return a if len(ra["path"]) <= len(rb["path"]) else b


def main():
    ROUTER_MGMT_IPS = {
        "r1": "172.20.20.11",
        "r2": "172.20.20.12",
        "r3": "172.20.20.13",
        "r4": "172.20.20.14",
        "r5": "172.20.20.15",
    }
    USERNAME = "admin"
    PASSWORD = "admin"

    # 1) collect topology + IPs
    lldp_topology = collect_lldp(ROUTER_MGMT_IPS, USERNAME, PASSWORD)
    ip_map = collect_ips(ROUTER_MGMT_IPS, USERNAME, PASSWORD)

    # 2) build graph
    graph = build_adjacency(lldp_topology)

    # 3) build link database (prefixes come from links)
    links = build_link_db(lldp_topology, ip_map)
    all_prefixes = sorted({l["prefix"] for l in links})

    # 4) build Global Route Table (PDF concept)
    routers = list(ROUTER_MGMT_IPS.keys())
    grt = build_global_route_table(routers, graph)

    # 5) static route pushing for full routing tables
    for r in routers:
        local = connected_prefixes(r, ip_map)

        for prefix in all_prefixes:
            if prefix in local:
                continue  # directly connected

            endpoint = choose_best_endpoint(r, prefix, links, grt)
            if not endpoint:
                continue

            # path to chosen endpoint router (from GRT)
            path = grt[r][endpoint]["path"]

            install_routes(
                path=path,
                destination=prefix,
                lldp_topology=lldp_topology,
                ip_map=ip_map,
                router_mgmt_ips=ROUTER_MGMT_IPS,
                username=USERNAME,
                password=PASSWORD
            )


if __name__ == "__main__":
    main()
