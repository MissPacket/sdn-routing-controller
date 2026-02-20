import ipaddress
from collections import deque


def build_graph(lldp_topology):
    """
    Builds adjacency list graph from LLDP topology.

    Input:
        {
            "r1": [("Ethernet1","r2","Ethernet1"), ...],
            ...
        }

    Output:
        {
            "r1": ["r2","r3"],
            "r2": ["r1","r4"],
            ...
        }
    """

    graph = {}

    for router, neighbors in lldp_topology.items():
        graph.setdefault(router, [])

        for local_if, neighbor, remote_if in neighbors:
            if neighbor not in graph[router]:
                graph[router].append(neighbor)

    return graph


def bfs_shortest_path(graph, start, goal):
    """
    Standard BFS shortest path.
    """

    visited = set()
    queue = deque([[start]])

    if start == goal:
        return [start]

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


def _router_subnets(router, ip_map):
    """
    Return all subnet prefixes (as strings) attached to a router.
    e.g. {"10.0.1.0/30", "10.0.2.0/30"}
    """
    nets = set()
    for iface, ip_cidr in ip_map.get(router, {}).items():
        try:
            net = ipaddress.ip_network(ip_cidr, strict=False)
            nets.add(str(net))
        except Exception:
            continue
    return nets


def build_global_routing_table(graph, ip_map):
    """
    Build Global Routing Table (GRT) keyed by destination subnet prefix.

    For each source router, compute the shortest path to every other router,
    then record a route entry for each subnet attached to that destination router.

    Output:
        {
            "r1": {
                "10.0.2.0/30": {
                    "path": ["r1", "r2", "r3"],
                    "cost": 2
                },
                ...
            },
            ...
        }
    """

    grt = {}

    for src in graph:
        grt[src] = {}

        for dst in graph:
            if src == dst:
                continue

            path = bfs_shortest_path(graph, src, dst)

            if not path:
                continue

            # Add a route entry for every subnet directly attached to dst
            for prefix in _router_subnets(dst, ip_map):
                # Only record if we don't already have a shorter/equal path
                # (multiple routers could share a subnet in theory — take first found)
                if prefix not in grt[src]:
                    grt[src][prefix] = {
                        "path": path,
                        "cost": len(path) - 1,
                    }

    return grt
