"""
Ansible module for managing rollback protection on Siklu EH devices.
"""

DOCUMENTATION = """
module: siklu_rollback
short_description: Manage rollback protection on Siklu EH devices
description:
  - Enable or disable rollback protection on Siklu EH devices
  - Rollback is a safety mechanism for recovery from configuration changes that may cause communication loss
  - When active, device auto-reboots to startup config if no commands are executed within timeout period
  - Highly recommended when managing remote devices over network links
version_added: "1.1.0"
options:
  state:
    description:
      - Enable or disable rollback protection
      - C(present) activates rollback with specified timeout
      - C(absent) clears rollback (confirms configuration changes)
    type: str
    choices: [ present, absent ]
    required: true
  timeout:
    description:
      - Rollback timeout in seconds (0-86400)
      - Required when I(state=present)
      - If no CLI command or Web UI action is performed within this period, device reboots to saved startup config
      - Timer resets after each command execution
    type: int
    required: false
notes:
  - Rollback protection is recommended best practice for remote device management
  - Web UI polling automatically resets the rollback timer
  - Use rollback when changing critical parameters (IP addresses, RF settings, routing)
  - Always verify device connectivity before clearing rollback
author:
  - Ceragon Networks DevOps Team
"""

EXAMPLES = """
# Basic usage: Enable rollback, apply config, verify, then clear
- name: Enable rollback protection
  siklu.eh.siklu_rollback:
    state: present
    timeout: 300

- name: Apply configuration changes
  siklu.eh.siklu_config:
    lines:
      - set ip 1 ip-addr 'static 192.168.1.100'

- name: Wait for device connectivity
  wait_for:
    host: 192.168.1.100
    port: 22
    timeout: 60
  delegate_to: localhost

- name: Confirm changes (clear rollback)
  siklu.eh.siklu_rollback:
    state: absent

# Point-to-point radio link workflow (2 devices)
- hosts: radio_link
  gather_facts: false
  tasks:
    - name: Enable rollback on both devices
      siklu.eh.siklu_rollback:
        state: present
        timeout: 600

    - name: Apply RF configuration
      siklu.eh.siklu_config:
        lines:
          - set rf tx-power 14

    - name: Verify RF link status
      siklu.eh.siklu_facts:
        gather_subset:
          - rf
      register: rf_status
      retries: 5
      delay: 10
      until: rf_status.ansible_facts.ansible_net_rf.operational == 'up'

    - name: Confirm changes on both devices
      siklu.eh.siklu_rollback:
        state: absent

# Check current rollback status
- name: Get rollback status
  siklu.eh.siklu_command:
    commands:
      - show rollback
  register: rollback_status

# Extend timeout during long configuration session
- name: Set rollback with extended timeout
  siklu.eh.siklu_rollback:
    state: present
    timeout: 1800  # 30 minutes

- name: Multiple configuration steps
  siklu.eh.siklu_config:
    lines: "{{ item }}"
  loop:
    - set system name NewHostname
    - set system contact admin@example.com
"""

RETURN = """
changed:
  description: Whether rollback state was changed
  returned: always
  type: bool
  sample: true
state:
  description: Current rollback state after operation
  returned: always
  type: str
  sample: present
timeout:
  description: Current rollback timeout in seconds (null if not active)
  returned: always
  type: int
  sample: 300
msg:
  description: Human-readable operation result
  returned: always
  type: str
  sample: "Rollback activated with 300 second timeout"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.connection_utils import (
    get_rollback_status,
    set_rollback,
    clear_rollback,
)


def main() -> None:
    """Main module execution"""
    module = AnsibleModule(
        argument_spec={
            'state': {
                'type': 'str',
                'required': True,
                'choices': ['present', 'absent']
            },
            'timeout': {
                'type': 'int',
                'required': False,
            },
        },
        required_if=[
            ('state', 'present', ['timeout']),
        ],
        supports_check_mode=True
    )

    state = module.params['state']
    timeout = module.params.get('timeout')

    # Validate timeout range
    if timeout is not None and not (0 <= timeout <= 86400):
        module.fail_json(msg='Timeout must be between 0 and 86400 seconds')

    try:
        connection = Connection(module._socket_path)

        # Get current rollback status
        current_status = get_rollback_status(connection)
        current_active = current_status['active']
        current_timeout = current_status['timeout']

        changed = False
        msg = ""

        if state == 'present':
            # User wants rollback enabled
            if current_active and current_timeout == timeout:
                # Already enabled with same timeout - idempotent
                changed = False
                msg = f"Rollback already active with {timeout} second timeout"
            else:
                # Need to set rollback (new or different timeout)
                if not module.check_mode:
                    response = set_rollback(connection, timeout)
                    
                    # Verify response indicates success
                    response_lower = response.lower()
                    if 'set done' not in response_lower and 'rollbacktimeout' not in response_lower:
                        module.fail_json(msg=f'Unexpected response from set rollback: {response}')
                
                changed = True
                if current_active:
                    msg = f"Rollback timeout changed from {current_timeout} to {timeout} seconds"
                else:
                    msg = f"Rollback activated with {timeout} second timeout"

        elif state == 'absent':
            # User wants rollback disabled
            if not current_active:
                # Already disabled - idempotent
                changed = False
                msg = "Rollback already cleared"
            else:
                # Need to clear rollback
                if not module.check_mode:
                    response = clear_rollback(connection)
                    
                    # Verify response indicates success
                    if 'rollback cleared' not in response:
                        module.fail_json(msg=f'Unexpected response from clear rollback: {response}')
                
                changed = True
                msg = f"Rollback cleared (was active with {current_timeout} second timeout)"

        # Get final status (unless in check mode)
        if not module.check_mode:
            final_status = get_rollback_status(connection)
            final_timeout = final_status['timeout']
        else:
            # In check mode, predict final state
            final_timeout = timeout if state == 'present' else None

        module.exit_json(
            changed=changed,
            state=state,
            timeout=final_timeout,
            msg=msg
        )

    except Exception as exc:
        module.fail_json(msg=f'Module execution failed: {exc}')


if __name__ == '__main__':
    main()
