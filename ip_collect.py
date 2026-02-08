import json
from netmiko import ConnectHandler


def _get_interface_ips(conn):
    """
    Collect interface IPs from a single router.

    Returns:
      {
        "Ethernet1": {"ip": "10.0.12.1", "mask": 30},
        "Ethernet2": {"ip": "10.0.13.1", "mask": 30},
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
            iface_ip_map[ifname] = {
                "ip": ip,
                "mask": mask,
            }

    return iface_ip_map


def collect_ips(inventory, username, password):
    """
    Collect interface → IP mappings from all routers.

    Args:
        inventory: dict mapping router name -> management IP
        username: device username
        password: device password

    Returns:
        ip_map of the form:
        {
          "r1": {
              "Ethernet1": {"ip": "10.0.12.1", "mask": 30},
              "Ethernet2": {"ip": "10.0.13.1", "mask": 30},
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
            "username": username,
            "password": password,
            "secret": password,
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


