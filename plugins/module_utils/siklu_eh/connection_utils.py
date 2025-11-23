"""
Connection utilities for Siklu EH devices.

Reusable functions for fetching and parsing device information.
"""

from ansible.module_utils.connection import Connection
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    parse_system_info,
    parse_sw_info,
    parse_ip_config,
    parse_route_config,
)


def get_system_info(connection: Connection) -> dict:
    """
    Get and parse system information.

    Args:
        connection: Ansible connection object

    Returns:
        Parsed system information dictionary
    """
    output = connection.get('show system')
    return parse_system_info(output)


def get_software_info(connection: Connection) -> dict:
    """
    Get and parse software bank information.

    Args:
        connection: Ansible connection object

    Returns:
        Parsed software bank information dictionary
    """
    output = connection.get('show sw')
    return parse_sw_info(output)


def get_ip_info(connection: Connection, slot: int | None = None) -> dict:
    """
    Get and parse IP configuration.

    Args:
        connection: Ansible connection object
        slot: Optional slot number, if None returns all slots

    Returns:
        Parsed IP configuration dictionary
    """
    cmd = f'show ip {slot}' if slot is not None else 'show ip'
    output = connection.get(cmd)
    return parse_ip_config(output)


def get_route_info(connection: Connection, slot: int | None = None) -> dict:
    """
    Get and parse route configuration.

    Args:
        connection: Ansible connection object
        slot: Optional slot number, if None returns all slots

    Returns:
        Parsed route configuration dictionary
    """
    cmd = f'show route {slot}' if slot is not None else 'show route'
    output = connection.get(cmd)
    return parse_route_config(output)
