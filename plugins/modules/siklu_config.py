"""
Ansible module for configuring Siklu EH devices.
"""

DOCUMENTATION = """
module: siklu_config
short_description: Configure IP and routes on Siklu EH devices
description:
  - Configure IP addresses and routes on Siklu EH devices
  - Idempotent - checks current configuration before making changes
  - Validates configuration after applying changes
version_added: "1.0.1"
options:
  config:
    description: List of configuration items
    type: list
    elements: dict
    suboptions:
      type:
        description: Configuration type (ip or route)
        required: true
        type: str
        choices: ['ip', 'route']
      slot:
        description: Slot number
        required: true
        type: int
      ip_address:
        description: IP address (required for type=ip)
        type: str
      prefix_len:
        description: Prefix length
        required: true
        type: int
      vlan:
        description: VLAN ID (required for type=ip)
        type: int
      dest:
        description: Destination IP (required for type=route)
        type: str
      next_hop:
        description: Next hop IP (required for type=route)
        type: str
  show:
    description: List of show commands to execute after config
    type: list
    elements: dict
author:
  - Dmitry Grinberg (Ceragon Networks)
"""

EXAMPLES = """
- name: Configure IP address
  siklu.eh.siklu_config:
    config:
      - type: ip
        slot: 3
        ip_address: 192.168.1.100
        prefix_len: 24
        vlan: 0

- name: Configure static route
  siklu.eh.siklu_config:
    config:
      - type: route
        slot: 1
        dest: 10.0.0.0
        prefix_len: 8
        next_hop: 192.168.1.1

- name: Configure and verify
  siklu.eh.siklu_config:
    config:
      - type: ip
        slot: 3
        ip_address: 192.168.1.100
        prefix_len: 24
        vlan: 0
    show:
      - type: ip
        slot: 3
"""

RETURN = """
changed:
  description: Whether any configuration was changed
  returned: always
  type: bool
results:
  description: List of configuration operation results
  returned: always
  type: list
  elements: dict
show:
  description: Output of show commands
  returned: when show parameter provided
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    validate_set_ip_response,
    validate_set_route_response,
)
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.connection_utils import (
    get_ip_info,
    get_route_info,
)


def validate_ip_config_item(item: dict) -> tuple[bool, str]:
    """
    Validate IP configuration item parameters.

    Args:
        item: Configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['slot', 'ip_address', 'prefix_len', 'vlan']
    for field in required_fields:
        if field not in item:
            return False, f'Missing required field for IP config: {field}'

    slot = item['slot']
    if not isinstance(slot, int) or slot < 0:
        return False, f'Invalid slot number: {slot}'

    prefix_len = item['prefix_len']
    if not isinstance(prefix_len, int) or not 0 <= prefix_len <= 32:
        return False, f'Invalid prefix length: {prefix_len}'

    vlan = item['vlan']
    if not isinstance(vlan, int) or not 0 <= vlan <= 4094:
        return False, f'Invalid VLAN ID: {vlan}'

    return True, ''


def validate_route_config_item(item: dict) -> tuple[bool, str]:
    """
    Validate route configuration item parameters.

    Args:
        item: Configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['slot', 'dest', 'prefix_len', 'next_hop']
    for field in required_fields:
        if field not in item:
            return False, f'Missing required field for route config: {field}'

    slot = item['slot']
    if not isinstance(slot, int) or slot < 0:
        return False, f'Invalid slot number: {slot}'

    prefix_len = item['prefix_len']
    if not isinstance(prefix_len, int) or not 0 <= prefix_len <= 32:
        return False, f'Invalid prefix length: {prefix_len}'

    return True, ''


def configure_ip(connection: Connection, item: dict) -> dict:
    """
    Configure IP address on specified slot.

    Args:
        connection: Ansible connection object
        item: Configuration parameters

    Returns:
        Result dictionary with operation status
    """
    slot = item['slot']
    ip_addr = item['ip_address']
    prefix_len = item['prefix_len']
    vlan = item['vlan']

    result: dict = {
        'type': 'ip',
        'slot': slot,
        'changed': False,
        'msg': '',
    }

    try:
        # Get current configuration using utility function
        current_config = get_ip_info(connection, slot)
        current = current_config.get(slot)

        # Check if already configured (idempotency)
        if current and (
                current.get('ip') == ip_addr and
                current.get('prefix_len') == prefix_len and
                current.get('vlan') == vlan
        ):
            result['msg'] = f'IP slot {slot} already configured correctly'
            result['config'] = current
            return result

        # Apply configuration
        cmd = f'set ip {slot} ip-addr {ip_addr} prefix-len {prefix_len} vlan {vlan}'
        set_output = connection.get(cmd)

        # Validate response
        if not validate_set_ip_response(set_output, slot):
            raise Exception(f'Failed to configure IP: {set_output}')

        # Verify configuration was applied using utility function
        updated_config = get_ip_info(connection, slot)
        updated = updated_config.get(slot, {})

        # Double-check the configuration
        if (updated.get('ip') != ip_addr or
                updated.get('prefix_len') != prefix_len or
                updated.get('vlan') != vlan):
            raise Exception(
                f'Configuration verification failed. '
                f'Expected: {ip_addr}/{prefix_len} vlan {vlan}, '
                f'Got: {updated}'
            )

        result['changed'] = True
        result['msg'] = f'IP slot {slot} configured successfully'
        result['config'] = updated

    except Exception as exc:
        result['failed'] = True
        result['msg'] = str(exc)

    return result


def configure_route(connection: Connection, item: dict) -> dict:
    """
    Configure static route on specified slot.

    Args:
        connection: Ansible connection object
        item: Configuration parameters

    Returns:
        Result dictionary with operation status
    """
    slot = item['slot']
    dest = item['dest']
    prefix_len = item['prefix_len']
    next_hop = item['next_hop']

    result: dict = {
        'type': 'route',
        'slot': slot,
        'changed': False,
        'msg': '',
    }

    try:
        # Get current configuration using utility function
        current_config = get_route_info(connection, slot)
        current = current_config.get(slot)

        # Check if already configured (idempotency)
        if current and (
                current.get('dest') == dest and
                current.get('prefix_len') == prefix_len and
                current.get('next_hop') == next_hop
        ):
            result['msg'] = f'Route slot {slot} already configured correctly'
            result['config'] = current
            return result

        # Apply configuration
        cmd = f'set route {slot} dest {dest} prefix-len {prefix_len} next-hop {next_hop}'
        set_output = connection.get(cmd)

        # Validate response
        if not validate_set_route_response(set_output, slot):
            raise Exception(f'Failed to configure route: {set_output}')

        # Verify configuration was applied using utility function
        updated_config = get_route_info(connection, slot)
        updated = updated_config.get(slot, {})

        # Double-check the configuration
        if (updated.get('dest') != dest or
                updated.get('prefix_len') != prefix_len or
                updated.get('next_hop') != next_hop):
            raise Exception(
                f'Configuration verification failed. '
                f'Expected: {dest}/{prefix_len} via {next_hop}, '
                f'Got: {updated}'
            )

        result['changed'] = True
        result['msg'] = f'Route slot {slot} configured successfully'
        result['config'] = updated

    except Exception as exc:
        result['failed'] = True
        result['msg'] = str(exc)

    return result


def execute_show_commands(connection: Connection, show_items: list[dict]) -> dict:
    """
    Execute show commands and parse outputs.

    Args:
        connection: Ansible connection object
        show_items: List of show command specifications

    Returns:
        Dictionary with parsed show command outputs
    """
    show_output: dict = {}

    for item in show_items:
        item_type = item.get('type')
        slot = item.get('slot')

        try:
            if item_type == 'ip':
                key = f'ip_slot_{slot}' if slot else 'ip_all'
                show_output[key] = get_ip_info(connection, slot)
            elif item_type == 'route':
                key = f'route_slot_{slot}' if slot else 'route_all'
                show_output[key] = get_route_info(connection, slot)
            else:
                show_output[f'error_{item_type}'] = f'Unknown show type: {item_type}'
        except Exception as exc:
            show_output[f'error_{item_type}'] = str(exc)

    return show_output


def main() -> None:
    """Main module execution"""
    module = AnsibleModule(
        argument_spec={
            'config': {
                'type': 'list',
                'elements': 'dict',
                'default': []
            },
            'show': {
                'type': 'list',
                'elements': 'dict',
                'default': []
            },
        },
        supports_check_mode=False
    )

    config_items = module.params['config']
    show_items = module.params.get('show') or []

    connection = Connection(module._socket_path)

    results: list[dict] = []
    changed = False
    show_output: dict = {}

    try:
        # Process configuration items
        for idx, item in enumerate(config_items):
            config_type = item.get('type')

            if not config_type:
                module.fail_json(
                    msg=f'Configuration item {idx} missing type field',
                    item=item
                )

            try:
                if config_type == 'ip':
                    is_valid, error_msg = validate_ip_config_item(item)
                    if not is_valid:
                        raise ValueError(error_msg)

                    result = configure_ip(connection, item)

                elif config_type == 'route':
                    is_valid, error_msg = validate_route_config_item(item)
                    if not is_valid:
                        raise ValueError(error_msg)

                    result = configure_route(connection, item)

                else:
                    raise ValueError(f'Unknown configuration type: {config_type}')

                result['index'] = idx
                results.append(result)

                if result['changed']:
                    changed = True

            except Exception as exc:
                result_item: dict = {
                    'index': idx,
                    'type': config_type,
                    'slot': item.get('slot'),
                    'changed': False,
                    'failed': True,
                    'msg': str(exc),
                }
                results.append(result_item)

        # Execute show commands if requested
        if show_items:
            show_output = execute_show_commands(connection, show_items)

        # Check if any items failed
        failed_items = [r for r in results if r.get('failed')]
        if failed_items:
            module.fail_json(
                msg=f'{len(failed_items)} configuration item(s) failed',
                results=results,
                show=show_output
            )

        module.exit_json(
            changed=changed,
            results=results,
            show=show_output
        )

    except Exception as exc:
        module.fail_json(
            msg=f'Module execution failed: {exc}',
            results=results
        )


if __name__ == '__main__':
    main()
