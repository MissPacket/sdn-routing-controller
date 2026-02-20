from netmiko import ConnectHandler

def configure_fabric(router_mgmt_ips, interfaces):

    for router, host in router_mgmt_ips.items():

        device = {
            "device_type": "arista_eos",
            "host": host,
            "username": "admin",
            "password": "admin",
            "secret": "admin",
            "fast_cli": False,
            "global_delay_factor": 2,
        }

        conn = ConnectHandler(**device)
        conn.enable()

        conn.send_config_set([
            "username admin privilege 15 role network-admin secret admin"
        ])

        cfg = []
        for iface, ip in interfaces.get(router, {}).items():
            cfg.extend([
                f"interface {iface}",
                "no switchport",
                f"ip address {ip}",
                "no shutdown"
            ])

        if cfg:
            conn.send_config_set(cfg)

        conn.disconnect()
