import yaml


def _base_from_subnet(subnet_cidr):
    """
    Example:
        "172.20.20.0/24"
    Returns:
        "172.20.20"
    """
    ip = subnet_cidr.split("/")[0]
    return ip.rsplit(".", 1)[0]


def build_containerlab_yaml(payload):
    """
    Builds containerlab topology dict and management IP map.

    Returns:
        topo_dict
        mgmt_ips (dict)
    """

    name = payload.get("name", "sdn-lab")
    mgmt_subnet = payload.get("mgmt_subnet", "172.20.20.0/24")
    routers = payload["routers"]
    links = payload["links"]
    image = payload.get("ceos_image", "ceos:4.35.1F")

    # Assign management IPs deterministically (.11, .12, ...)
    base = _base_from_subnet(mgmt_subnet)
    start_host = 11
    mgmt_ips = {r: f"{base}.{start_host + i}" for i, r in enumerate(routers)}

    topo = {
        "name": name,
        "mgmt": {
            "network": "clab",
            "ipv4-subnet": mgmt_subnet,
        },
        "topology": {
            "kinds": {
                "ceos": {
                    "image": image,
                    "env": {"INTFTYPE": "eth"},
                    "startup-config": "\n".join([
                        "hostname {{ .Name }}",
                        "service routing protocols model multi-agent",
                        "lldp run",
                        "",
                  "username admin privilege 15 role network-admin secret admin",
                  "",
                  "management ssh",
                   "no shutdown",
                    "",
                        "management api http-commands",
                        "  protocol http",
                        "  no shutdown",
                    ]),
                }
            },
            "nodes": {},
            "links": [],
        },
    }

    # Create router nodes
    for r in routers:
        topo["topology"]["nodes"][r] = {
            "kind": "ceos",
            "mgmt-ipv4": mgmt_ips[r],
        }

    # Assign link interfaces (eth1, eth2, etc.)
    if_counter = {r: 1 for r in routers}

    for a, b in links:
        a_if = f"eth{if_counter[a]}"
        b_if = f"eth{if_counter[b]}"
        if_counter[a] += 1
        if_counter[b] += 1

        topo["topology"]["links"].append({
            "endpoints": [f"{a}:{a_if}", f"{b}:{b_if}"]
        })

    return topo, mgmt_ips


def dump_yaml(data, path):
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
