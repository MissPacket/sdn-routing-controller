import re
from netmiko import ConnectHandler


LOCAL_IF_RE = re.compile(r"Interface (\S+) detected")
SYSTEM_RE = re.compile(r'System Name:\s+"([^"]+)"')
REMOTE_IF_RE = re.compile(r'Port ID\s+:\s+"([^"]+)"')


def collect_lldp(router_mgmt_ips):
    """
    Collect LLDP topology from all routers.
    Returns:
        {
            "r1": [("Ethernet1","r2","Ethernet1"), ...]
        }
    """

    topology = {}

    for router, mgmt_ip in router_mgmt_ips.items():

        device = {
            "device_type": "arista_eos",
            "host": mgmt_ip,
            "username": "admin",
            "password": "admin",
            "ssh_strict": False,
        }

        conn = ConnectHandler(**device)
        conn.enable()

        output = conn.send_command("show lldp neighbors detail")
        conn.disconnect()

        neighbors = []

        # Split on blank-line + "Interface" boundaries, drop the header block (index 0)
        raw_blocks = re.split(r'\n\nInterface ', output)

        for i, block in enumerate(raw_blocks):
            # Re-attach the keyword stripped by split (skip for the first header block)
            if i > 0:
                block = "Interface " + block
            else:
                # First chunk is the command header; only process if it starts correctly
                if not block.strip().startswith("Interface"):
                    continue

            local_if = LOCAL_IF_RE.search(block)
            system = SYSTEM_RE.search(block)
            remote_if = REMOTE_IF_RE.search(block)

            if not (local_if and system and remote_if):
                continue

            if local_if.group(1).lower().startswith("management"):
                continue

            neighbors.append(
                (
                    local_if.group(1),
                    system.group(1),
                    remote_if.group(1),
                )
            )

        topology[router] = neighbors

    return topology
