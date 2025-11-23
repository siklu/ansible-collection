# Contributing to Siklu EH Ansible Collection

Thank you for your interest in contributing to the Siklu EH Ansible Collection!

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Ansible core 2.20.0 or higher

### Setup Steps

1. **Clone the repository**:
```bash
git clone https://github.com/siklu/ansible-collection.git
cd ansible-collection
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
ansible-galaxy collection install -r requirements-galaxy.yml
```

4. **Build and install collection locally**:
```bash
make install
```

## Development Workflow

### Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes to the code

3. Test your changes:
```bash
make test-all
```

4. Build and install locally:
```bash
make install
```

5. Commit your changes:
```bash
git add .
git commit -m "Add feature: description"
```

6. Push to your fork:
```bash
git push origin feature/your-feature-name
```

7. Create a Pull Request on GitHub

### Adding New Modules

When adding a new module:

1. Create module file in `plugins/modules/`
2. Add parser functions to `plugins/module_utils/siklu_eh/parsers.py` if needed
3. Add connection utilities to `plugins/module_utils/siklu_eh/connection_utils.py` if needed
4. Create test playbook in root directory
5. Update `README.md` with module documentation
6. Update `CHANGELOG.md`

### Code Structure

```
plugins/
├── cliconf/          # CLI configuration plugin
├── terminal/         # Terminal interaction plugin
├── modules/          # Ansible modules
└── module_utils/     # Shared utilities
    └── siklu_eh/
        ├── parsers.py           # Output parsing functions
        └── connection_utils.py  # Connection helper functions
```

## Code Style Guidelines

### Python Code

- **Python version**: 3.11+ syntax and features
- **Type hints**: Use type hints for all function parameters and return values
- **Docstrings**: All functions and classes must have docstrings
- **Comments**: Write comments in English
- **Line length**: Maximum 100 characters (soft limit)
- **Imports**: Group imports (standard library, third-party, local)

Example:
```python
def configure_ip(connection: Connection, item: dict) -> dict:
    """
    Configure IP address on specified slot.

    Args:
        connection: Ansible connection object
        item: Configuration parameters

    Returns:
        Result dictionary with operation status
    """
    # Implementation here
    pass
```

### Module Documentation

All modules must include:
- `DOCUMENTATION` - Module description and parameters
- `EXAMPLES` - Usage examples
- `RETURN` - Return value documentation

### Git Commit Messages

Use clear, descriptive commit messages:

```
Add support for X feature
Fix bug in Y module
Update documentation for Z
Refactor parsers for better performance
```

Commit message format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description if needed

## Testing

### Test Playbooks

Test your changes using provided test playbooks:

```bash
# Test command execution
ansible-playbook test_command.yaml -i inventory.ini -v

# Test configuration
ansible-playbook test_config.yaml -i inventory.ini -v

# Test facts gathering
ansible-playbook test_facts.yaml -i inventory.ini -v
```

### Creating Test Inventory

Create `inventory.ini` in root directory:
```ini
[siklu_devices]
eh8010 ansible_host=10.0.101.2

[siklu_devices:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=siklu.eh.siklu_eh
ansible_user=admin
ansible_password=admin
```

## Security

### Sensitive Data

Never commit:
- Passwords or credentials
- Private keys
- API tokens
- Internal IP addresses

Use `.gitignore` to exclude sensitive files.

## Documentation

### README Updates

Update `README.md` when:
- Adding new modules
- Adding new features
- Changing installation instructions
- Changing examples

### Docstring Format

Use Google-style docstrings:

```python
def get_device_info(connection: Connection) -> dict:
    """
    Get device information.

    Retrieves system information including model, hostname,
    and software version from the device.

    Args:
        connection: Active connection to device

    Returns:
        Dictionary with keys:
        - model: Device model string
        - hostname: Device hostname
        - version: Software version

    Raises:
        Exception: If connection fails or device is unresponsive
    """
```

## Bug Reports

When reporting bugs, include:
- Device model and firmware version
- Ansible version
- Collection version
- Playbook/code that triggers the bug
- Error message and traceback
- Steps to reproduce

## Feature Requests

When requesting features:
- Describe the use case
- Explain why it's needed
- Provide examples if possible
- Link to related issues

## Review Process

All pull requests will be reviewed for:
- Code quality and style
- Documentation completeness
- Test coverage
- Backward compatibility
- Security considerations

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or discussion in the GitHub repository!

Thank you for contributing! 🎉
