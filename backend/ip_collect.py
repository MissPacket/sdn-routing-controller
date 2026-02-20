import json
from netmiko import ConnectHandler


def _get_interface_ips(conn):
    """
    Collect interface IPs from a single router.

    Returns:
      {
        "Ethernet1": "10.0.12.1/30",
        "Ethernet2": "10.0.13.1/30",
      }
    """
    output = conn.send_command("show interfaces | json", expect_string=r"#")
    data = json.loads(output)

    iface_ip_map = {}

    for ifname, ifdata in data.get("interfaces", {}).items():
        # Ignore management interface
        if ifname.lower().startswith("management"):
            continue

        iface_addr = ifdata.get("interfaceAddress", [])
        if not iface_addr:
            continue

        primary = iface_addr[0].get("primaryIp")
        if not primary:
            continue

        ip = primary.get("address")
        mask = primary.get("maskLen")

        if ip and mask is not None:
            # Return as CIDR string so install_routes.py can use it directly
            iface_ip_map[ifname] = f"{ip}/{mask}"

    return iface_ip_map


def collect_interface_ips(inventory):
    """
    Collect interface -> IP mappings from all routers.

    Args:
        inventory: dict mapping router name -> management IP

    Returns:
        ip_map of the form:
        {
          "r1": {
              "Ethernet1": "10.0.12.1/30",
              "Ethernet2": "10.0.13.1/30",
          },
          "r2": {...},
        }
    """
    ip_table = {}

    for router, host in inventory.items():
        print(f"\n=== Collecting interface IPs from {router} ===")

        device = {
            "device_type": "arista_eos",
            "host": host,
            "username": "admin",
            "password": "admin",
            "secret": "admin",
            "use_keys": False,
            "allow_agent": False,
            "fast_cli": False,
            "global_delay_factor": 2,
        }

        conn = ConnectHandler(**device)
        conn.enable()

        ip_table[router] = _get_interface_ips(conn)

        conn.disconnect()

    return ip_table
