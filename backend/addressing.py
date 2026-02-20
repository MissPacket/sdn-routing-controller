def generate_interface_map(routers, links):
    """
    Generate interface-to-IP assignments for all routers.

    Inputs:
        routers: ["r1", "r2", "r3"]
        links: [
            ["r1", "r2"],
            ["r2", "r3"]
        ]

    Returns:
        {
            "r1": {"Ethernet1": "10.0.1.1/30"},
            "r2": {
                "Ethernet1": "10.0.1.2/30",
                "Ethernet2": "10.0.2.1/30"
            },
            "r3": {"Ethernet1": "10.0.2.2/30"}
        }
    """

    # Initialize empty structure
    interface_map = {router: {} for router in routers}

    # Track next Ethernet number per router
    interface_counters = {router: 1 for router in routers}

    subnet_counter = 1  # used to generate unique /30 per link

    for link in links:
        r1 = link[0]
        r2 = link[1]

        # Assign subnet 10.0.X.0/30
        ip1 = f"10.0.{subnet_counter}.1/30"
        ip2 = f"10.0.{subnet_counter}.2/30"

        # Assign next available Ethernet interface
        iface1 = f"Ethernet{interface_counters[r1]}"
        iface2 = f"Ethernet{interface_counters[r2]}"

        interface_map[r1][iface1] = ip1
        interface_map[r2][iface2] = ip2

        # Increment counters
        interface_counters[r1] += 1
        interface_counters[r2] += 1
        subnet_counter += 1

    return interface_map
