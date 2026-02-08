from netmiko import ConnectHandler


def _find_next_hop_ip(curr_router, next_router, lldp_topology, ip_map):
    """
    Resolve the next-hop IP for curr_router -> next_router
    using LLDP adjacency + interface IPs.
    """
    for local_if, nbr, nbr_if in lldp_topology.get(curr_router, []):
        if nbr == next_router:
            iface_info = ip_map.get(next_router, {}).get(nbr_if)
            if iface_info:
                return iface_info["ip"]
    return None


def install_routes(
    path,
    destination,
    lldp_topology,
    ip_map,
    router_mgmt_ips,
    username,
    password,
):
    """
    Install static routes for ONE destination prefix along ONE path.

    This function assumes:
    - path[0] is the router to configure
    - path[-1] is the router closest to the destination
    """

    if not path or len(path) < 2:
        return

    router = path[0]
    mgmt_ip = router_mgmt_ips.get(router)
    if not mgmt_ip:
        return

    device = {
        "device_type": "arista_eos",
        "host": mgmt_ip,
        "username": username,
        "password": password,
        "fast_cli": False,
        "global_delay_factor": 2,
    }

    conn = ConnectHandler(**device)
    conn.enable()
    conn.config_mode()

    # Install routes hop-by-hop
    for i in range(len(path) - 1):
        curr = path[i]
        nxt = path[i + 1]

        next_hop_ip = _find_next_hop_ip(
            curr, nxt, lldp_topology, ip_map
        )
        if not next_hop_ip:
            continue

        print(
            f"[INFO] Installing route on {router}: "
            f"{destination} → {next_hop_ip}"
        )

        # Timing-based send (NO prompt matching)
        conn.send_command_timing(
            f"ip route {destination} {next_hop_ip}",
            strip_prompt=False,
            strip_command=False,
        )

    conn.exit_config_mode()
    conn.save_config()
    conn.disconnect()
