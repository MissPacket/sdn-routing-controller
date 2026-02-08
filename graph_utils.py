from collections import deque


def build_adjacency(lldp_topology):
    """
    Build a router-level adjacency list from LLDP data.

    Input:
      {
        "r1": [("Ethernet1", "r2", "Ethernet1"),
               ("Ethernet2", "r3", "Ethernet1")],
        "r2": [("Ethernet1", "r1", "Ethernet1")]
      }

    Output:
      {
        "r1": {"r2", "r3"},
        "r2": {"r1"},
        "r3": {"r1"}
      }
    """
    graph = {}

    for router, neighbors in lldp_topology.items():
        if router not in graph:
            graph[router] = set()

        for _, nbr, _ in neighbors:
            graph[router].add(nbr)

            if nbr not in graph:
                graph[nbr] = set()
            graph[nbr].add(router)

    return graph


def bfs_shortest_path(graph, start, goal):
    """
    Compute the shortest path (minimum hops) between two routers using BFS.

    Returns:
      ["r1", "r2", "r4", "r5"] if a path exists
      None if no path exists
    """
    if start not in graph or goal not in graph:
        return None

    queue = deque([[start]])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == goal:
            return path

        if node in visited:
            continue

        visited.add(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                queue.append(path + [neighbor])

    return None

