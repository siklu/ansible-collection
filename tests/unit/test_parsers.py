"""
Unit tests for Siklu EH parsers.

Tests all parsing functions with real device output examples.
"""

import pytest
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    parse_inventory,
    parse_rf_status,
    parse_configuration,
    parse_rollback_status,
    _normalize_empty_value,
    _convert_to_int,
    _convert_to_float,
    _convert_to_bool,
)


class TestHelperFunctions:
    """Test utility/helper functions."""

    def test_normalize_empty_value(self):
        """Test normalization of empty and N/A values."""
        assert _normalize_empty_value("") is None
        assert _normalize_empty_value("   ") is None
        assert _normalize_empty_value("N/A") is None
        assert _normalize_empty_value("n/a") is None
        assert _normalize_empty_value("default") is None
        assert _normalize_empty_value("DEFAULT") is None
        assert _normalize_empty_value("valid value") == "valid value"
        assert _normalize_empty_value("  trimmed  ") == "trimmed"

    def test_convert_to_int(self):
        """Test integer conversion."""
        assert _convert_to_int("42") == 42
        assert _convert_to_int("-128") == -128
        assert _convert_to_int("0") == 0
        assert _convert_to_int("") is None
        assert _convert_to_int("N/A") is None
        assert _convert_to_int("invalid") is None

    def test_convert_to_float(self):
        """Test float conversion."""
        assert _convert_to_float("42.5") == 42.5
        assert _convert_to_float("-128.0") == -128.0
        assert _convert_to_float("28") == 28.0
        assert _convert_to_float("") is None
        assert _convert_to_float("n/a") is None
        assert _convert_to_float("invalid") is None

    def test_convert_to_bool(self):
        """Test boolean conversion."""
        assert _convert_to_bool("true") is True
        assert _convert_to_bool("True") is True
        assert _convert_to_bool("TRUE") is True
        assert _convert_to_bool("false") is False
        assert _convert_to_bool("False") is False
        assert _convert_to_bool("FALSE") is False
        assert _convert_to_bool("") is None
        assert _convert_to_bool("N/A") is None
        assert _convert_to_bool("invalid") is None


class TestInventoryParser:
    """Test inventory parsing."""

    @pytest.fixture
    def inventory_output_8010(self):
        """Real output from EH-8010FX device."""
        return """
inventory 1 desc                      : EH-8010FX-AES-H
inventory 1 cont-in                   : 0
inventory 1 class                     : chassis
inventory 1 rel-pos                   : -1
inventory 1 name                      : Chassis
inventory 1 hw-rev                    : D1
inventory 1 fw-rev                    : 
inventory 1 sw-rev                    : 10.8.2-19419-f50a23d53d
inventory 1 serial                    : FC18594555
inventory 1 mfg-name                  : Siklu
inventory 1 model-name                : EH-8010FX-ODUH-A-2C1P-EX-D
inventory 1 fru                       : true

inventory 2 desc                      : BB Board
inventory 2 cont-in                   : 1
inventory 2 class                     : container
inventory 2 rel-pos                   : 0
inventory 2 name                      : Base Band
inventory 2 hw-rev                    : 2.0.
inventory 2 fw-rev                    : 
inventory 2 sw-rev                    : 
inventory 2 serial                    : FC17588055
inventory 2 mfg-name                  : Siklu
inventory 2 model-name                : 
inventory 2 fru                       : false

inventory 6 desc                      : Modem Chip
inventory 6 cont-in                   : 2
inventory 6 class                     : container
inventory 6 rel-pos                   : 0
inventory 6 name                      : Modem
inventory 6 hw-rev                    : 110
inventory 6 fw-rev                    : 
inventory 6 sw-rev                    : 
inventory 6 serial                    : 
inventory 6 mfg-name                  : Siklu
inventory 6 model-name                : 
inventory 6 fru                       : false

inventory 14 desc                      : Dual media: SFP (empty)
inventory 14 cont-in                   : 10
inventory 14 class                     : module
inventory 14 rel-pos                   : 0
inventory 14 name                      : Sfp eth2
inventory 14 hw-rev                    : 
inventory 14 fw-rev                    : 
inventory 14 sw-rev                    : 
inventory 14 serial                    : 
inventory 14 mfg-name                  : N/A
inventory 14 model-name                : 
inventory 14 fru                       : true
"""

    def test_parse_inventory_structure(self, inventory_output_8010):
        """Test hierarchical structure is correctly built."""
        result = parse_inventory(inventory_output_8010)

        assert "chassis" in result
        chassis = result["chassis"]

        # Verify chassis fields
        assert chassis["id"] == 1
        assert chassis["desc"] == "EH-8010FX-AES-H"
        assert chassis["serial"] == "FC18594555"
        assert chassis["hw_rev"] == "D1"
        assert chassis["sw_rev"] == "10.8.2-19419-f50a23d53d"
        assert chassis["fru"] is True
        assert chassis["cont_in"] == 0

        # Verify chassis has components
        assert "components" in chassis
        assert len(chassis["components"]) > 0

    def test_parse_inventory_nested_components(self, inventory_output_8010):
        """Test nested component hierarchy."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]

        # Find BB Board (should be in chassis components)
        bb_board = None
        for comp in chassis["components"]:
            if comp["desc"] == "BB Board":
                bb_board = comp
                break

        assert bb_board is not None
        assert bb_board["id"] == 2
        assert bb_board["cont_in"] == 1
        assert bb_board["fru"] is False

        # BB Board should have nested components (Modem)
        assert "components" in bb_board
        modem = None
        for comp in bb_board["components"]:
            if comp["desc"] == "Modem Chip":
                modem = comp
                break

        assert modem is not None
        assert modem["id"] == 6
        assert modem["cont_in"] == 2

    def test_parse_inventory_empty_values(self, inventory_output_8010):
        """Test empty and N/A values are normalized to None."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]

        # Find component with empty values
        bb_board = chassis["components"][0]
        
        # Empty fields are set to None in the dict
        assert bb_board.get("fw_rev") is None
        assert bb_board.get("sw_rev") is None
        
        # Fields that have values should not be None
        assert bb_board["hw_rev"] is not None
        assert bb_board["serial"] is not None
        assert bb_board["mfg_name"] is not None

    def test_parse_inventory_type_conversions(self, inventory_output_8010):
        """Test field type conversions."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]

        # Integer conversions
        assert isinstance(chassis["id"], int)
        assert isinstance(chassis["cont_in"], int)
        assert isinstance(chassis["rel_pos"], int)

        # Boolean conversion
        assert isinstance(chassis["fru"], bool)
        assert chassis["fru"] is True


class TestRFStatusParser:
    """Test RF status parsing."""

    @pytest.fixture
    def rf_output_up(self):
        """RF output when link is up."""
        return """
rf operational               : up
rf tx-state                  : normal
rf rx-state                  : normal
rf cinr                      : 28
rf rssi                      : -28
rf channel-width             : 250
rf country                   : Worldwide
rf tx-frequency              : 82000
rf rx-frequency              : 72000
rf tx-mute                   : disable
rf tx-mute-timeout           : 60
rf mode                      : adaptive qam32
rf alignment-status          : inactive
rf alignment-max-rssi        : n/a
rf lowest-modulation         : bpsk1
rf tx-asymmetry              : 100tx-100rx
rf loopback-timeout          : 60
rf loopback-dst-mac          : 00:00:00:00:00:00
rf loopback                  : disabled
rf tx-power                  : 14
rf dtpc                      : disable
rf air-capacity              : 1000
"""

    @pytest.fixture
    def rf_output_down(self):
        """RF output when link is down."""
        return """
rf operational               : down
rf tx-state                  : sync
rf rx-state                  : sync
rf cinr                      : -128
rf rssi                      : -128
rf channel-width             : 250
rf country                   : Worldwide
rf tx-frequency              : 82000
rf rx-frequency              : 72000
rf tx-mute                   : disable
rf tx-mute-timeout           : 60
rf mode                      : alignment
rf alignment-status          : active
rf alignment-max-rssi        : n/a
rf lowest-modulation         : bpsk1
rf tx-asymmetry              : 100tx-100rx
rf loopback-timeout          : 60
rf loopback-dst-mac          : 00:00:00:00:00:00
rf loopback                  : disabled
rf tx-power                  : 14
rf dtpc                      : disable
rf air-capacity              : 0
"""

    def test_parse_rf_basic_fields(self, rf_output_up):
        """Test basic RF field parsing."""
        result = parse_rf_status(rf_output_up)

        assert result["operational"] == "up"
        assert result["tx_state"] == "normal"
        assert result["rx_state"] == "normal"
        assert result["mode"] == "adaptive qam32"
        assert result["country"] == "Worldwide"

    def test_parse_rf_int_fields(self, rf_output_up):
        """Test integer field conversions."""
        result = parse_rf_status(rf_output_up)

        assert isinstance(result["tx_frequency"], int)
        assert result["tx_frequency"] == 82000
        assert isinstance(result["rx_frequency"], int)
        assert result["rx_frequency"] == 72000
        assert isinstance(result["channel_width"], int)
        assert result["channel_width"] == 250
        assert isinstance(result["tx_power"], int)
        assert result["tx_power"] == 14
        assert isinstance(result["air_capacity"], int)
        assert result["air_capacity"] == 1000

    def test_parse_rf_float_fields(self, rf_output_up):
        """Test float field conversions for CINR and RSSI."""
        result = parse_rf_status(rf_output_up)

        assert isinstance(result["cinr"], float)
        assert result["cinr"] == 28.0
        assert isinstance(result["rssi"], float)
        assert result["rssi"] == -28.0

    def test_parse_rf_special_values(self, rf_output_down):
        """Test special values like -128 and n/a."""
        result = parse_rf_status(rf_output_down)

        # -128 should remain as float (not converted to None)
        assert result["cinr"] == -128.0
        assert result["rssi"] == -128.0

        # n/a should become None
        assert result["alignment_max_rssi"] is None

    def test_parse_rf_string_fields(self, rf_output_up):
        """Test fields that remain as strings."""
        result = parse_rf_status(rf_output_up)

        # These should remain strings (not converted to bool)
        assert result["tx_mute"] == "disable"
        assert result["loopback"] == "disabled"
        assert result["dtpc"] == "disable"


class TestConfigurationParser:
    """Test configuration parsing."""

    @pytest.fixture
    def config_output(self):
        """Sample configuration output."""
        return """
####====####  Generated by ver. 10.8.2, convert ver. 3
# license configuring
set license data-rate config 10000

# syslog configuring

# auth-settings configuring
set auth-settings  password-min-length 8  password-min-difference 1

# ip configuring
set ip 1  ip-addr 'static 172.18.128.2'  prefix-len 24  vlan 128

# route configuring
set route 1  prefix-len 0  dest 0.0.0.0  next-hop 172.18.128.1

# system configuring
set system  contact undefined  name EH-8010FX-AES-H

# rf configuring
set rf  mode 'adaptive qam32'  tx-power 14  lowest-modulation bpsk1
"""

    def test_parse_configuration_preserves_structure(self, config_output):
        """Test that configuration structure is preserved."""
        result = parse_configuration(config_output)

        assert isinstance(result, str)
        assert "Generated by ver. 10.8.2" in result
        assert "set license data-rate config 10000" in result
        assert "set ip 1" in result
        assert "set route 1" in result

    def test_parse_configuration_removes_empty_lines(self, config_output):
        """Test that excessive empty lines are removed."""
        result = parse_configuration(config_output)

        # Should not have consecutive empty lines
        assert "\n\n\n" not in result

    def test_parse_configuration_keeps_comments(self, config_output):
        """Test that comment lines are preserved."""
        result = parse_configuration(config_output)

        assert "# license configuring" in result
        assert "# ip configuring" in result
        assert "# rf configuring" in result

    def test_parse_inventory_orphaned_components(self):
        """Verify that orphaned components (invalid cont-in) are handled gracefully."""
        orphaned_output = """
    inventory 1 desc                      : Chassis
    inventory 1 cont-in                   : 0
    inventory 1 class                     : chassis
    inventory 1 serial                    : TEST123
    inventory 1 fru                       : true

    inventory 99 desc                      : Orphaned Module
    inventory 99 cont-in                   : 50
    inventory 99 class                     : module
    inventory 99 serial                    : ORPHAN999
    inventory 99 fru                       : false
    """
        result = parse_inventory(orphaned_output)
        chassis = result["chassis"]

        # Chassis should exist
        assert chassis["id"] == 1
        assert chassis["serial"] == "TEST123"

        assert len(chassis["components"]) == 0

        def find_component_recursive(comp_tree: list, comp_id: int) -> bool:
            for comp in comp_tree:
                if comp["id"] == comp_id:
                    return True
                if find_component_recursive(comp.get("components", []), comp_id):
                    return True
            return False

        assert not find_component_recursive(chassis.get("components", []), 99), \
            "Orphaned component should not appear in hierarchy"


class TestRollbackParser:
    """Test rollback status parsing."""

    @pytest.fixture
    def rollback_not_started(self):
        """Rollback output when not active."""
        return "rollback timeout                   : not started\n"

    @pytest.fixture
    def rollback_active(self):
        """Rollback output when active with 9000 second timeout."""
        return "rollback timeout                   : 9000\n"

    @pytest.fixture
    def rollback_active_short(self):
        """Rollback output with short timeout."""
        return "rollback timeout                   : 300\n"

    def test_parse_rollback_not_started(self, rollback_not_started):
        """Test parsing when rollback is not started."""
        result = parse_rollback_status(rollback_not_started)

        assert result['active'] is False
        assert result['timeout'] is None

    def test_parse_rollback_active(self, rollback_active):
        """Test parsing when rollback is active."""
        result = parse_rollback_status(rollback_active)

        assert result['active'] is True
        assert isinstance(result['timeout'], int)
        assert result['timeout'] == 9000

    def test_parse_rollback_active_short_timeout(self, rollback_active_short):
        """Test parsing with different timeout value."""
        result = parse_rollback_status(rollback_active_short)

        assert result['active'] is True
        assert result['timeout'] == 300

    def test_parse_rollback_empty_output(self):
        """Test parsing with empty output."""
        result = parse_rollback_status("")

        # Should return default values
        assert result['active'] is False
        assert result['timeout'] is None

    def test_parse_rollback_malformed_timeout(self):
        """Test parsing with malformed timeout value."""
        result = parse_rollback_status("rollback timeout                   : invalid\n")
        assert result['active'] is False
        assert result['timeout'] is None
