"""
Ansible module to save configuration on Siklu EH device.
"""

DOCUMENTATION = """
module: siklu_save_config
short_description: Save running configuration to startup configuration
description:
  - Executes 'copy running-configuration startup-configuration' command
  - Commits the current running configuration to persistent storage
  - Ensures configuration survives device reboot
version_added: "1.0.0"
author:
  - Dmitry Grinberg (@siklu)
"""

EXAMPLES = """
- name: Save configuration on device
  siklu.eh.siklu_save_config:
  register: result

- name: Save config and display result
  siklu.eh.siklu_save_config:
  register: save_result

- name: Display save result
  debug:
    var: save_result.stdout
"""

RETURN = """
changed:
  description: Whether configuration was changed (always false for this command)
  returned: always
  type: bool
stdout:
  description: Output from save command
  returned: always
  type: str
msg:
  description: Status message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


def main() -> None:
    """Main module execution"""
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True
    )

    try:
        # In check mode, don't actually save
        if module.check_mode:
            module.exit_json(
                changed=False,
                msg='Configuration save skipped (check mode)',
                stdout='Would execute: copy running-configuration startup-configuration'
            )

        # Execute save command
        connection = Connection(module._socket_path)
        output = connection.get('copy running-configuration startup-configuration')

        # Parse output for success indication
        output_lower = output.lower()

        if 'error' in output_lower or 'failed' in output_lower:
            module.fail_json(
                msg='Failed to save configuration',
                stdout=output
            )

        module.exit_json(
            changed=False,
            msg='Configuration saved successfully',
            stdout=output
        )

    except Exception as exc:
        module.fail_json(msg=f'Failed to save configuration: {exc}')


if __name__ == '__main__':
    main()
