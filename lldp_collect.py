import re
from netmiko import ConnectHandler

# Regex patterns
LOCAL_IF_RE = re.compile(r"Interface (\S+) detected")
SYSTEM_RE = re.compile(r'System Name:\s+"([^"]+)"')
REMOTE_IF_RE = re.compile(r'Port ID\s+:\s+"([^"]+)"')


def collect_lldp(inventory, username, password):
    """
    Collect LLDP topology from all routers.

    Args:
        inventory: dict mapping router name -> management IP
        username: device username
        password: device password

    Returns:
        topology dict of the form:
        {
          "r1": [("Ethernet1", "r2", "Ethernet1"), ...],
          "r2": [...],
        }
    """
    topology = {}

    for router, host in inventory.items():
        print(f"\n=== Collecting LLDP from {router} ===")

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

        output = conn.send_command(
            "show lldp neighbors detail",
            expect_string=r"#"
        )
        conn.disconnect()

        neighbors = []

        # Split output into per-interface blocks
        blocks = output.split("\n\nInterface ")
        for block in blocks:
            if not block.startswith("Interface"):
                block = "Interface " + block

            local_if = LOCAL_IF_RE.search(block)
            system = SYSTEM_RE.search(block)
            remote_if = REMOTE_IF_RE.search(block)

            if not (local_if and system and remote_if):
                continue

            # Skip management interface
            if local_if.group(1).lower().startswith("management"):
                continue

            neighbors.append(
                (
                    local_if.group(1),   # local interface
                    system.group(1),     # neighbor router name
                    remote_if.group(1),  # neighbor interface
                )
            )

        topology[router] = neighbors

    return topology

