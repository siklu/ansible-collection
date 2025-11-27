"""
Unit tests for Siklu EH parsers.

Tests helper functions, inventory/rf/config/rollback/system/sw/ip/route parsers,
and set command validations.
"""

import pytest
from ansible_collections.siklu.eh.plugins.module_utils.siklu_eh.parsers import (
    parse_inventory,
    parse_rf_status,
    parse_configuration,
    parse_rollback_status,
    parse_system_info,
    parse_sw_info,
    parse_ip_config,
    parse_route_config,
    validate_set_ip_response,
    validate_set_route_response,
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


# ================== INVENTORY PARSER TESTS ====================

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

        assert chassis["id"] == 1
        assert chassis["desc"] == "EH-8010FX-AES-H"
        assert chassis["serial"] == "FC18594555"
        assert chassis["hw_rev"] == "D1"
        assert chassis["sw_rev"] == "10.8.2-19419-f50a23d53d"
        assert chassis["fru"] is True
        assert chassis["cont_in"] == 0
        assert "components" in chassis
        assert len(chassis["components"]) > 0

    def test_parse_inventory_nested_components(self, inventory_output_8010):
        """Test nested component hierarchy."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]
        bb_board = next(
            (comp for comp in chassis["components"]
             if comp["desc"] == "BB Board"),
            None
        )
        assert bb_board is not None
        assert bb_board["id"] == 2
        assert bb_board["cont_in"] == 1
        assert bb_board["fru"] is False
        assert "components" in bb_board
        modem = next(
            (comp for comp in bb_board["components"]
             if comp["desc"] == "Modem Chip"),
            None
        )
        assert modem is not None
        assert modem["id"] == 6
        assert modem["cont_in"] == 2

    def test_parse_inventory_empty_values(self, inventory_output_8010):
        """Test empty and N/A values are normalized to None."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]
        bb_board = chassis["components"][0]

        # Empty fields are set to None in the dict
        assert bb_board.get("fw_rev") is None
        assert bb_board.get("sw_rev") is None

        # Fields that have values should not be None
        assert bb_board["hw_rev"] is not None
        assert bb_board["serial"] is not None

    def test_parse_inventory_type_conversions(self, inventory_output_8010):
        """Test field type conversions."""
        result = parse_inventory(inventory_output_8010)
        chassis = result["chassis"]
        assert isinstance(chassis["id"], int)
        assert isinstance(chassis["cont_in"], int)
        assert isinstance(chassis["rel_pos"], int)
        assert isinstance(chassis["fru"], bool)
        assert chassis["fru"] is True

    def test_parse_inventory_orphaned_components(self):
        """Test orphaned components (invalid cont-in) are handled."""
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
        assert chassis["id"] == 1
        assert chassis["serial"] == "TEST123"
        assert len(chassis["components"]) == 0

        def find_component_recursive(comp_tree: list, comp_id: int) -> bool:
            """Recursively search for component by ID."""
            for comp in comp_tree:
                if comp["id"] == comp_id:
                    return True
                if find_component_recursive(
                    comp.get("components", []), comp_id
                ):
                    return True
            return False

        assert not find_component_recursive(
            chassis.get("components", []), 99
        ), "Orphaned component should not appear in hierarchy"


# ================== RF STATUS PARSER TESTS ====================

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
        assert result["tx_frequency"] == 82000
        assert result["rx_frequency"] == 72000
        assert result["channel_width"] == 250
        assert result["tx_power"] == 14
        assert result["air_capacity"] == 1000

    def test_parse_rf_float_fields(self, rf_output_up):
        """Test float field conversions for CINR and RSSI."""
        result = parse_rf_status(rf_output_up)
        assert result["cinr"] == 28.0
        assert result["rssi"] == -28.0

    def test_parse_rf_special_values(self, rf_output_down):
        """Test special values like -128 and n/a."""
        result = parse_rf_status(rf_output_down)
        assert result["cinr"] == -128.0
        assert result["rssi"] == -128.0
        assert result["alignment_max_rssi"] is None

    def test_parse_rf_string_fields(self, rf_output_up):
        """Test fields that remain as strings."""
        result = parse_rf_status(rf_output_up)
        assert result["tx_mute"] == "disable"
        assert result["loopback"] == "disabled"
        assert result["dtpc"] == "disable"


# ================== CONFIGURATION PARSER TESTS ====================

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
        assert "\n\n\n" not in result

    def test_parse_configuration_keeps_comments(self, config_output):
        """Test that comment lines are preserved."""
        result = parse_configuration(config_output)
        assert "# license configuring" in result
        assert "# ip configuring" in result
        assert "# rf configuring" in result


# ================== ROLLBACK PARSER TESTS ====================

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
        assert result['timeout'] == 9000

    def test_parse_rollback_active_short_timeout(self, rollback_active_short):
        """Test parsing with different timeout value."""
        result = parse_rollback_status(rollback_active_short)
        assert result['active'] is True
        assert result['timeout'] == 300

    def test_parse_rollback_empty_output(self):
        """Test parsing with empty output."""
        result = parse_rollback_status("")
        assert result['active'] is False
        assert result['timeout'] is None

    def test_parse_rollback_malformed_timeout(self):
        """Test parsing with malformed timeout value."""
        result = parse_rollback_status(
            "rollback timeout                   : invalid\n"
        )
        assert result['active'] is False
        assert result['timeout'] is None


# ============= SYSTEM/SW/IP/ROUTE PARSERS TESTS (NEW) =============

class TestSystemInfoParser:
    """Test system info parsing."""

    def test_parse_system_info_eh8010fx(self):
        """Test parsing EH-8010FX system info."""
        output = """
system description               : EH-8010FX
system snmpid                    : .1.3.6.1.4.1.31926
system uptime                    : 0000:04:31:14
system contact                   : undefined
system name                      : EH8010FX-L
system hostname                  : sw
system location                  : undefined
system voltage                   : poe (injector)
system temperature               : 54
system date                      : 2025.08.30
system time                      : 15:29:40
system cli-timeout               : 15
system loop-permission           : mac-swap
system antenna-heater            : disabled
system heartbeat-trap-period     : 0
"""
        info = parse_system_info(output)
        assert info["model"] == "EH-8010FX"
        assert info["snmp_id"] == ".1.3.6.1.4.1.31926"
        assert info["uptime"] == "0000:04:31:14"
        assert info["contact"] == "undefined"
        assert info["name"] == "EH8010FX-L"
        assert info["hostname"] == "sw"
        assert info["location"] == "undefined"
        assert info["voltage"] == "poe (injector)"
        assert info["temperature"] == 54
        assert isinstance(info["temperature"], int)
        assert info["date"] == "2025.08.30"
        assert info["time"] == "15:29:40"
        assert info["cli_timeout"] == 15
        assert isinstance(info["cli_timeout"], int)
        assert info["loop_permission"] == "mac-swap"
        assert info["antenna_heater"] == "disabled"
        assert info["heartbeat_trap_period"] == 0
        assert isinstance(info["heartbeat_trap_period"], int)

    def test_parse_system_info_eh8020fx(self):
        """Test parsing EH-8020FX system info."""
        output = """
system description               : EH-8020FX
system snmpid                    : .1.3.6.1.4.1.31926.36
system uptime                    : 0015:01:19:18
system contact                   : undefined
system name                      : EH-8020FX
system hostname                  : sw
system location                  : undefined
system voltage                   : poe
system temperature               : 47
system date                      : 2025.11.27
system time                      : 14:59:27
system cli-timeout               : 15
system loop-permission           : enabled
system antenna-heater            : disabled
system heartbeat-trap-period     : 0
"""
        info = parse_system_info(output)
        assert info["model"] == "EH-8020FX"
        assert info["snmp_id"] == ".1.3.6.1.4.1.31926.36"
        assert info["uptime"] == "0015:01:19:18"
        assert info["voltage"] == "poe"
        assert info["temperature"] == 47
        assert info["loop_permission"] == "enabled"


class TestSWInfoParser:
    """Test software info parsing."""

    def test_parse_sw_info_two_banks_with_warning(self):
        """Test parsing with two banks and WARNING line (ignored)."""
        output = """
Flash Bank    Version                           Running     Scheduled to run    startup-config
1             10.6.0-18451-c009ec33d1           yes         no                  exists
2             10.6.0-18618-74a2427065           no          no                  missing

WARNING: Active sw version does not match running bank version!
"""
        info = parse_sw_info(output)
        assert "running" in info
        assert "standby" in info

        # Bank 1 is running
        assert info["running"]["version"] == "10.6.0-18451-c009ec33d1"
        assert info["running"]["bank"] == 1
        assert info["running"]["scheduled_to_run"] is False
        assert info["running"]["startup_config"] is True

        # Bank 2 is standby
        assert info["standby"]["version"] == "10.6.0-18618-74a2427065"
        assert info["standby"]["bank"] == 2
        assert info["standby"]["scheduled_to_run"] is False
        assert info["standby"]["startup_config"] is False

    def test_parse_sw_info_both_banks_same_version(self):
        """Test parsing when both banks have same version."""
        output = """
Flash Bank    Version                           Running     Scheduled to run    startup-config
1             10.8.0-19319-b36c7a6f08           yes         no                  missing
2             10.8.0-19319-b36c7a6f08           no          no                  missing
"""
        info = parse_sw_info(output)
        assert "running" in info
        assert "standby" in info

        # Both banks have same version
        assert info["running"]["version"] == "10.8.0-19319-b36c7a6f08"
        assert info["standby"]["version"] == "10.8.0-19319-b36c7a6f08"

        # Both banks missing startup config
        assert info["running"]["startup_config"] is False
        assert info["standby"]["startup_config"] is False


class TestIPConfigParser:
    """Test IP configuration parsing."""

    def test_parse_ip_config_single_slot(self):
        """Test parsing single IP slot configuration."""
        output = """
ip 1 ip-addr                   : static 172.18.102.2
ip 1 prefix-len                : 24
ip 1 vlan                      : 102
ip 1 default-gateway           : 172.18.102.1
"""
        config = parse_ip_config(output)
        assert 1 in config
        slot1 = config[1]
        assert slot1["ip"] == "172.18.102.2"
        assert slot1["prefix_len"] == 24
        assert slot1["vlan"] == 102
        assert slot1["default_gateway"] == "172.18.102.1"

    def test_parse_ip_config_multiple_slots(self):
        """Test parsing multiple IP slot configurations."""
        output = """
ip 1 ip-addr                   : static 172.18.102.2
ip 1 prefix-len                : 24
ip 1 vlan                      : 102
ip 1 default-gateway           : 172.18.102.1

ip 3 ip-addr                   : static 100.100.100.100
ip 3 prefix-len                : 24
ip 3 vlan                      : 100
ip 3 default-gateway           : 0.0.0.0
"""
        config = parse_ip_config(output)
        assert 1 in config
        assert 3 in config

        # Slot 1
        slot1 = config[1]
        assert slot1["ip"] == "172.18.102.2"
        assert slot1["prefix_len"] == 24
        assert slot1["vlan"] == 102
        assert slot1["default_gateway"] == "172.18.102.1"

        # Slot 3 with unconfigured gateway (0.0.0.0)
        slot3 = config[3]
        assert slot3["ip"] == "100.100.100.100"
        assert slot3["prefix_len"] == 24
        assert slot3["vlan"] == 100
        assert slot3["default_gateway"] == "0.0.0.0"


class TestRouteConfigParser:
    """Test route configuration parsing."""

    def test_parse_route_config_single_route(self):
        """Test parsing single route configuration."""
        output = """
route 1 dest                      : 0.0.0.0
route 1 prefix-len                : 0
route 1 next-hop                  : 172.18.102.1
"""
        config = parse_route_config(output)
        assert 1 in config
        route1 = config[1]
        assert route1["dest"] == "0.0.0.0"
        assert route1["prefix_len"] == 0
        assert route1["next_hop"] == "172.18.102.1"

    def test_parse_route_config_multiple_routes(self):
        """Test parsing multiple route configurations."""
        output = """
route 1 dest                      : 0.0.0.0
route 1 prefix-len                : 0
route 1 next-hop                  : 172.18.102.1

route 5 dest                      : 1.2.3.0
route 5 prefix-len                : 24
route 5 next-hop                  : 100.100.100.1
"""
        config = parse_route_config(output)
        assert 1 in config
        assert 5 in config

        # Default route
        route1 = config[1]
        assert route1["dest"] == "0.0.0.0"
        assert route1["prefix_len"] == 0
        assert route1["next_hop"] == "172.18.102.1"

        # Custom route
        route5 = config[5]
        assert route5["dest"] == "1.2.3.0"
        assert route5["prefix_len"] == 24
        assert route5["next_hop"] == "100.100.100.1"


class TestSetCommandValidators:
    """Test set command response validators."""

    def test_validate_set_ip_response_success(self):
        """Test validation of successful set ip response."""
        response = "Set done: ip 3"
        assert validate_set_ip_response(response, 3) is True

        response = "Set done: ip 1"
        assert validate_set_ip_response(response, 1) is True

    def test_validate_set_ip_response_failure(self):
        """Test validation of failed set ip response."""
        # Wrong slot number
        response = "Set done: ip 3"
        assert validate_set_ip_response(response, 1) is False

        # Error messages
        assert validate_set_ip_response("% Operation failed", 1) is False
        assert validate_set_ip_response("", 1) is False

    def test_validate_set_route_response_success(self):
        """Test validation of successful set route response."""
        response = "Set done: route 5"
        assert validate_set_route_response(response, 5) is True

        response = "Set done: route 10"
        assert validate_set_route_response(response, 10) is True

    def test_validate_set_route_response_failure(self):
        """Test validation of failed set route response."""
        # Wrong slot number
        response = "Set done: route 5"
        assert validate_set_route_response(response, 1) is False

        # Error messages (real device errors)
        assert validate_set_route_response(
            "% Destination 1.2.3.4 is not a subnet. Operation failed",
            5
        ) is False
        assert validate_set_route_response(
            "% The ip subnet not found. Operation failed", 5
        ) is False
        assert validate_set_route_response(
            "% The next-hop 100.100.100.0 is the subnet address. "
            "Operation failed",
            5
        ) is False
        assert validate_set_route_response("", 1) is False
