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
- Multi-vendor interoperability (Ansible best practices)


## Features

- Gather device facts (`siklu_facts`):
  - System and software info
  - IP and routing config
  - Hierarchical hardware inventory
  - RF radio status and metrics
  - Running and startup configuration reading capability
- Show and set commands via `siklu_command`
- Configuration tasks via `siklu_config`
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
          Model: {{ inv.ansible_facts.ansible_net_inventory.chassis.model_name }}
          Serial: {{ inv.ansible_facts.ansible_net_inventory.chassis.serial }}
          RF status: {{ rf.ansible_facts.ansible_net_rf.operational }}
          CINR: {{ rf.ansible_facts.ansible_net_rf.cinr }} dB
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

## Module Reference (excerpts)

### siklu_facts

Gather facts from Siklu device:
- `inventory`: hierarchical hardware inventory tree
- `rf`: RF operational and quality metrics
- `config`: running configuration backup
- `config_startup`: startup configuration backup
- Note: `config` and `config_startup` require explicit gather_subset (not in 'all')

# Examples:
```yaml
- siklu.eh.siklu_facts:
  gather_subset: [rf, inventory, config]
  register: facts

- siklu.eh.siklu_facts:
  gather_subset: [config, config_startup]
  register: configs
```

### Facts Structure

- `ansible_net_system`: hostname, model, contact, location, ...
- `ansible_net_software`: running/standby software bank
- `ansible_net_ip`: per slot
- `ansible_net_route`: per slot
- `ansible_net_inventory`: hierarchical hardware tree
- `ansible_net_rf`: link status, CINR/RSSI, frequency, mode
- `ansible_net_config`: running config

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

### Integration Test Playbook

```bash
pytest tests/unit/test_parsers.py -v # Parser unit tests
ansible-playbook test_facts.yaml -i inventory.ini -v # Integration tests
```

**Coverage:**
- All parsing functions with real device output
- Type conversions and edge cases
- Hierarchical data structures
- Live device fact gathering (system, software, IP, routes, inventory, RF, config)
- Error handling and validation

## Authors
- Ceragon Networks DevOps Team
