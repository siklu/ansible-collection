"""
Siklu EH Facts Module

This module gathers facts from Siklu EH devices including system information,
software version, IP configuration, routes, inventory, RF status, and configuration.
"""

DOCUMENTATION = r"""
---
module: siklu_facts
short_description: Gather facts from Siklu EH devices
description:
  - Gathers comprehensive device facts from Siklu EH radio devices
  - Supports multiple fact subsets including system, software, IP, routes, inventory, RF, and config
  - All gathered facts are returned under ansible_facts with 'ansible_net_' prefix
version_added: "1.0.1"
options:
  gather_subset:
    description:
      - List of fact subsets to gather
      - Use 'all' to gather all available facts except 'config' and 'config_startup'
      - 'config' and 'config_startup' must be explicitly requested due to potentially large output
    type: list
    elements: str
    default: ['all']
    choices:
      - all
      - system
      - software
      - ip
      - route
      - inventory
      - rf
      - config
      - config_startup
author:
  - Ceragon Networks DevOps Team
notes:
  - The 'config' and 'config_startup' subsets are not included in 'all' and must be explicitly requested
  - RF status shows real-time radio link state and signal quality
  - Inventory provides hierarchical view of hardware components
  - Config subsets return raw configuration in set-command format
"""

EXAMPLES = r"""
# Gather all facts (excluding config)
- name: Gather all device facts
  siklu.eh.siklu_facts:
  register: device_facts

# Gather specific fact subsets
- name: Gather system and software info
  siklu.eh.siklu_facts:
    gather_subset:
      - system
      - software
  register: basic_info

# Gather RF status for link monitoring
- name: Check RF link status
  siklu.eh.siklu_facts:
    gather_subset:
      - rf
  register: rf_status

- name: Display RF operational state
  debug:
    msg: "RF link is {{ rf_status.ansible_facts.ansible_net_rf.operational }}"

# Gather inventory for hardware audit
- name: Get hardware inventory
  siklu.eh.siklu_facts:
    gather_subset:
      - inventory
  register: hw_inventory

# Gather running configuration
- name: Backup running configuration
  siklu.eh.siklu_facts:
    gather_subset:
      - config
  register: running_config

- name: Save running config to file
  copy:
    content: "{{ running_config.ansible_facts.ansible_net_config }}"
    dest: "./backup/{{ inventory_hostname }}_running.txt"

# Gather startup configuration
- name: Backup startup configuration
  siklu.eh.siklu_facts:
    gather_subset:
      - config_startup
  register: startup_config

# Gather both configurations for comparison
- name: Compare running vs startup
  siklu.eh.siklu_facts:
    gather_subset:
      - config
      - config_startup
  register: configs

- name: Check if configs differ
  debug:
    msg: "WARNING: Running and startup configs are different!"
  when: configs.ansible_facts.ansible_net_config != configs.ansible_facts.ansible_net_config_startup
"""

RETURN = r"""
ansible_facts:
  description: Dictionary of facts gathered from device
  returned: always
  type: dict
  contains:
    ansible_net_system:
      description: System information
      returned: when 'system' or 'all' in gather_subset
      type: dict
      sample: {
        "name": "EH-8010FX-AES-H",
        "hostname": "sw",
        "location": "undefined",
        "contact": "undefined"
      }
    ansible_net_software:
      description: Software version information
      returned: when 'software' or 'all' in gather_subset
      type: dict
      sample: {
        "running": {
          "version": "10.8.2-19419-f50a23d53d",
          "bank": 1,
          "scheduled_to_run": false,
          "startup_config": true
        },
        "standby": {
          "version": "10.6.0-18451-c009ec33d1",
          "bank": 2,
          "scheduled_to_run": false,
          "startup_config": false
        }
      }
    ansible_net_ip:
      description: IP configuration for all slots
      returned: when 'ip' or 'all' in gather_subset
      type: dict
      sample: {
        1: {
          "ip": "172.18.128.2",
          "prefix_len": 24,
          "vlan": 128,
          "default_gateway": "172.18.128.1"
        }
      }
    ansible_net_route:
      description: Static routes configuration
      returned: when 'route' or 'all' in gather_subset
      type: dict
      sample: {
        1: {
          "dest": "0.0.0.0",
          "prefix_len": 0,
          "next_hop": "172.18.128.1"
        }
      }
    ansible_net_inventory:
      description: Hardware inventory in hierarchical structure
      returned: when 'inventory' in gather_subset
      type: dict
      sample: {
        "chassis": {
          "id": 1,
          "desc": "EH-8010FX-AES-H",
          "serial": "FC18594555",
          "hw_rev": "D1",
          "sw_rev": "10.8.2-19419-f50a23d53d",
          "components": [
            {
              "id": 2,
              "desc": "BB Board",
              "serial": "FC17588055",
              "components": []
            }
          ]
        }
      }
    ansible_net_rf:
      description: RF radio status and configuration
      returned: when 'rf' in gather_subset
      type: dict
      sample: {
        "operational": "up",
        "tx_state": "normal",
        "rx_state": "normal",
        "cinr": 28.0,
        "rssi": -28.0,
        "tx_frequency": 82000,
        "rx_frequency": 72000,
        "channel_width": 250,
        "mode": "adaptive qam32"
      }
    ansible_net_config:
      description: Running device configuration in set-command format
      returned: when 'config' in gather_subset
      type: str
      sample: "####====#### Generated by ver. 10.8.2\\nset license data-rate config 10000\\n..."
    ansible_net_config_startup:
      description: Startup device configuration in set-command format
      returned: when 'config_startup' in gather_subset
      type: str
      sample: "####====#### Generated by ver. 10.8.2\\nset license data-rate config 10000\\n..."
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    parse_system_info,
    parse_sw_info,
    parse_ip_config,
    parse_route_config,
    parse_inventory,
    parse_rf_status,
    parse_configuration,
)


class FactsGatherer:
    """Orchestrates gathering of device facts across multiple subsets."""

    VALID_SUBSETS = {
        "system",
        "software",
        "ip",
        "route",
        "inventory",
        "rf",
        "config",
        "config_startup",
        "all",
    }

    # Subsets included when 'all' is specified (config excluded by default)
    DEFAULT_SUBSETS = {"system", "software", "ip", "route"}

    def __init__(self, module: AnsibleModule):
        """
        Initialize facts gatherer.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.connection = Connection(module._socket_path)
        self.facts = {}

    def validate_gather_subset(self, gather_subset: list[str]) -> list[str]:
        """
        Validate and normalize gather_subset parameter.

        Args:
            gather_subset: List of requested subsets

        Returns:
            Validated and normalized list of subsets to gather
        """
        if not gather_subset:
            gather_subset = ["all"]

        # Check for invalid subsets
        invalid = set(gather_subset) - self.VALID_SUBSETS
        if invalid:
            self.module.fail_json(
                msg=f"Invalid gather_subset values: {', '.join(invalid)}. "
                f"Valid values: {', '.join(sorted(self.VALID_SUBSETS))}"
            )

        # Expand 'all' to default subsets
        if "all" in gather_subset:
            gather_subset = list(self.DEFAULT_SUBSETS)

        return gather_subset

    def run_command(self, command: str) -> str:
        """
        Execute command on device via connection plugin.

        Args:
            command: CLI command to execute

        Returns:
            Command output as string

        Raises:
            Exception on command execution failure
        """
        try:
            output = self.connection.get(command)
            return output
        except ConnectionError as exc:
            raise Exception(f"Connection error executing '{command}': {str(exc)}") from exc
        except Exception as exc:
            raise Exception(f"Failed to execute '{command}': {str(exc)}") from exc


    def gather_system_facts(self) -> None:
        """Gather system information facts."""
        output = self.run_command("show system")
        self.facts["ansible_net_system"] = parse_system_info(output)

    def gather_software_facts(self) -> None:
        """Gather software version facts."""
        output = self.run_command("show sw")
        self.facts["ansible_net_software"] = parse_sw_info(output)

    def gather_ip_facts(self) -> None:
        """Gather IP configuration facts."""
        output = self.run_command("show ip")
        self.facts["ansible_net_ip"] = parse_ip_config(output)

    def gather_route_facts(self) -> None:
        """Gather routing configuration facts."""
        output = self.run_command("show route")
        self.facts["ansible_net_route"] = parse_route_config(output)

    def gather_inventory_facts(self) -> None:
        """Gather hardware inventory facts."""
        output = self.run_command("show inventory")
        self.facts["ansible_net_inventory"] = parse_inventory(output)

    def gather_rf_facts(self) -> None:
        """Gather RF radio status facts."""
        output = self.run_command("show rf")
        self.facts["ansible_net_rf"] = parse_rf_status(output)

    def gather_config_facts(self) -> None:
        """Gather running device configuration facts."""
        output = self.run_command("copy running-configuration display")
        self.facts["ansible_net_config"] = parse_configuration(output)

    def gather_config_startup_facts(self) -> None:
        """Gather startup device configuration facts."""
        output = self.run_command("copy startup-configuration display")
        self.facts["ansible_net_config_startup"] = parse_configuration(output)

    def gather_facts(self, gather_subset: list[str]) -> dict:
        """
        Gather all requested fact subsets.

        Args:
            gather_subset: List of subsets to gather

        Returns:
            Dictionary of gathered facts
        """
        subset_methods = {
            "system": self.gather_system_facts,
            "software": self.gather_software_facts,
            "ip": self.gather_ip_facts,
            "route": self.gather_route_facts,
            "inventory": self.gather_inventory_facts,
            "rf": self.gather_rf_facts,
            "config": self.gather_config_facts,
            "config_startup": self.gather_config_startup_facts,
        }

        for subset in gather_subset:
            if subset in subset_methods:
                try:
                    subset_methods[subset]()
                except Exception as exc:
                    # Use module.warn() instead of warnings list
                    self.module.warn(f"Failed to gather {subset} facts: {str(exc)}")

        return self.facts


def main():
    """Main module execution."""
    argument_spec = {
        "gather_subset": {
            "type": "list",
            "elements": "str",
            "default": ["all"],
            "choices": list(FactsGatherer.VALID_SUBSETS),
        }
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    gatherer = FactsGatherer(module)
    gather_subset = gatherer.validate_gather_subset(module.params["gather_subset"])

    facts = gatherer.gather_facts(gather_subset)

    result = {
        "changed": False,
        "ansible_facts": facts,
    }

    module.exit_json(**result)


if __name__ == "__main__":
    main()
