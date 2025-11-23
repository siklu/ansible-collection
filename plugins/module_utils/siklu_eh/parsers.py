"""
Parsers for Siklu EH device command outputs.

This module provides parsing functions for various Siklu EH CLI commands.
All functions are pure and side-effect free for easy testing.
"""

import re


def parse_system_info(output: str) -> dict[str, str | int | None]:
    """
    Parse 'show system' command output.

    Args:
        output: Raw output from 'show system' command

    Returns:
        Dictionary with system information:
            - model: Device model (e.g., 'EH-8010FX')
            - snmp_id: SNMP OID
            - uptime: System uptime string
            - contact: Contact name
            - name: System name
            - hostname: System hostname
            - location: System location
            - voltage: Voltage source (e.g., 'poe (injector)')
            - temperature: Temperature in Celsius (int)
            - date: System date (YYYY.MM.DD)
            - time: System time (HH:MM:SS)
            - cli_timeout: CLI session timeout in minutes (int)
            - loop_permission: Loop permission setting
            - antenna_heater: Antenna heater status
            - heartbeat_trap_period: SNMP heartbeat trap period in seconds (int)

    Example output:
        system description               : EH-8010FX
        system snmpid                    : .1.3.6.1.4.1.31926
        system uptime                    : 0000:10:38:41
        system contact                   : undefined
        system name                      : EH-8010FX
        system hostname                  : sw
        system location                  : undefined
        system voltage                   : poe (injector)
        system temperature               : 57
        system date                      : 2025.11.23
        system time                      : 18:05:00
        system cli-timeout               : 15
        system loop-permission           : mac-swap
        system antenna-heater            : disabled
        system heartbeat-trap-period     : 0
    """
    info: dict[str, str | int | None] = {}

    # Parse each field using regex patterns
    patterns = {
        'model': r'system description\s+:\s+(\S+)',
        'snmp_id': r'system snmpid\s+:\s+(\S+)',
        'uptime': r'system uptime\s+:\s+(\S+)',
        'contact': r'system contact\s+:\s+(.+)',
        'name': r'system name\s+:\s+(\S+)',
        'hostname': r'system hostname\s+:\s+(\S+)',
        'location': r'system location\s+:\s+(.+)',
        'voltage': r'system voltage\s+:\s+(.+)',
        'temperature': r'system temperature\s+:\s+(\d+)',
        'date': r'system date\s+:\s+(\S+)',
        'time': r'system time\s+:\s+(\S+)',
        'cli_timeout': r'system cli-timeout\s+:\s+(\d+)',
        'loop_permission': r'system loop-permission\s+:\s+(\S+)',
        'antenna_heater': r'system antenna-heater\s+:\s+(\S+)',
        'heartbeat_trap_period': r'system heartbeat-trap-period\s+:\s+(\d+)',
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            value = match.group(1).strip()

            # Convert to int for numeric fields
            if field in ('temperature', 'cli_timeout', 'heartbeat_trap_period'):
                info[field] = int(value)
            else:
                info[field] = value

    return info


def parse_sw_info(output: str) -> dict[str, dict[str, str | int | bool]]:
    """
    Parse 'show sw' command output.
    
    Args:
        output: Raw output from 'show sw' command
        
    Returns:
        Dictionary with keys 'running' and 'standby':
            - version: Software version string
            - bank: Bank number (1 or 2)
            - scheduled_to_run: Boolean
            - startup_config: Boolean (whether startup-config exists)
            
    Example output:
        Flash Bank    Version                           Running     Scheduled to run    startup-config  
        1             10.6.0-18451-c009ec33d1           yes         no                  exists          
        2             10.8.2-19409-92aead94fe           no          no                  missing
    """
    info: dict[str, dict[str, str | int | bool]] = {}
    
    for line in output.split('\n'):
        if 'Flash Bank' in line or not line.strip():
            continue
            
        match = re.search(
            r'^\s*(\d+)\s+(\S+)\s+(yes|no)\s+(yes|no)\s+(exists|missing)',
            line,
            re.IGNORECASE
        )
        
        if match:
            bank_num = int(match.group(1))
            version = match.group(2)
            is_running = match.group(3).lower() == 'yes'
            scheduled = match.group(4).lower() == 'yes'
            has_config = match.group(5).lower() == 'exists'
            
            bank_data = {
                'version': version,
                'bank': bank_num,
                'scheduled_to_run': scheduled,
                'startup_config': has_config,
            }
            
            if is_running:
                info['running'] = bank_data
            else:
                info['standby'] = bank_data
    
    return info


def parse_ip_config(output: str) -> dict[int, dict[str, str | int]]:
    """
    Parse 'show ip' command output.
    
    Args:
        output: Raw output from 'show ip' or 'show ip <slot>' command
        
    Returns:
        Dictionary keyed by slot number, values contain:
            - ip: IP address string
            - prefix_len: Prefix length (int)
            - vlan: VLAN ID (int)
            - default_gateway: Default gateway IP (derived field)
    """
    config: dict[int, dict[str, str | int]] = {}
    current_slot = 0
    
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        match = re.search(r'^ip\s+(\d+)\s+ip-addr\s+:\s+(?:static\s+)?(\S+)', line)
        if match:
            current_slot = int(match.group(1))
            ip_addr = match.group(2)
            config[current_slot] = {}
            config[current_slot]['ip'] = ip_addr
            continue
        
        if current_slot == 0:
            continue
        
        match = re.search(r'^ip\s+\d+\s+prefix-len\s+:\s+(\d+)', line)
        if match:
            config[current_slot]['prefix_len'] = int(match.group(1))
            continue
        
        match = re.search(r'^ip\s+\d+\s+vlan\s+:\s+(\d+)', line)
        if match:
            config[current_slot]['vlan'] = int(match.group(1))
            continue
        
        match = re.search(r'^ip\s+\d+\s+default-gateway\s+:\s+(\S+)', line)
        if match:
            config[current_slot]['default_gateway'] = match.group(1)
            continue
    
    return config


def parse_route_config(output: str) -> dict[int, dict[str, str | int]]:
    """
    Parse 'show route' command output.
    
    Args:
        output: Raw output from 'show route' or 'show route <slot>' command
        
    Returns:
        Dictionary keyed by slot number, values contain:
            - dest: Destination IP address
            - prefix_len: Prefix length (int)
            - next_hop: Next hop IP address
    """
    config: dict[int, dict[str, str | int]] = {}
    current_slot = 0
    
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        match = re.search(r'^route\s+(\d+)\s+dest\s+:\s+(\S+)', line)
        if match:
            current_slot = int(match.group(1))
            dest = match.group(2)
            config[current_slot] = {}
            config[current_slot]['dest'] = dest
            continue
        
        if current_slot == 0:
            continue
        
        match = re.search(r'^route\s+\d+\s+prefix-len\s+:\s+(\d+)', line)
        if match:
            config[current_slot]['prefix_len'] = int(match.group(1))
            continue
        
        match = re.search(r'^route\s+\d+\s+next-hop\s+:\s+(\S+)', line)
        if match:
            config[current_slot]['next_hop'] = match.group(1)
            continue
    
    return config


def validate_set_ip_response(output: str, slot: int) -> bool:
    """
    Validate 'set ip' command response.
    
    Args:
        output: Raw output from 'set ip' command
        slot: Expected slot number
        
    Returns:
        True if response indicates success, False otherwise
    """
    pattern = rf'Set done:\s+ip\s+{slot}'
    return bool(re.search(pattern, output, re.IGNORECASE))


def validate_set_route_response(output: str, slot: int) -> bool:
    """
    Validate 'set route' command response.
    
    Args:
        output: Raw output from 'set route' command
        slot: Expected slot number
        
    Returns:
        True if response indicates success, False otherwise
    """
    pattern = rf'Set done:\s+route\s+{slot}'
    return bool(re.search(pattern, output, re.IGNORECASE))


parse_show_system = parse_system_info
parse_show_sw = parse_sw_info
parse_show_ip = parse_ip_config
parse_show_route = parse_route_config
