"""
Test cases for logify.core.levels module
"""

import pytest
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL


class TestLogLevelEnum:
    """Test LogLevel enum basic properties"""

    def test_level_values(self):
        """Test that log levels have correct integer values"""
        assert LogLevel.DEBUG == 10
        assert LogLevel.INFO == 20
        assert LogLevel.WARNING == 30
        assert LogLevel.ERROR == 40
        assert LogLevel.CRITICAL == 50

    def test_level_ordering(self):
        """Test that log levels are ordered correctly (DEBUG < INFO < WARNING < ERROR < CRITICAL)"""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR
        assert LogLevel.ERROR < LogLevel.CRITICAL

    def test_level_comparison_with_int(self):
        """Test that log levels can be compared with integers"""
        assert LogLevel.DEBUG == 10
        assert LogLevel.INFO > 15
        assert LogLevel.WARNING < 35
        assert LogLevel.ERROR >= 40
        assert LogLevel.CRITICAL <= 50

    def test_level_is_int_enum(self):
        """Test that LogLevel is an IntEnum"""
        assert isinstance(LogLevel.DEBUG, int)
        assert isinstance(LogLevel.INFO, int)


class TestGetName:
    """Test LogLevel.get_name() class method"""

    def test_get_name_for_valid_levels(self):
        """Test get_name returns correct name for valid level values"""
        assert LogLevel.get_name(10) == "DEBUG"
        assert LogLevel.get_name(20) == "INFO"
        assert LogLevel.get_name(30) == "WARNING"
        assert LogLevel.get_name(40) == "ERROR"
        assert LogLevel.get_name(50) == "CRITICAL"

    def test_get_name_for_invalid_level(self):
        """Test get_name returns LEVEL_X format for unknown level values"""
        assert LogLevel.get_name(0) == "LEVEL_0"
        assert LogLevel.get_name(15) == "LEVEL_15"
        assert LogLevel.get_name(100) == "LEVEL_100"
        assert LogLevel.get_name(-5) == "LEVEL_-5"


class TestGetLevel:
    """Test LogLevel.get_level() class method"""

    def test_get_level_for_valid_names(self):
        """Test get_level returns correct LogLevel for valid names"""
        assert LogLevel.get_level("DEBUG") == LogLevel.DEBUG
        assert LogLevel.get_level("INFO") == LogLevel.INFO
        assert LogLevel.get_level("WARNING") == LogLevel.WARNING
        assert LogLevel.get_level("ERROR") == LogLevel.ERROR
        assert LogLevel.get_level("CRITICAL") == LogLevel.CRITICAL

    def test_get_level_case_insensitive(self):
        """Test get_level is case insensitive"""
        assert LogLevel.get_level("debug") == LogLevel.DEBUG
        assert LogLevel.get_level("Debug") == LogLevel.DEBUG
        assert LogLevel.get_level("DeBuG") == LogLevel.DEBUG
        assert LogLevel.get_level("info") == LogLevel.INFO
        assert LogLevel.get_level("Info") == LogLevel.INFO
        assert LogLevel.get_level("warning") == LogLevel.WARNING
        assert LogLevel.get_level("error") == LogLevel.ERROR
        assert LogLevel.get_level("critical") == LogLevel.CRITICAL

    def test_get_level_for_invalid_name(self):
        """Test get_level returns None for invalid names"""
        assert LogLevel.get_level("INVALID") is None
        assert LogLevel.get_level("") is None
        assert LogLevel.get_level("WARN") is None
        assert LogLevel.get_level("ERR") is None
        assert LogLevel.get_level("TRACE") is None


class TestGetAllLevels:
    """Test LogLevel.get_all_levels() class method"""

    def test_get_all_levels_returns_dict(self):
        """Test get_all_levels returns a dictionary"""
        result = LogLevel.get_all_levels()
        assert isinstance(result, dict)

    def test_get_all_levels_contains_all_levels(self):
        """Test get_all_levels contains all defined levels"""
        result = LogLevel.get_all_levels()
        assert len(result) == 5
        assert "DEBUG" in result
        assert "INFO" in result
        assert "WARNING" in result
        assert "ERROR" in result
        assert "CRITICAL" in result

    def test_get_all_levels_correct_values(self):
        """Test get_all_levels returns correct name-value mappings"""
        result = LogLevel.get_all_levels()
        assert result["DEBUG"] == 10
        assert result["INFO"] == 20
        assert result["WARNING"] == 30
        assert result["ERROR"] == 40
        assert result["CRITICAL"] == 50


class TestConvenienceConstants:
    """Test convenience constants exported from the module"""

    def test_convenience_constants_exist(self):
        """Test that convenience constants are exported"""
        assert DEBUG is not None
        assert INFO is not None
        assert WARNING is not None
        assert ERROR is not None
        assert CRITICAL is not None

    def test_convenience_constants_equal_enum_values(self):
        """Test that convenience constants equal their enum counterparts"""
        assert DEBUG == LogLevel.DEBUG
        assert INFO == LogLevel.INFO
        assert WARNING == LogLevel.WARNING
        assert ERROR == LogLevel.ERROR
        assert CRITICAL == LogLevel.CRITICAL

    def test_convenience_constants_are_log_level_instances(self):
        """Test that convenience constants are LogLevel instances"""
        assert isinstance(DEBUG, LogLevel)
        assert isinstance(INFO, LogLevel)
        assert isinstance(WARNING, LogLevel)
        assert isinstance(ERROR, LogLevel)
        assert isinstance(CRITICAL, LogLevel)

    def test_convenience_constants_values(self):
        """Test convenience constants have correct integer values"""
        assert DEBUG == 10
        assert INFO == 20
        assert WARNING == 30
        assert ERROR == 40
        assert CRITICAL == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
