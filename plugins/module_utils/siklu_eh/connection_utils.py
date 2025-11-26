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
    parse_rollback_status,
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

def get_rollback_status(connection: Connection) -> dict:
    """
    Get and parse rollback status.

    Args:
        connection: Ansible connection object

    Returns:
        Parsed rollback status dictionary with keys:
        - active: bool (True if rollback timer is running)
        - timeout: int | None (timeout in seconds, None if not started)
    """
    output = connection.get('show rollback')
    return parse_rollback_status(output)


def set_rollback(connection: Connection, timeout: int) -> str:
    """
    Activate rollback protection with specified timeout.

    Args:
        connection: Ansible connection object
        timeout: Rollback timeout in seconds (0-86400)

    Returns:
        Command response string (e.g., "Set done: rollbacktimeout: 9000")

    Raises:
        Exception: If command execution fails
    """
    cmd = f'set rollback timeout {timeout}'
    response = connection.get(cmd)
    return response


def clear_rollback(connection: Connection) -> str:
    """
    Clear rollback protection (confirm configuration changes).

    Args:
        connection: Ansible connection object

    Returns:
        Command response string (e.g., "rollback cleared")

    Raises:
        Exception: If command execution fails
    """
    response = connection.get('clear rollback')
    return response
