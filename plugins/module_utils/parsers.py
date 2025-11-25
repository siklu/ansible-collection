"""
Parsing utilities for Siklu EH device output.

This module provides parsers for various CLI command outputs from Siklu EH devices.
All parsers follow a consistent pattern:
- Input: raw CLI output string
- Output: structured Python dict/list
- Handle edge cases (empty values, missing fields, special values like N/A)
"""

import re
from typing import Any


def _normalize_empty_value(value: str) -> str | None:
    """
    Normalize empty and N/A values to None.

    Args:
        value: Raw string value from CLI output

    Returns:
        None if value is empty or N/A variant, otherwise original value
    """
    if not value or value.strip() == "":
        return None
    normalized = value.strip().lower()
    if normalized in ("n/a", "default"):
        return None
    return value.strip()


def _convert_to_int(value: str) -> int | None:
    """
    Convert string to int, handling empty/N/A values.

    Args:
        value: String representation of integer

    Returns:
        Integer value or None if conversion fails or value is empty
    """
    normalized = _normalize_empty_value(value)
    if normalized is None:
        return None
    try:
        return int(normalized)
    except (ValueError, TypeError):
        return None


def _convert_to_float(value: str) -> float | None:
    """
    Convert string to float, handling empty/N/A values.

    Args:
        value: String representation of float

    Returns:
        Float value or None if conversion fails or value is empty
    """
    normalized = _normalize_empty_value(value)
    if normalized is None:
        return None
    try:
        return float(normalized)
    except (ValueError, TypeError):
        return None


def _convert_to_bool(value: str) -> bool | None:
    """
    Convert string to bool for true/false values.

    Args:
        value: String representation of boolean (true/false)

    Returns:
        Boolean value or None if not a recognized boolean string
    """
    normalized = _normalize_empty_value(value)
    if normalized is None:
        return None
    lower = normalized.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    return None


def parse_system_info(output: str) -> dict[str, Any]:
    """
    Parse 'show system' command output.

    Args:
        output: Raw output from 'show system' command

    Returns:
        Dictionary with system information
    """
    system_info = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"system\s+(\S+)\s*:\s*(.+)", line)
        if match:
            key = match.group(1).replace("-", "_")
            value = match.group(2).strip()
            system_info[key] = _normalize_empty_value(value)

    return system_info


def parse_software_info(output: str) -> dict[str, Any]:
    """
    Parse 'show software' command output.

    Args:
        output: Raw output from 'show software' command

    Returns:
        Dictionary with software information
    """
    software_info = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"software\s+(\S+)\s*:\s*(.+)", line)
        if match:
            key = match.group(1).replace("-", "_")
            value = match.group(2).strip()
            software_info[key] = _normalize_empty_value(value)

    return software_info


def parse_ip_config(output: str) -> list[dict[str, Any]]:
    """
    Parse 'show ip' command output.

    Args:
        output: Raw output from 'show ip' command

    Returns:
        List of IP configuration dictionaries
    """
    ip_configs = []
    current_slot = None
    current_config = {}

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match "ip <slot> <key> : <value>"
        match = re.match(r"ip\s+(\d+)\s+(\S+)\s*:\s*(.+)", line)
        if match:
            slot = int(match.group(1))
            key = match.group(2).replace("-", "_")
            value = match.group(3).strip()

            if current_slot != slot:
                if current_config:
                    ip_configs.append(current_config)
                current_slot = slot
                current_config = {"slot": slot}

            current_config[key] = _normalize_empty_value(value)

    if current_config:
        ip_configs.append(current_config)

    return ip_configs


def parse_route_config(output: str) -> list[dict[str, Any]]:
    """
    Parse 'show route' command output.

    Args:
        output: Raw output from 'show route' command

    Returns:
        List of route configuration dictionaries
    """
    routes = []
    current_slot = None
    current_route = {}

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match "route <slot> <key> : <value>"
        match = re.match(r"route\s+(\d+)\s+(\S+)\s*:\s*(.+)", line)
        if match:
            slot = int(match.group(1))
            key = match.group(2).replace("-", "_")
            value = match.group(3).strip()

            if current_slot != slot:
                if current_route:
                    routes.append(current_route)
                current_slot = slot
                current_route = {"slot": slot}

            current_route[key] = _normalize_empty_value(value)

    if current_route:
        routes.append(current_route)

    return routes


def parse_inventory(output: str) -> dict[str, Any]:
    """
    Parse 'show inventory' command output into hierarchical structure.

    The inventory has a tree structure where components can contain other components.
    The 'cont-in' field indicates the parent component ID (0 means root/chassis).

    Args:
        output: Raw output from 'show inventory' command

    Returns:
        Hierarchical dictionary representing the inventory tree with chassis as root
    """
    # First pass: parse all components as flat list
    components_by_id = {}
    current_id = None
    current_component = {}

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match "inventory <id> <key> : <value>"
        match = re.match(r"inventory\s+(\d+)\s+(\S+)\s*:\s*(.+)", line)
        if match:
            comp_id = int(match.group(1))
            key = match.group(2).replace("-", "_")
            value = match.group(3).strip()

            if current_id != comp_id:
                if current_component:
                    components_by_id[current_id] = current_component
                current_id = comp_id
                current_component = {"id": comp_id}

            # Type conversions
            if key == "cont_in" or key == "rel_pos":
                current_component[key] = _convert_to_int(value)
            elif key == "fru":
                current_component[key] = _convert_to_bool(value)
            else:
                current_component[key] = _normalize_empty_value(value)

    if current_component:
        components_by_id[current_id] = current_component

    # Second pass: build hierarchical structure
    def build_hierarchy(parent_id: int) -> list[dict[str, Any]]:
        """Recursively build component hierarchy."""
        children = []
        for comp_id, component in components_by_id.items():
            if component.get("cont_in") == parent_id:
                comp_copy = component.copy()
                # Add nested components
                nested = build_hierarchy(comp_id)
                if nested:
                    comp_copy["components"] = nested
                children.append(comp_copy)
        # Sort by rel_pos if available
        children.sort(key=lambda x: x.get("rel_pos", 999))
        return children

    # Find chassis (cont_in == 0)
    chassis = None
    for comp_id, component in components_by_id.items():
        if component.get("cont_in") == 0:
            chassis = component.copy()
            chassis["components"] = build_hierarchy(comp_id)
            break

    return {"chassis": chassis} if chassis else {}


def parse_rf_status(output: str) -> dict[str, Any]:
    """
    Parse 'show rf' command output.

    Args:
        output: Raw output from 'show rf' command

    Returns:
        Dictionary with RF status information with appropriate type conversions
    """
    rf_status = {}

    # Fields that should be converted to int
    int_fields = {
        "tx_frequency",
        "rx_frequency",
        "channel_width",
        "tx_mute_timeout",
        "tx_power",
        "loopback_timeout",
        "air_capacity",
    }

    # Fields that should be converted to float
    float_fields = {"cinr", "rssi"}

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match "rf <key> : <value>"
        match = re.match(r"rf\s+(\S+)\s*:\s*(.+)", line)
        if match:
            key = match.group(1).replace("-", "_")
            value = match.group(2).strip()

            # Apply type conversions
            if key in int_fields:
                rf_status[key] = _convert_to_int(value)
            elif key in float_fields:
                rf_status[key] = _convert_to_float(value)
            else:
                # Keep as string, but normalize empty/N/A
                rf_status[key] = _normalize_empty_value(value)

    return rf_status


def parse_configuration(output: str) -> str:
    """
    Parse configuration output from 'copy running-configuration display' or
    'copy startup-configuration display'.

    Args:
        output: Raw configuration output

    Returns:
        Raw configuration as string (minimal processing - just strip empty lines)
    """
    # Remove leading/trailing whitespace and excessive blank lines
    lines = []
    for line in output.splitlines():
        stripped = line.rstrip()
        # Keep comment lines and non-empty lines
        if stripped:
            lines.append(stripped)

    return "\n".join(lines)
