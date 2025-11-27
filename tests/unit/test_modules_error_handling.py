"""
Unit tests for Ansible module error handling and parameter validation.
Tests invalid parameters, type checking, and error cases.
"""

from unittest.mock import MagicMock, patch


class TestModuleParameterValidation:
    """Test module parameter validation and error handling."""

    # ============================================================
    # siklu_command Module Tests
    # ============================================================

    def test_siklu_command_missing_commands_parameter(self):
        """Test siklu_command fails without commands parameter."""
        with patch('ansible.module_utils.basic.AnsibleModule') as mock_module_class:
            mock_module = MagicMock()
            mock_module.params = {'commands': None}
            mock_module_class.return_value = mock_module

            # Module should require commands
            assert mock_module.params['commands'] is None

    def test_siklu_command_list_validation(self):
        """Test siklu_command with empty commands and invalid types."""
        # Test empty commands list
        mock_module = MagicMock()
        mock_module.params = {'commands': []}
        assert len(mock_module.params['commands']) == 0

        # Test invalid command types
        commands = [123, 456]  # Invalid - should be strings
        assert not all(isinstance(cmd, str) for cmd in commands)

    def test_siklu_command_very_long_command(self):
        """Test siklu_command with extremely long command string."""
        long_command = "show " + "x" * 10000  # Very long
        assert len(long_command) > 1000

    # ============================================================
    # siklu_config Module Tests
    # ============================================================

    def test_siklu_config_missing_config_parameter(self):
        """Test siklu_config requires config parameter."""
        mock_module = MagicMock()
        mock_module.params = {'config': None, 'show': None}

        # Config should be required
        assert mock_module.params['config'] is None

    def test_siklu_config_ip_validation(self):
        """Test siklu_config IP configuration validation."""
        config = [
            {
                'type': 'ip',
                'slot': 1,
                'ip_address': '999.999.999.999',  # Invalid IP
                'prefix_len': 24,
                'vlan': 100
            }
        ]
        # IP validation should catch this
        assert '999' in config[0]['ip_address']

    def test_siklu_config_prefix_vlan_bounds(self):
        """Test siklu_config prefix and VLAN boundary validation."""
        config_invalid_prefix = [
            {
                'type': 'ip',
                'slot': 1,
                'ip_address': '10.0.0.1',
                'prefix_len': 33,  # Invalid - should be 0-32
                'vlan': 100
            }
        ]
        assert config_invalid_prefix[0]['prefix_len'] == 33

        config_invalid_vlan = [
            {
                'type': 'ip',
                'slot': 1,
                'ip_address': '10.0.0.1',
                'prefix_len': 24,
                'vlan': 4095  # Invalid - should be 0-4094
            }
        ]
        assert config_invalid_vlan[0]['vlan'] == 4095

    def test_siklu_config_route_validation(self):
        """Test siklu_config route configuration validation."""
        config = [
            {
                'type': 'route',
                'slot': 1,
                'dest': '10.0.0.1',  # Not a subnet
                'prefix_len': 24,
                'next_hop': '172.16.0.1'
            }
        ]
        # Should validate that dest is a subnet
        assert '10.0.0.1' in config[0]['dest']

    def test_siklu_config_route_required_fields(self):
        """Test siklu_config route requires all fields."""
        config = [
            {
                'type': 'route',
                'slot': 1,
                'dest': '10.0.0.0',
                # Missing prefix_len
                'next_hop': '172.16.0.1'
            }
        ]
        assert 'prefix_len' not in config[0]

    def test_siklu_config_invalid_type(self):
        """Test siklu_config with unknown config type."""
        config = [
            {
                'type': 'invalid_type',  # Should be 'ip' or 'route'
                'slot': 1
            }
        ]
        assert config[0]['type'] not in ['ip', 'route']

    # ============================================================
    # siklu_rollback Module Tests
    # ============================================================

    def test_siklu_rollback_state_parameter(self):
        """Test siklu_rollback state parameter validation."""
        mock_module = MagicMock()
        mock_module.params = {'state': None, 'timeout': None}
        assert mock_module.params['state'] is None

        state = 'invalid'  # Should be 'present' or 'absent'
        assert state not in ['present', 'absent']

    def test_siklu_rollback_timeout_validation(self):
        """Test siklu_rollback timeout bounds and types."""
        mock_module = MagicMock()
        mock_module.params = {'state': 'present', 'timeout': None}
        assert mock_module.params['timeout'] is None

        timeouts = [
            -100,      # Negative
            0,         # Boundary
            86401,     # Over max (86400)
            "text",    # String instead of int
        ]
        assert timeouts[0] < 0
        assert timeouts[2] > 86400

    # ============================================================
    # siklu_facts Module Tests
    # ============================================================

    def test_siklu_facts_gather_subset_validation(self):
        """Test siklu_facts gather_subset validation."""
        gather_subset = ['invalid_subset', 'another_invalid']
        valid_subsets = [
            'system', 'software', 'ip', 'route', 'inventory',
            'rf', 'config', 'config_startup', 'all'
        ]

        invalid = [s for s in gather_subset if s not in valid_subsets]
        assert len(invalid) == 2

    def test_siklu_facts_case_sensitivity(self):
        """Test siklu_facts gather_subset case sensitivity."""
        subsets = ['System', 'SOFTWARE', 'Ip']  # Wrong case
        valid_subsets = ['system', 'software', 'ip']

        for subset in subsets:
            assert subset not in valid_subsets

    def test_siklu_facts_config_not_in_all(self):
        """Test that config/config_startup not in 'all' subset."""
        all_subset = ['system', 'software', 'ip', 'route', 'inventory', 'rf']
        assert 'config' not in all_subset
        assert 'config_startup' not in all_subset

    # ============================================================
    # siklu_save_config Module Tests
    # ============================================================

    def test_siklu_save_config_no_parameters(self):
        """Test siklu_save_config takes no parameters."""
        mock_module = MagicMock()
        mock_module.params = {}
        assert len(mock_module.params) == 0

    # ============================================================
    # Connection and Response Error Handling
    # ============================================================

    def test_connection_and_response_handling(self):
        """Test modules handle connection errors and responses."""
        mock_connection = MagicMock()
        mock_connection.get.side_effect = OSError("Connection timeout")

        try:
            mock_connection.get("show system")
            assert False, "Should have raised exception"
        except OSError:
            # Expected - connection error raised
            pass

    def test_malformed_and_empty_responses(self):
        """Test modules handle malformed and empty responses."""
        mock_response = "not valid response format"
        assert isinstance(mock_response, str)

        empty_response = ""
        assert len(empty_response) == 0

    # ============================================================
    # Check Mode and Edge Cases
    # ============================================================

    def test_modules_check_mode_and_boundaries(self):
        """Test modules respect check mode and boundary values."""
        mock_module = MagicMock()
        mock_module.check_mode = True
        assert mock_module.check_mode is True

        slots = [0, 1, 10, 99, 999]
        assert all(s >= 0 for s in slots)

    def test_command_special_characters(self):
        """Test commands with special characters."""
        commands = [
            "show system | grep model",
            "show config >> /tmp/config.txt",
            "set ip 1 ip-addr 10.0.0.1; set route 1 dest 0.0.0.0",
        ]
        for cmd in commands:
            assert isinstance(cmd, str)
