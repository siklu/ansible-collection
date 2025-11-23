"""
Cliconf plugin for Siklu EH devices
"""

DOCUMENTATION = """
name: siklu_eh
short_description: Use siklu_eh cliconf to run commands on Siklu EH devices
description:
  - This plugin provides CLI interactions with Siklu EH devices
version_added: "1.0.0"
"""

import json
from ansible.module_utils.common.text.converters import to_text
from ansible_collections.ansible.netcommon.plugins.plugin_utils.cliconf_base import CliconfBase
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.connection_utils import (
    get_system_info,
    get_software_info,
)


class Cliconf(CliconfBase):
    """
    Cliconf plugin for Siklu EH devices
    """

    def get_device_info(self) -> dict[str, str]:
        """
        Retrieve device information including model, hostname, and version.

        Returns:
            Dictionary containing device identification information
        """
        device_info: dict[str, str] = {'network_os': 'siklu_eh'}

        try:
            # Get system information using utility function
            system_info = get_system_info(self)

            # Map system info to device info
            if 'model' in system_info and system_info['model']:
                device_info['network_os_model'] = system_info['model']
            if 'hostname' in system_info and system_info['hostname']:
                device_info['network_os_hostname'] = system_info['hostname']
            if 'name' in system_info and system_info['name']:
                device_info['network_os_name'] = system_info['name']

            # Get software version information using utility function
            sw_info = get_software_info(self)

            if 'running' in sw_info and 'version' in sw_info['running']:
                device_info['network_os_version'] = sw_info['running']['version']

        except Exception as exc:
            # Log error but return partial info
            self._connection.queue_message('warning',
                                           f'Failed to retrieve complete device info: {exc}')

        return device_info

    def get_config(
            self,
            source: str = 'running',
            flags: list[str] | None = None,
            format: str | None = None
    ) -> str:
        """
        Get configuration - not applicable for Siklu EH.

        Siklu EH devices don't support traditional config retrieval.
        """
        return ""

    def edit_config(
            self,
            candidate: str | None = None,
            commit: bool = True,
            replace: str | None = None,
            comment: str | None = None,
            **kwargs
    ) -> dict:
        """
        Edit configuration - not applicable for Siklu EH.

        Use siklu_config module for configuration changes.
        """
        return {}

    def get(
            self,
            command: str | None = None,
            prompt: str | None = None,
            answer: str | None = None,
            sendonly: bool = False,
            newline: bool = True,
            check_all: bool = False,
            **kwargs
    ) -> str:
        """
        Execute show command on the device.

        Args:
            command: CLI command to execute
            prompt: Expected prompt pattern
            answer: Answer to provide if prompted
            sendonly: Send command without waiting for response
            newline: Append newline to command
            check_all: Check all prompts

        Returns:
            Command output as string
        """
        return self.send_command(
            command=command,
            prompt=prompt,
            answer=answer,
            sendonly=sendonly,
            newline=newline,
            check_all=check_all
        )

    def get_capabilities(self) -> str:
        """
        Get device capabilities including supported RPC methods.

        Returns:
            JSON string with capability information
        """
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        return json.dumps(result)

    @staticmethod
    def get_base_rpc() -> list[str]:
        """
        Get list of supported RPC methods.

        Returns:
            List of RPC method names
        """
        return [
            'get_config',
            'edit_config',
            'get_capabilities',
            'get',
        ]
