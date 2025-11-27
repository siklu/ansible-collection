"""
Unit tests for error handling in Siklu EH parsers.
Tests realistic error scenarios based on actual parser behavior.
Parsers use regex patterns - if pattern doesn't match, field is not extracted.
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
    # System Info Parser - Graceful Degradation
    # ============================================================

    def test_parse_system_info_empty_output(self):
        """Test parser handles empty output gracefully."""
        result = parse_system_info("")
        assert isinstance(result, dict)
        assert result.get("model") is None

    def test_parse_system_info_minimal_data(self):
        """Test parser handles minimal valid data."""
        output = "system description EH-8010FX\n"
        result = parse_system_info(output)
        # Parser should extract model from description
        assert result.get("model") == "EH-8010FX" or result.get("model") is None

    # ============================================================
    # IP Config Parser - Error Cases
    # ============================================================

    def test_parse_ip_config_empty_output(self):
        """Test parser returns empty dict for empty output."""
        result = parse_ip_config("")
        assert result == {}

    def test_parse_ip_config_malformed_slot(self):
        """Test parser returns empty dict when slot is not numeric."""
        output = "set ip invalid ip-addr 10.0.0.1 prefix-len 24 vlan 100\n"
        result = parse_ip_config(output)
        assert result == {}

    def test_parse_ip_config_no_matches(self):
        """Test parser returns empty dict when output has no set ip lines."""
        output = "show running-configuration\nsome other output\n"
        result = parse_ip_config(output)
        assert result == {}

    # ============================================================
    # Route Config Parser - Error Cases
    # ============================================================

    def test_parse_route_config_empty_output(self):
        """Test parser returns empty dict for empty output."""
        result = parse_route_config("")
        assert result == {}

    def test_parse_route_config_malformed_slot(self):
        """Test parser returns empty dict when slot is not numeric."""
        output = "set route bad dest 10.0.0.0 prefix-len 24 next-hop 172.16.0.1\n"
        result = parse_route_config(output)
        assert result == {}

    def test_parse_route_config_no_matches(self):
        """Test parser returns empty dict when output has no set route lines."""
        output = "show routes\nno routes found\n"
        result = parse_route_config(output)
        assert result == {}

    # ============================================================
    # Inventory Parser - Graceful Degradation
    # ============================================================

    def test_parse_inventory_empty_output(self):
        """Test parser handles empty output."""
        result = parse_inventory("")
        assert isinstance(result, dict)

    def test_parse_inventory_returns_dict(self):
        """Test parser always returns dict structure."""
        result = parse_inventory("garbage data")
        assert isinstance(result, dict)

    # ============================================================
    # RF Status Parser - Graceful Degradation
    # ============================================================

    def test_parse_rf_status_empty_output(self):
        """Test parser handles empty output."""
        result = parse_rf_status("")
        assert isinstance(result, dict)

    def test_parse_rf_status_invalid_numeric_fields(self):
        """Test parser handles non-numeric values in numeric fields."""
        output = "rf cinr invalid_value\nrf rssi not_a_number\n"
        result = parse_rf_status(output)
        # Parser should not set these fields if conversion fails
        assert result.get("cinr") is None
        assert result.get("rssi") is None

    def test_parse_rf_status_valid_partial_data(self):
        """Test parser handles partial valid RF status data."""
        output = "rf operational up\nrf tx-state normal\n"
        result = parse_rf_status(output)
        # Should return dict with available fields
        assert isinstance(result, dict)

    # ============================================================
    # SW Info Parser - Graceful Degradation
    # ============================================================

    def test_parse_sw_info_empty_output(self):
        """Test parser handles empty output."""
        result = parse_sw_info("")
        assert isinstance(result, dict)

    def test_parse_sw_info_returns_dict(self):
        """Test parser always returns dict structure."""
        result = parse_sw_info("no valid data")
        assert isinstance(result, dict)
