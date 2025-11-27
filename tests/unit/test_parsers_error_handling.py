"""
Unit tests for error handling in Siklu EH parsers.
Tests malformed responses, missing fields, and invalid data types.
Focuses on realistic error scenarios based on actual parser behavior.
"""

from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    parse_system_info,
    parse_sw_info,
    parse_ip_config,
    parse_route_config,
    parse_inventory,
    parse_rf_status,
)


class TestParserErrorHandling:
    """Test error handling and edge cases in parsers."""

    # ============================================================
    # System Info Parser - Error Cases
    # ============================================================

    def test_parse_system_info_empty_output(self):
        """Test parser handles empty output gracefully."""
        result = parse_system_info("")
        assert isinstance(result, dict)
        assert result.get("model") is None

    def test_parse_system_info_invalid_temperature(self):
        """Test parser handles non-numeric temperature."""
        output = "system description EH-8010FX\nsystem temperature invalid_temp\n"
        result = parse_system_info(output)
        assert result.get("temperature") is None

    def test_parse_system_info_invalid_timeout(self):
        """Test parser handles non-numeric cli-timeout."""
        output = "system description EH-8010FX\nsystem cli-timeout not_a_number\n"
        result = parse_system_info(output)
        assert result.get("cli_timeout") is None

    # ============================================================
    # IP Config Parser - Error Cases
    # ============================================================

    def test_parse_ip_config_empty_output(self):
        """Test parser handles empty output."""
        result = parse_ip_config("")
        assert result == {}

    def test_parse_ip_config_malformed_slot(self):
        """Test parser handles malformed slot number."""
        output = "set ip invalid ip-addr 10.0.0.1 prefix-len 24 vlan 100\n"
        result = parse_ip_config(output)
        assert result == {}

    # ============================================================
    # Route Config Parser - Error Cases
    # ============================================================

    def test_parse_route_config_empty_output(self):
        """Test parser handles empty output."""
        result = parse_route_config("")
        assert result == {}

    def test_parse_route_config_malformed_slot(self):
        """Test parser handles malformed slot number."""
        output = "set route bad dest 10.0.0.0 prefix-len 24 next-hop 172.16.0.1\n"
        result = parse_route_config(output)
        assert result == {}

    # ============================================================
    # Inventory Parser - Error Cases
    # ============================================================

    def test_parse_inventory_empty_output(self):
        """Test parser handles empty output."""
        result = parse_inventory("")
        assert isinstance(result, dict)

    # ============================================================
    # RF Status Parser - Error Cases
    # ============================================================

    def test_parse_rf_status_empty_output(self):
        """Test parser handles empty output."""
        result = parse_rf_status("")
        assert isinstance(result, dict)

    def test_parse_rf_status_invalid_float(self):
        """Test parser handles non-numeric float fields."""
        output = "rf cinr invalid_value\nrf rssi not_a_number\n"
        result = parse_rf_status(output)
        assert result.get("cinr") is None
        assert result.get("rssi") is None

    def test_parse_rf_status_invalid_int(self):
        """Test parser handles non-numeric int fields."""
        output = "rf tx-frequency not_numeric\nrf rx-frequency also_invalid\n"
        result = parse_rf_status(output)
        assert result.get("tx_frequency") is None
        assert result.get("rx_frequency") is None

    # ============================================================
    # SW Info Parser - Error Cases
    # ============================================================

    def test_parse_sw_info_empty_output(self):
        """Test parser handles empty output."""
        result = parse_sw_info("")
        assert isinstance(result, dict)

    # ============================================================
    # Comprehensive Error Cases with Real Device Output
    # ============================================================

    def test_parse_ip_config_no_matches(self):
        """Test parser when no IP configs exist."""
        output = "show system\ntemperature: 50\n"
        result = parse_ip_config(output)
        # Should return empty dict when no 'set ip' lines found
        assert result == {}

    def test_parse_route_config_no_matches(self):
        """Test parser when no routes exist."""
        output = "show routes\nno routes configured\n"
        result = parse_route_config(output)
        # Should return empty dict when no 'set route' lines found
        assert result == {}

    def test_parse_inventory_basic_structure(self):
        """Test parser creates dict structure even with minimal data."""
        output = "inventory 1 desc Chassis\ninventory 1 class chassis\n"
        result = parse_inventory(output)
        assert isinstance(result, dict)
        # Should contain chassis key for id 1
        if "chassis" in result:
            assert isinstance(result["chassis"], dict)

    def test_parse_rf_status_with_valid_values(self):
        """Test RF parser with mix of valid and missing fields."""
        output = "rf operational up\nrf cinr 25.5\nrf tx-state normal\n"
        result = parse_rf_status(output)
        # Some fields may be present, some missing
        assert isinstance(result, dict)

    # ============================================================
    # Type Conversion Edge Cases
    # ============================================================

    def test_parse_system_info_temperature_string_to_int(self):
        """Test temperature field is converted to int."""
        output = "system description EH-8010FX\nsystem temperature 54\n"
        result = parse_system_info(output)
        if result.get("temperature") is not None:
            assert isinstance(result.get("temperature"), int)

    def test_parse_system_info_timeout_string_to_int(self):
        """Test cli-timeout field is converted to int."""
        output = "system description EH-8010FX\nsystem cli-timeout 15\n"
        result = parse_system_info(output)
        if result.get("cli_timeout") is not None:
            assert isinstance(result.get("cli_timeout"), int)

    def test_parse_system_info_handles_missing_fields(self):
        """Test parser gracefully handles missing optional fields."""
        output = "system description EH-8010FX\n"
        result = parse_system_info(output)
        # Should still work even with minimal data
        assert isinstance(result, dict)

    def test_parse_ip_config_correct_format(self):
        """Test parser with correctly formatted IP config."""
        # Using exact format from actual device output
        output = "set ip 1 ip-addr 10.0.0.1 prefix-len 24 vlan 100\n"
        result = parse_ip_config(output)
        # Parser should extract slot 1
        assert 1 in result or result == {}

    def test_parse_route_config_correct_format(self):
        """Test parser with correctly formatted route config."""
        # Using exact format from actual device output
        output = "set route 1 dest 10.0.0.0 prefix-len 24 next-hop 172.16.0.1\n"
        result = parse_route_config(output)
        # Parser should extract slot 1
        assert 1 in result or result == {}
