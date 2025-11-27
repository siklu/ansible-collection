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
        """Parser should handle empty output gracefully."""
        result = parse_system_info("")
        assert isinstance(result, dict)
        assert result.get("model") is None

    def test_parse_system_info_minimal_data(self):
        """Parser should handle minimal valid system description."""
        output = "system description : EH-8010FX\n"
        result = parse_system_info(output)
        assert result.get("model") == "EH-8010FX"

    def test_parse_system_info_invalid_temperature_ignored(self):
        """Parser should ignore temperature with non-numeric value."""
        output = "system description : EH-8010FX\nsystem temperature : invalid_temp\n"
        result = parse_system_info(output)
        # Temperature field should not be present since pattern requires \d+
        assert "temperature" not in result
        # But model should still be parsed
        assert result.get("model") == "EH-8010FX"

    def test_parse_system_info_invalid_cli_timeout_ignored(self):
        """Parser should ignore cli-timeout with non-numeric value."""
        output = "system description : EH-8010FX\nsystem cli-timeout : not_a_number\n"
        result = parse_system_info(output)
        # cli_timeout field should not be present since pattern requires \d+
        assert "cli_timeout" not in result
        # But model should still be parsed
        assert result.get("model") == "EH-8010FX"

    def test_parse_system_info_valid_numeric_temperature(self):
        """Parser should convert valid numeric temperature to int."""
        output = "system description : EH-8010FX\nsystem temperature : 57\n"
        result = parse_system_info(output)
        assert result.get("temperature") == 57
        assert isinstance(result.get("temperature"), int)

    def test_parse_system_info_valid_numeric_cli_timeout(self):
        """Parser should convert valid numeric cli-timeout to int."""
        output = "system description : EH-8010FX\nsystem cli-timeout : 15\n"
        result = parse_system_info(output)
        assert result.get("cli_timeout") == 15
        assert isinstance(result.get("cli_timeout"), int)

    # ============================================================
    # IP Config Parser - Error Cases
    # ============================================================

    def test_parse_ip_config_empty_output(self):
        """Parser should return empty dict for empty output."""
        result = parse_ip_config("")
        assert result == {}

    def test_parse_ip_config_malformed_slot(self):
        """Parser should ignore entries with non-numeric slot."""
        output = "ip invalid ip-addr : 10.0.0.1\n"
        result = parse_ip_config(output)
        assert result == {}

    def test_parse_ip_config_no_matches(self):
        """Parser should return empty dict when no set ip lines."""
        output = "show running-configuration\nsome other output\n"
        result = parse_ip_config(output)
        assert result == {}

    # ============================================================
    # Route Config Parser - Error Cases
    # ============================================================

    def test_parse_route_config_empty_output(self):
        """Parser should return empty dict for empty output."""
        result = parse_route_config("")
        assert result == {}

    def test_parse_route_config_malformed_slot(self):
        """Parser should ignore entries with non-numeric slot."""
        output = "route bad dest : 10.0.0.0\n"
        result = parse_route_config(output)
        assert result == {}

    def test_parse_route_config_no_matches(self):
        """Parser should return empty dict when no set route lines."""
        output = "show routes\nno routes found\n"
        result = parse_route_config(output)
        assert result == {}

    # ============================================================
    # Inventory Parser - Graceful Degradation
    # ============================================================

    def test_parse_inventory_empty_output(self):
        """Parser should handle empty output and return a dict."""
        result = parse_inventory("")
        assert isinstance(result, dict)

    def test_parse_inventory_returns_dict_for_garbage(self):
        """Parser should return dict structure even for garbage data."""
        result = parse_inventory("garbage data")
        assert isinstance(result, dict)

    def test_parse_inventory_valid_chassis_only(self):
        """Parser should extract valid chassis-only inventory data."""
        output = "inventory 0 description : EH-8010FX\ninventory 0 cont-in : 0\n"
        result = parse_inventory(output)
        assert isinstance(result, dict)
        assert "chassis" in result
        chassis = result["chassis"]
        assert chassis.get("description") == "EH-8010FX"
        assert chassis.get("cont_in") == 0

    # ============================================================
    # RF Status Parser - Graceful Degradation
    # ============================================================

    def test_parse_rf_status_empty_output(self):
        """Parser should handle empty output and return a dict."""
        result = parse_rf_status("")
        assert isinstance(result, dict)

    def test_parse_rf_status_invalid_numeric_fields(self):
        """Parser should handle non-numeric RF values gracefully."""
        output = "rf cinr : invalid_value\nrf rssi : not_a_number\n"
        result = parse_rf_status(output)
        # Conversion helpers return None for invalid values
        assert result.get("cinr") is None
        assert result.get("rssi") is None

    def test_parse_rf_status_valid_partial_data(self):
        """Parser should handle partial but valid RF status data."""
        output = "rf operational : up\nrf tx-state : normal\n"
        result = parse_rf_status(output)
        assert isinstance(result, dict)
        assert result.get("operational") == "up"
        assert result.get("tx_state") == "normal"

    def test_parse_rf_status_valid_numeric_fields(self):
        """Parser should convert valid numeric RF fields to int/float."""
        output = "rf cinr : 15.5\nrf rssi : -60\n"
        result = parse_rf_status(output)
        assert result.get("cinr") == 15.5
        assert isinstance(result.get("cinr"), float)

        # rssi is also treated as float by parser
        assert result.get("rssi") == -60.0
        assert isinstance(result.get("rssi"), float)

    def test_parse_rf_status_comprehensive_data(self):
        """Parser should handle comprehensive RF status output."""
        output = """rf operational : up
rf tx-state : normal
rf cinr : 18.5
rf rssi : -55
rf tx-frequency : 73400000
rf rx-frequency : 81400000"""
        result = parse_rf_status(output)
        assert result.get("operational") == "up"
        assert result.get("tx_state") == "normal"
        assert result.get("cinr") == 18.5
        assert result.get("rssi") == -55.0
        assert result.get("tx_frequency") == 73400000
        assert result.get("rx_frequency") == 81400000

    # ============================================================
    # SW Info Parser - Graceful Degradation
    # ============================================================

    def test_parse_sw_info_empty_output(self):
        """Parser should handle empty output and return a dict."""
        result = parse_sw_info("")
        assert isinstance(result, dict)

    def test_parse_sw_info_returns_dict_for_garbage(self):
        """Parser should return dict structure even for garbage data."""
        result = parse_sw_info("no valid data")
        assert isinstance(result, dict)

    def test_parse_sw_info_valid_running_bank(self):
        """Parser should extract valid running software info."""
        output = """Flash Bank Version Running Scheduled to run startup-config
1 10.6.0-18451-c009ec33d1 yes no exists
2 10.8.2-19409-92aead94fe no no missing"""
        result = parse_sw_info(output)
        assert "running" in result
        running = result["running"]
        assert running.get("version") == "10.6.0-18451-c009ec33d1"
        assert running.get("bank") == 1
        assert running.get("scheduled_to_run") is False
        assert running.get("startup_config") is True

    def test_parse_sw_info_valid_standby_bank(self):
        """Parser should extract valid standby software info."""
        output = """Flash Bank Version Running Scheduled to run startup-config
1 10.6.0-18451-c009ec33d1 yes no exists
2 10.8.2-19409-92aead94fe no no missing"""
        result = parse_sw_info(output)
        assert "standby" in result
        standby = result["standby"]
        assert standby.get("version") == "10.8.2-19409-92aead94fe"
        assert standby.get("bank") == 2
        assert standby.get("scheduled_to_run") is False
        assert standby.get("startup_config") is False

    def test_parse_sw_info_scheduled_upgrade(self):
        """Parser should handle scheduled upgrade scenario."""
        output = """Flash Bank Version Running Scheduled to run startup-config
1 10.6.0-18451-c009ec33d1 yes no exists
2 10.8.2-19409-92aead94fe no yes exists"""
        result = parse_sw_info(output)
        standby = result.get("standby", {})
        assert standby.get("scheduled_to_run") is True
        assert standby.get("startup_config") is True
