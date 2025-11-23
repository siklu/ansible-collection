"""
Ansible module for gathering facts from Siklu EH devices.
"""

DOCUMENTATION = """
module: siklu_facts
short_description: Gather facts from Siklu EH devices
description:
  - Gather device information including system details and software banks
  - Returns structured data parsed from device output
version_added: "1.0.0"
options:
  gather_subset:
    description: List of fact subsets to gather
    type: list
    elements: str
    default: ['all']
    choices: ['all', 'system', 'software', 'ip', 'route']
author:
  - Dmitry Grinberg (@siklu)
"""

EXAMPLES = """
- name: Gather all facts
  siklu.eh.siklu_facts:
  register: facts

- name: Gather only system facts
  siklu.eh.siklu_facts:
    gather_subset:
      - system
  register: system_facts
"""

RETURN = """
ansible_facts:
  description: Facts gathered from the device
  returned: always
  type: dict
  contains:
    ansible_net_system:
      description: System information
      returned: when system subset requested
      type: dict
    ansible_net_software:
      description: Software bank information
      returned: when software subset requested
      type: dict
    ansible_net_ip:
      description: IP configuration
      returned: when ip subset requested
      type: dict
    ansible_net_route:
      description: Route configuration
      returned: when route subset requested
      type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.connection_utils import (
    get_system_info,
    get_software_info,
    get_ip_info,
    get_route_info,
)


def main() -> None:
    """Main module execution"""
    module = AnsibleModule(
        argument_spec={
            'gather_subset': {
                'type': 'list',
                'elements': 'str',
                'default': ['all'],
                'choices': ['all', 'system', 'software', 'ip', 'route']
            },
        },
        supports_check_mode=True
    )

    gather_subset = module.params['gather_subset']

    # Convert 'all' to all available subsets
    if 'all' in gather_subset:
        gather_subset = ['system', 'software', 'ip', 'route']

    connection = Connection(module._socket_path)

    ansible_facts = {}

    try:
        # Gather requested facts using utility functions
        if 'system' in gather_subset:
            ansible_facts['ansible_net_system'] = get_system_info(connection)

        if 'software' in gather_subset:
            ansible_facts['ansible_net_software'] = get_software_info(connection)

        if 'ip' in gather_subset:
            ansible_facts['ansible_net_ip'] = get_ip_info(connection)

        if 'route' in gather_subset:
            ansible_facts['ansible_net_route'] = get_route_info(connection)

        module.exit_json(
            changed=False,
            ansible_facts=ansible_facts
        )

    except Exception as exc:
        module.fail_json(msg=f'Failed to gather facts: {exc}')


if __name__ == '__main__':
    main()
