# Siklu EH Ansible Collection

[![Ansible Collection](https://img.shields.io/badge/collection-siklu.eh-blue)](https://github.com/siklu/ansible-collection)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ansible](https://img.shields.io/badge/ansible-%3E%3D2.20.0-blue.svg)](https://www.ansible.com/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg)](https://www.python.org/)

Professional Ansible Collection for managing and configuring Siklu by Ceragon EtherHaul millimeter-wave radio devices.

## Features

- ✅ Execute show commands (`siklu_command`)
- ✅ Configure IP addresses and routes (`siklu_config`)
- ✅ Gather device facts (`siklu_facts`)
- ✅ Save configuration (`siklu_save_config`)
- ✅ Idempotent operations with verification
- ✅ Full type hints and documentation
- ✅ Comprehensive test playbooks
- ✅ Production-ready code

## Quick Start

### Install collection

```bash
ansible-galaxy collection install siklu.eh
```

### Create inventory

```ini
[siklu_devices]
eh8010 ansible_host=10.0.101.2

[siklu_devices:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=siklu.eh.siklu_eh
ansible_user=admin
ansible_password=admin
```

### Run playbook

```bash
ansible-playbook playbook.yaml -i inventory.ini
```

## Installation

### Requirements

- **ansible-core** >= 2.20.0
- **ansible-pylibssh** >= 1.3.0
- **Python** >= 3.11
- **ansible.netcommon** >= 8.1.0

### Install from Galaxy

```bash
ansible-galaxy collection install siklu.eh
```

### Install from source

```bash
git clone https://github.com/siklu/ansible-collection.git
cd ansible-collection
ansible-galaxy collection build --force
ansible-galaxy collection install siklu-eh-*.tar.gz
```

### Development setup

```bash
git clone https://github.com/siklu/ansible-collection.git
cd ansible-collection
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
ansible-galaxy collection install -r requirements-galaxy.yml
make install
```

## Supported Devices

- Siklu EH8010FX
- Siklu EH8020FX

## Included Content

### Modules

| Module | Description |
|--------|-------------|
| `siklu_command` | Execute device commands (show) |
| `siklu_config` | Configure device (IP addresses, routes) |
| `siklu_facts` | Gather device facts (system info, software, IP, routes) |
| `siklu_save_config` | Save configuration to startup (commit) |

### Plugins

| Plugin | Type | Description |
|--------|------|-------------|
| `siklu_eh` | cliconf | Network device abstraction for Siklu EH |
| `siklu_eh` | terminal | Terminal handler for Siklu EH SSH |

## Usage Examples

### Example 1: Execute show commands

```yaml
---
- name: Show IP configuration
  hosts: siklu_devices
  gather_facts: false

  tasks:
    - name: Execute show commands
      siklu.eh.siklu_command:
        commands:
          - show system
          - show ip
          - show route
      register: result

    - name: Display output
      debug:
        var: result.stdout_lines
```

### Example 2: Gather device facts

```yaml
---
- name: Gather device facts
  hosts: siklu_devices
  gather_facts: false

  tasks:
    - name: Gather all facts
      siklu.eh.siklu_facts:
      register: facts

    - name: Display system information
      debug:
        var: facts.ansible_facts.ansible_net_system

    - name: Display software information
      debug:
        var: facts.ansible_facts.ansible_net_software
```

### Example 3: Configure IP address

```yaml
---
- name: Configure device
  hosts: siklu_devices
  gather_facts: false

  tasks:
    - name: Configure IP on slot 3
      siklu.eh.siklu_config:
        config:
          - type: ip
            slot: 3
            ip_address: 192.168.1.100
            prefix_len: 24
            vlan: 0
        show:
          - type: ip
            slot: 3
      register: result

    - name: Display configuration result
      debug:
        var: result
```

### Example 4: Configure static route

```yaml
---
- name: Configure route
  hosts: siklu_devices
  gather_facts: false

  tasks:
    - name: Add static route
      siklu.eh.siklu_config:
        config:
          - type: route
            slot: 1
            dest: 10.0.0.0
            prefix_len: 8
            next_hop: 192.168.1.254
        show:
          - type: route
            slot: 1
      register: result

    - name: Display route result
      debug:
        var: result
```

### Example 5: Save configuration

```yaml
---
- name: Save configuration
  hosts: siklu_devices
  gather_facts: false

  tasks:
    - name: Commit configuration
      siklu.eh.siklu_save_config:
      register: result

    - name: Display result
      debug:
        msg: "{{ result.msg }}"
```

## Module Documentation

### siklu_command

Execute arbitrary show commands on the device.

**Options:**
- `commands` (list, required) - List of commands to execute

**Example:**
```yaml
- siklu.eh.siklu_command:
    commands:
      - show system
      - show ip
  register: result
```

### siklu_config

Configure IP addresses and static routes on the device. Supports idempotent operations.

**Options:**
- `config` (list) - List of configuration items
    - `type` (str, required) - Type: `ip` or `route`
    - `slot` (int, required) - Slot number
    - `ip_address` (str) - IP address (for type=ip)
    - `prefix_len` (int) - Prefix length (0-32)
    - `vlan` (int) - VLAN ID (for type=ip)
    - `dest` (str) - Destination IP (for type=route)
    - `next_hop` (str) - Next hop IP (for type=route)
- `show` (list) - Show commands to execute after configuration

**Example:**
```yaml
- siklu.eh.siklu_config:
    config:
      - type: ip
        slot: 3
        ip_address: 192.168.1.100
        prefix_len: 24
        vlan: 0
    show:
      - type: ip
        slot: 3
  register: result
```

### siklu_facts

Gather device facts including system info, software, IP config, and routes.

**Options:**
- `gather_subset` (list, default=['all']) - Fact subsets to gather
    - Choices: `all`, `system`, `software`, `ip`, `route`

**Example:**
```yaml
- siklu.eh.siklu_facts:
    gather_subset:
      - system
      - software
  register: facts
```

### siklu_save_config

Save running configuration to startup configuration (commit).

**Example:**
```yaml
- siklu.eh.siklu_save_config:
  register: result
```

## Testing

### Run test playbooks

```bash
# Run all tests
make test-all

# Test individual components
make test-command  # Test siklu_command module
make test-config   # Test siklu_config module
make test-facts    # Test siklu_facts module
```

### Manual testing

Create test inventory:
```ini
[siklu_devices]
device1 ansible_host=10.0.101.2

[siklu_devices:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=siklu.eh.siklu_eh
ansible_user=admin
ansible_password=admin
```

Run playbooks:
```bash
ansible-playbook test_command.yaml -i inventory.ini -v
ansible-playbook test_config.yaml -i inventory.ini -v
ansible-playbook test_facts.yaml -i inventory.ini -v
```

## Security Best Practices

⚠️ **WARNING** - Network Configuration Safety

**NEVER configure production routes/IPs remotely without:**
- Out-of-band (OOB) access (serial console, IPMI, etc.)
- Backup connection path
- Testing on non-critical slots first

**Safe test slots:** 4, 5, 6, 7
**Critical slots (avoid in tests):** 1, 2, 3

### Handling Credentials

- Never commit passwords to git
- Use Ansible vault for sensitive data:
  ```bash
  ansible-vault encrypt inventory.ini
  ansible-playbook playbook.yaml -i inventory.ini --ask-vault-pass
  ```
- Use environment variables:
  ```bash
  export ANSIBLE_NET_PASSWORD=your_password
  ```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing procedures
- Git workflow

## Architecture

### Project Structure

```
ansible-collection-siklu-eh/
├── plugins/
│   ├── cliconf/siklu_eh.py          # CLI configuration plugin
│   ├── terminal/siklu_eh.py         # Terminal plugin
│   ├── modules/
│   │   ├── siklu_command.py         # Command execution module
│   │   ├── siklu_config.py          # Configuration module
│   │   ├── siklu_facts.py           # Facts gathering module
│   │   └── siklu_save_config.py     # Config save module
│   └── module_utils/siklu_eh/
│       ├── parsers.py               # Output parsing functions
│       └── connection_utils.py      # Connection utilities
├── test_command.yaml                # Test playbook for commands
├── test_config.yaml                 # Test playbook for configuration
├── test_facts.yaml                  # Test playbook for facts
├── inventory.ini                    # Test inventory
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── requirements-galaxy.yml          # Ansible dependencies
├── galaxy.yml                       # Collection metadata
├── Makefile                         # Build/test automation
├── README.md                        # This file
├── CONTRIBUTING.md                  # Contribution guidelines
├── CHANGELOG.md                     # Version history
└── LICENSE                          # MIT License
```

### Code Philosophy

- **DRY (Don't Repeat Yourself)** - Shared utilities in `module_utils/`
- **Type Safety** - Full type hints throughout
- **Documentation** - Comprehensive docstrings and examples
- **Testing** - Playbook-based testing for integration
- **Maintainability** - Clear separation of concerns

## Troubleshooting

### Connection issues

```
ESTABLISH LOCAL CONNECTION FOR USER
```

This is normal - modules run locally and create network connections to the device.

### Regex warnings

Update `plugins/terminal/siklu_eh.py` with proper regex patterns for your device output.

### Idempotency failures

Check that current configuration exactly matches desired state (exact IP format, VLAN IDs, etc.).

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Add tests for new functionality
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## License

This collection is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For issues and feature requests, please:

1. Check [existing issues](https://github.com/siklu/ansible-collection/issues)
2. Create a [new issue](https://github.com/siklu/ansible-collection/issues/new) with:
    - Device model and firmware version
    - Ansible version
    - Collection version
    - Steps to reproduce
    - Error messages/logs

## Related Resources

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Network Documentation](https://docs.ansible.com/ansible/latest/network/index.html)
- [Siklu by Ceragon Documentation](https://www.siklu.com/)
- [Collection Repository](https://github.com/siklu/ansible-collection)

## Authors

Created and maintained by DevOps team at Ceragon Networks.

## Acknowledgments

- Thanks to Ansible community for excellent framework
- Inspired by other network device collections
- Built with best practices from production environments
