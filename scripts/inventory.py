#!/usr/bin/env python3
"""Dynamic inventory script for Ansible.

Calls the FastAPI API and returns inventory in the format Ansible expects.

Usage:
    ./inventory.py --list       # Full inventory JSON
    ./inventory.py --host HOST  # Variables for a specific host
"""

import json
import sys
import urllib.request

API_URL = "http://localhost:8000/api/inventory"


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(fetch_json(API_URL), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        print(json.dumps(fetch_json(f"{API_URL}/{sys.argv[2]}"), indent=2))
    else:
        print("Usage: inventory.py --list  OR  inventory.py --host <hostname>", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
