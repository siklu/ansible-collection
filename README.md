# Siklu EH Ansible Collection

## Overview

This Ansible collection provides production-grade automation for Siklu by Ceragon EtherHaul (EH8010/EH8020) millimeter-wave radio devices.

- Modern Python 3.11+ code
- Style inspired by Cisco/NetCommon collections
- Best-practices for DevOps and production rollout
- High test coverage: unit tests and integration playbooks

Supports:
- Inventory, facts, configuration (idempotent)
- Remote CLI execution
- Hardware inventory audit (hierarchical)
- RF radio metrics & link monitoring
- Full configuration backup/restore
- **Rollback protection for safe remote configuration**
- Multi-vendor interoperability (Ansible best practices)

## Important: Rollback Protection

**When managing Siklu devices, always use rollback protection to prevent loss of connectivity.**

The `siklu_rollback` module provides automatic recovery if configuration changes break network access. Without rollback, a misconfigured IP address or RF parameter can permanently disconnect a remote device.

**Recommended workflow:**
```yaml
# 1. Enable rollback before changes
- siklu.eh.siklu_rollback:
    state: present
    timeout: 300

# 2. Apply configuration
- siklu.eh.siklu_config:
    lines: [your changes]

# 3. Verify connectivity
- wait_for:
    host: "{{ ansible_host }}"
    port: 22

# 4. Confirm changes (clear rollback)
- siklu.eh.siklu_rollback:
    state: absent
```

See [Rollback Protection](#siklu_rollback) section for detailed usage.

## Features

- Gather device facts (`siklu_facts`):
  - System and software info
  - IP and routing config
  - Hierarchical hardware inventory
  - RF radio status and metrics
  - Running and startup configuration reading capability
- Show and set commands via `siklu_command`
- Configuration tasks via `siklu_config`
- **Rollback protection via `siklu_rollback`** (prevents connectivity loss)
- Idempotency and safety (with rollback workflows)
- Full documentation and type hints


## Requirements
- Ansible >= 2.12
- Python >= 3.11
- Accessible Siklu EH80XX device(s) via SSH (uses ansible.netcommon.network_cli connection)


## Installation

```bash
ansible-galaxy collection install siklu.eh
# or from local source
ansible-galaxy collection build --force
ansible-galaxy collection install siklu-eh-*.tar.gz --force
```

## Usage Examples

### Gathering Default Facts (Excludes Config)
```yaml
- hosts: siklu_devices
  gather_facts: false
  tasks:
    - name: Gather default facts
      siklu.eh.siklu_facts:
      register: facts
```

### Gathering Inventory and RF Metrics
```yaml
- hosts: siklu_devices
  gather_facts: false
  tasks:
    - name: Get hardware inventory
      siklu.eh.siklu_facts:
        gather_subset:
          - inventory
      register: inv

    - name: Get RF status
      siklu.eh.siklu_facts:
        gather_subset:
          - rf
      register: rf

    - name: Show inventory and RF
      debug:
        msg: |
          Model: {{ inv.ansible_facts.ansible_net_inventory.chassis.model_name | default('N/A') }}
          Serial: {{ inv.ansible_facts.ansible_net_inventory.chassis.serial | default('N/A') }}
          RF status: {{ rf.ansible_facts.ansible_net_rf.operational | default('Unknown') }}
          CINR: {{ rf.ansible_facts.ansible_net_rf.cinr | default('N/A') }} dB
```

### Configuration Backup
```yaml
- hosts: siklu_devices
  gather_facts: false
  tasks:
    - name: Backup running config
      siklu.eh.siklu_facts:
        gather_subset:
          - config
      register: config

    - name: Save to file
      copy:
        content: "{{ config.ansible_facts.ansible_net_config }}"
        dest: "/tmp/{{ inventory_hostname }}_config.txt"
      delegate_to: localhost
```

### RF Link Monitoring
```yaml
- hosts: siklu_devices
  gather_facts: false
  tasks:
    - name: Gather RF metrics
      siklu.eh.siklu_facts:
        gather_subset:
          - rf
      register: rf_status

    - name: Assert RF link quality
      assert:
        that:
          - rf_status.ansible_facts.ansible_net_rf.operational == 'up'
          - rf_status.ansible_facts.ansible_net_rf.cinr | float > 10.0
          - rf_status.ansible_facts.ansible_net_rf.rssi | float > -70.0
        msg: "RF link quality below minimum required"
```

## Module Reference

### siklu_facts

Gather facts from Siklu device:
- `inventory`: hierarchical hardware inventory tree
- `rf`: RF operational and quality metrics
- `config`: running configuration backup
- `config_startup`: startup configuration backup
- Note: `config` and `config_startup` require explicit gather_subset (not in 'all')

**Examples:**
```yaml
- siklu.eh.siklu_facts:
    gather_subset: [rf, inventory, config]
  register: facts

- siklu.eh.siklu_facts:
    gather_subset: [config, config_startup]
  register: configs
```

**Facts Structure:**

- `ansible_net_system`: hostname, model, contact, location, ...
- `ansible_net_software`: running/standby software bank
- `ansible_net_ip`: per slot
- `ansible_net_route`: per slot
- `ansible_net_inventory`: hierarchical hardware tree
- `ansible_net_rf`: link status, CINR/RSSI, frequency, mode
- `ansible_net_config`: running config

---

### siklu_rollback

**CRITICAL: Use rollback protection for all remote device configuration to prevent connectivity loss.**

Manage rollback protection on Siklu devices. Rollback is a safety mechanism that automatically reboots the device to saved startup configuration if no commands are executed within the timeout period.

**When rollback is active:**
- Timer resets after each CLI command or Web UI action
- If timer expires, device automatically reboots to startup config
- Prevents permanent loss of access from misconfiguration

**Use rollback when:**
- Changing IP addresses on remote devices
- Modifying RF parameters (frequency, power, modulation)
- Updating routing configuration
- Any changes that could break network connectivity
- **Recommended for ALL remote device management**

**Parameters:**
- `state`: `present` (enable rollback) or `absent` (clear/confirm changes)
- `timeout`: Rollback timeout in seconds (0-86400, required when state=present)

**Basic Usage:**
```yaml
# Enable rollback protection
- name: Enable rollback with 5 minute timeout
  siklu.eh.siklu_rollback:
    state: present
    timeout: 300

# Apply configuration changes
- name: Change IP address
  siklu.eh.siklu_config:
    lines:
      - set ip 1 ip-addr 'static 192.168.1.100'

# Verify connectivity
- name: Wait for device on new IP
  wait_for:
    host: 192.168.1.100
    port: 22
    timeout: 60
  delegate_to: localhost

# Confirm changes (clear rollback)
- name: Clear rollback protection
  siklu.eh.siklu_rollback:
    state: absent
```

**Point-to-Point Link Workflow (2 devices):**
```yaml
- hosts: radio_link
  gather_facts: false
  tasks:
    # Enable rollback on both devices
    - name: Enable rollback protection
      siklu.eh.siklu_rollback:
        state: present
        timeout: 600

    # Apply configuration to both
    - name: Change RF settings
      siklu.eh.siklu_config:
        lines:
          - set rf tx-power 14

    # Verify RF link on both devices
    - name: Verify RF link status
      siklu.eh.siklu_facts:
        gather_subset: [rf]
      register: rf_status
      retries: 5
      delay: 10
      until: rf_status.ansible_facts.ansible_net_rf.operational == 'up'

    # Confirm on both devices
    - name: Clear rollback protection
      siklu.eh.siklu_rollback:
        state: absent
```

**Error Handling with Rollback:**
```yaml
- hosts: remote_device
  gather_facts: false
  tasks:
    - block:
        - name: Enable rollback protection
          siklu.eh.siklu_rollback:
            state: present
            timeout: 300

        - name: Apply configuration
          siklu.eh.siklu_config:
            lines:
              - set ip 1 ip-addr 'static {{ new_ip }}'

        - name: Verify connectivity
          wait_for:
            host: "{{ new_ip }}"
            port: 22
            timeout: 120
          delegate_to: localhost

        - name: Confirm if successful
          siklu.eh.siklu_rollback:
            state: absent

      rescue:
        - name: Config failed - rollback will auto-revert
          debug:
            msg: "Device will auto-reboot to startup config in {{ rollback_timeout }}s"
```

**Best Practices:**
1. Always use rollback for remote devices
2. Choose appropriate timeout (5-10 min single device, 10-30 min multi-device)
3. Verify connectivity before clearing rollback
4. Use block/rescue for error handling

---

### siklu_command

Execute show commands on Siklu devices via network_cli connection.

**Examples:**
```yaml
- name: Execute show commands
  siklu.eh.siklu_command:
    commands:
      - show system
      - show sw
      - show ip
  register: output
```

---

### siklu_config

Configure Siklu devices with idempotent configuration management.

**Examples:**
```yaml
- name: Configure system settings
  siklu.eh.siklu_config:
    lines:
      - set system name MyDevice
      - set system contact admin@example.com
```

---

## Testing

### Unit Tests (`pytest`)

**Requires:** `pytest`

```bash
pytest tests/unit/test_parsers.py -v
```

Tested:
- Helpers: value normalization/type conversion
- Inventory parser (nested tree, fields)
- RF parser (numeric and string fields, edge cases)
- Config parser (structure, comment preservation)
- Rollback parser (status and timeout parsing)

### Integration Test Playbooks

```bash
# Parser unit tests
pytest tests/unit/test_parsers.py -v

# Facts gathering integration tests
ansible-playbook test_facts.yaml -i inventory.ini -v

# Rollback protection integration tests
ansible-playbook test_rollback.yaml -i inventory.ini -v
```

**Coverage:**
- All parsing functions with real device output
- Type conversions and edge cases
- Hierarchical data structures
- Live device fact gathering (system, software, IP, routes, inventory, RF, config)
- Rollback enable/disable operations and idempotency
- Error handling and validation

## Authors
- Ceragon Networks DevOps Team
