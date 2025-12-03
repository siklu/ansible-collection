"""
Ansible module for executing show commands on Siklu EH devices.
"""

DOCUMENTATION = """
module: siklu_command
short_description: Execute show commands on Siklu EH devices
description:
  - Execute show commands on Siklu EH devices via network_cli
  - Supports multiple commands in a single task
version_added: "1.0.0"
options:
  commands:
    description: List of commands to execute
    required: true
    type: list
    elements: str
author:
  - Dmitry Grinberg (Ceragon Networks)
"""

EXAMPLES = """
- name: Execute show commands
  siklu.eh.siklu_command:
    commands:
      - show system
      - show sw
      - show ip

- name: Get device information
  siklu.eh.siklu_command:
    commands:
      - show system
  register: system_info
"""

RETURN = """
stdout:
  description: Command outputs
  returned: always
  type: list
  elements: str
stdout_lines:
  description: Command outputs split by lines
  returned: always
  type: list
  elements: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


def run_commands(connection: Connection, commands: list[str]) -> list[str]:
    """
    Execute list of commands on the device.

    Args:
        connection: Ansible connection object
        commands: List of CLI commands to execute

    Returns:
        List of command outputs
    """
    responses: list[str] = []
    for cmd in commands:
        response = connection.get(cmd)
        responses.append(response)
    return responses


def main() -> None:
    """Main module execution."""
    module = AnsibleModule(
        argument_spec={
            'commands': {'type': 'list', 'required': True, 'elements': 'str'},
        },
        supports_check_mode=True
    )

    commands = module.params['commands']
    if not commands:
        module.fail_json(msg="At least one command is required")

    try:
        connection = Connection(module._socket_path)
        responses = run_commands(connection, commands)

        module.exit_json(
            changed=False,
            stdout=responses,
            stdout_lines=[r.split('\n') for r in responses]
        )
    except Exception as exc:
        module.fail_json(msg=f"Unexpected error: {exc}")


if __name__ == '__main__':
    main()
