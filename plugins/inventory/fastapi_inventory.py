"""Custom Ansible inventory plugin — fetches hosts from FastAPI API."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleParserError

DOCUMENTATION = r'''
    name: fastapi_inventory
    plugin_type: inventory
    short_description: Fetches inventory from a FastAPI REST API
    description:
        - This plugin fetches host information from a FastAPI-based API endpoint.
        - Hosts are grouped by group_name field from the API response.
        - Group variables are merged onto each host in the group.
    extends_documentation_fragment:
        - constructed
    options:
      plugin:
        description: Token that ensures this is a source file for the plugin.
        required: true
        choices: ['fastapi_inventory']
      api_url:
        description: URL of the FastAPI /api/hosts endpoint.
        type: str
        required: true
        env:
          - name: INVENTORY_API_URL
      verify_ssl:
        description: Whether to verify SSL certificates.
        type: bool
        default: true
'''

EXAMPLES = r'''
# inventory/fastapi_inventory.yml
plugin: fastapi_inventory
api_url: "http://localhost:8000/api/hosts"
cache: false
'''


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'fastapi_inventory'

    def verify_file(self, path):
        valid = False
        if super().verify_file(path):
            if path.endswith(('fastapi_inventory.yml', 'fastapi_inventory.yaml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache)
        self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        use_cache = self.get_option('cache') and cache
        hosts_data = None

        if use_cache:
            try:
                hosts_data = self._cache[cache_key]
            except KeyError:
                pass

        if hosts_data is None:
            hosts_data = self._fetch_from_api()
            if use_cache:
                self._cache[cache_key] = hosts_data

        self._populate(hosts_data)

    def _fetch_from_api(self):
        api_url = self.get_option('api_url')

        if not api_url:
            raise AnsibleParserError("api_url is required")

        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})

        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            raise AnsibleParserError("Failed to connect to API at {}: {}".format(api_url, e))
        except json.JSONDecodeError as e:
            raise AnsibleParserError("Invalid JSON from {}: {}".format(api_url, e))

        if not isinstance(data, list):
            raise AnsibleParserError("Expected a list of hosts from the API, got: {}".format(type(data)))

        return data

    def _populate(self, hosts_data):
        group_vars_cache = {}

        for host_data in hosts_data:
            hostname = host_data.get('name')
            if not hostname:
                self.display.warning("Skipping host without 'name': {}".format(host_data))
                continue

            group_name = host_data.get('group_name')

            self.inventory.add_host(hostname)

            if group_name:
                self.inventory.add_group(group_name)
                self.inventory.add_child(group_name, hostname)

                if group_name not in group_vars_cache:
                    group_vars_cache[group_name] = self._fetch_group_vars(group_name)

                for var_name, var_value in group_vars_cache[group_name].items():
                    if var_name not in host_data:
                        self.inventory.set_variable(hostname, var_name, var_value)

            for key, value in host_data.items():
                if key not in ('name', 'group_name'):
                    self.inventory.set_variable(hostname, key, value)

            strict = self.get_option('strict')
            self._set_composite_vars(
                self.get_option('compose'),
                host_data,
                hostname,
                strict=strict,
            )
            self._add_host_to_composed_groups(
                self.get_option('groups'),
                host_data,
                hostname,
                strict=strict,
            )
            self._add_host_to_keyed_groups(
                self.get_option('keyed_groups'),
                host_data,
                hostname,
                strict=strict,
            )

    def _fetch_group_vars(self, group_name):
        api_url = self.get_option('api_url')
        base_url = api_url.rsplit('/api/', 1)[0]
        groups_url = "{}/api/groups".format(base_url)

        try:
            req = urllib.request.Request(groups_url, headers={"Accept": "application/json"})
            resp = urllib.request.urlopen(req, timeout=30)
            groups = json.loads(resp.read().decode('utf-8'))

            for group in groups:
                if group.get('name') == group_name:
                    return group.get('vars', {})
        except Exception:
            pass

        return {}
