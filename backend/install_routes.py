import ipaddress
from netmiko import ConnectHandler


def _safe_disconnect(conn, router):
    """
    Forcefully close the SSH connection without relying on Netmiko's disconnect(),
    which can hang on cEOS waiting for the session to close cleanly.
    """
    try:
        # Close the underlying Paramiko channel directly
        if conn.remote_conn is not None:
            conn.remote_conn.close()
    except Exception as e:
        print(f"Warning: channel close failed for {router}: {e}")

    try:
        # Close the Paramiko transport
        if conn.remote_conn_pre is not None:
            conn.remote_conn_pre.close()
    except Exception as e:
        print(f"Warning: transport close failed for {router}: {e}")


def _directly_connected_networks(router, ip_map):
    """
    ip_map schema assumed:
      ip_map[router][iface] = "10.0.x.y/30"
    Returns a set of networks as strings, e.g. {"10.0.1.0/30", "10.0.2.0/30"}.
    """
    nets = set()
    for iface, ip_cidr in ip_map.get(router, {}).items():
        try:
            net = ipaddress.ip_network(ip_cidr, strict=False)
            nets.add(str(net))
        except Exception:
            continue
    return nets


def _find_next_hop_ip(curr_router, next_router, lldp_topology, ip_map):
    """
    Uses LLDP tuples from curr_router to locate the neighbor interface on next_router,
    then reads that interface IP from ip_map[next_router][neighbor_if] and returns just the IP.
    """
    # lldp_topology[curr] = [(local_if, neighbor_router, neighbor_if), ...]
    for local_if, nbr, nbr_if in lldp_topology.get(curr_router, []):
        if nbr == next_router:
            ip_cidr = ip_map.get(next_router, {}).get(nbr_if)
            if not ip_cidr:
                return None
            # "10.0.2.1/30" -> "10.0.2.1"
            return ip_cidr.split("/")[0]
    return None


def install_routes(router_mgmt_ips, lldp_topology, ip_map, global_route_table,
                   username="admin", password="admin"):
    """
    global_route_table schema assumed:
      grt[router][prefix] = {"path": ["rX","rY",...], "cost": <int>}
    where prefix is like "10.0.1.0/30" (network string).

    Installs routes on each router:
      ip route <prefix> <next_hop_ip>
    """
    for router, mgmt_ip in router_mgmt_ips.items():
        print("\n====================================")
        print(f"Installing routes on {router}")
        print("====================================")

        connected_nets = _directly_connected_networks(router, ip_map)

        device = {
            "device_type": "arista_eos",
            "host": mgmt_ip,
            "username": username,
            "password": password,
            "secret": password,
            "fast_cli": False,
            "global_delay_factor": 2,
        }

        conn = ConnectHandler(**device)
        conn.enable()

        routes_for_router = global_route_table.get(router, {})

        for prefix, info in routes_for_router.items():
            # Skip directly connected networks
            if prefix in connected_nets:
                continue

            path = info.get("path") or []
            if len(path) < 2:
                continue

            next_router = path[1]

            # Safety: don't install nonsensical routes
            if next_router == router:
                continue

            next_hop_ip = _find_next_hop_ip(router, next_router, lldp_topology, ip_map)

            print("\n----------------------------------")
            print("CURRENT ROUTER:", router)
            print("DEST PREFIX:", prefix)
            print("PATH:", path)
            print("NEXT ROUTER:", next_router)
            print("NEXT HOP IP:", next_hop_ip)

            if not next_hop_ip:
                print("❌ No next-hop found (LLDP/IP mismatch). Skipping.")
                continue

            cmd = f"ip route {prefix} {next_hop_ip}"
            print("Sending:", cmd)

            out = conn.send_config_set([cmd], read_timeout=30)
            print("Device response:")
            print(out)

        # Save config: use send_command directly instead of save_config() to avoid
        # Netmiko hanging on cEOS waiting for a prompt that never arrives.
        try:
            save_out = conn.send_command("write memory", read_timeout=30)
            print("Save output:", save_out)
        except Exception as e:
            # cEOS persists running-config automatically; a save failure is non-fatal.
            print(f"Warning: write memory failed (non-fatal): {e}")

        # Force-close SSH connection instead of conn.disconnect() which hangs on cEOS
        print("Disconnecting...")
        _safe_disconnect(conn, router)
        print(f"Disconnected from {router}.")
