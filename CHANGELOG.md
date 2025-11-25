# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-11-25

### Added
- New fact subsets in `siklu_facts` module: `inventory`, `rf`, `config`, `config_startup`
- Hierarchical hardware inventory parsing
- RF radio status monitoring with type conversions
- Running and startup configuration reading capability via facts

### Changed
- `siklu_facts` now excludes `config` and `config_startup` subsets from `all` by default (must be explicitly requested)

### Fixed
- Proper network connection handling in facts module

## [1.0.0] - 2025-11-23

### Added

- Initial release of Siklu EH Ansible Collection
- `siklu_command` module - Execute show commands on Siklu EH devices
- `siklu_config` module - Configure IP addresses and static routes
- `siklu_facts` module - Gather device facts (system info, software, IP, routes)
- `siklu_save_config` module - Save running configuration to startup
- Terminal plugin for CLI interaction with Siklu EH devices
- Cliconf plugin for network device abstraction
- Connection utilities for code reuse (`connection_utils.py`)
- Output parsing utilities (`parsers.py`)
- Comprehensive test playbooks
    - `test_command.yaml` - Command execution tests
    - `test_config.yaml` - Configuration management tests
    - `test_facts.yaml` - Facts gathering tests
- Full documentation with examples
- Makefile for build and test automation
- Type hints throughout the codebase
- Idempotent configuration operations with verification
- Support for Ansible 2.20.0+
- Support for Python 3.11+
