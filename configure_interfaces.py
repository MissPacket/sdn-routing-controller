import yaml
from netmiko import ConnectHandler

# -----------------------------
# Router inventory (mgmt IPs)
# -----------------------------
inventory = {
    "r1": "172.20.20.11",
    "r2": "172.20.20.12",
    "r3": "172.20.20.13",
    "r4": "172.20.20.14",
    "r5": "172.20.20.15",
}

# -----------------------------
# Load interface definitions
# -----------------------------
with open("interfaces.yaml") as f:
    interfaces = yaml.safe_load(f)

# -----------------------------
# Loop through routers
# -----------------------------
for router, host in inventory.items():
    print(f"\n=== Configuring {router} ===")

    device = {
        "device_type": "arista_eos",
        "host": host,
        "username": "admin",
        "password": "admin",
        "secret": "admin",          # enable password
        "fast_cli": False,          # IMPORTANT for EOS
        "global_delay_factor": 2,   # prevents timing issues
    }

    conn = ConnectHandler(**device)

    # Enter privileged mode
    conn.enable()
  
    # Ensure admin user exists
    conn.send_config_set([
    "username admin privilege 15 role network-admin secret admin"])

    # Build config commands
    cfg = []
    for iface, ip in interfaces.get(router, {}).items():
        cfg.extend([
            f"interface {iface}",
            "no switchport", 
            f"ip address {ip}",
            "no shutdown"
        ])

    # Push config if present
    if cfg:
        conn.send_config_set(cfg)
        conn.save_config()

    print(f"{router}: interface configuration complete")

    conn.disconnect()
