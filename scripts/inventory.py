#!/usr/bin/env python3
"""Ansible exec_vars inventory script — calls FastAPI API.

Usage:
    ./inventory.py --list       # Full inventory JSON
    ./inventory.py --host HOST  # Variables for a specific host
"""

import json
import sys
import urllib.request

API_BASE = "http://localhost:8000"


def fetch(path):
    with urllib.request.urlopen(API_BASE + path, timeout=30) as resp:
        return json.loads(resp.read().decode())


def get_list():
    hosts = fetch("/api/hosts")
    groups = fetch("/api/groups")

    groups_map = {g["name"]: g for g in groups}
    grouped = {}
    for host in hosts:
        gname = host.get("group_name", "ungrouped")
        grouped.setdefault(gname, []).append(host["name"])

    inventory = {"_meta": {"hostvars": {}}}

    for gname, gvars in groups_map.items():
        inventory[gname] = {
            "hosts": grouped.get(gname, []),
            "vars": gvars.get("vars", {}),
        }

    if "ungrouped" in grouped:
        inventory["ungrouped"] = {"hosts": grouped["ungrouped"]}

    for host in hosts:
        hostvars = {k: v for k, v in host.items() if k != "group_name"}
        inventory["_meta"]["hostvars"][host["name"]] = hostvars

    return inventory


def get_host(hostname):
    hosts = fetch("/api/hosts")
    for h in hosts:
        if h["name"] == hostname:
            return {k: v for k, v in h.items() if k != "group_name"}
    return {}


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(get_list(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps(get_host(sys.argv[2]), indent=2))
    else:
        print("Usage: inventory.py --list  OR  inventory.py --host <hostname>", file=sys.stderr)
        sys.exit(1)
