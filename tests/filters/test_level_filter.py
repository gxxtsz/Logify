"""
Test cases for logify.filters.level_filter module
"""

import pytest
from logify.filters.level_filter import LevelFilter
from logify.core.record import LogRecord
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL


class TestLevelFilterCreation:
    """Test LevelFilter initialization"""

    def test_default_level_is_debug(self):
        """Test that default level is DEBUG"""
        filter_ = LevelFilter()
        assert filter_.level == DEBUG

    def test_create_with_log_level_enum(self):
        """Test creating with LogLevel enum"""
        filter_ = LevelFilter(level=LogLevel.WARNING)
        assert filter_.level == WARNING

    def test_create_with_integer(self):
        """Test creating with integer level"""
        filter_ = LevelFilter(level=30)
        assert filter_.level == 30

    def test_create_with_string(self):
        """Test creating with string level name"""
        filter_ = LevelFilter(level="ERROR")
        assert filter_.level == ERROR

    def test_create_with_lowercase_string(self):
        """Test creating with lowercase string level name"""
        filter_ = LevelFilter(level="warning")
        assert filter_.level == WARNING

    def test_create_with_invalid_string(self):
        """Test creating with invalid string defaults to DEBUG"""
        filter_ = LevelFilter(level="INVALID")
        assert filter_.level == DEBUG

    def test_create_with_custom_name(self):
        """Test creating with custom filter name"""
        filter_ = LevelFilter(level=INFO, name="MyLevelFilter")
        assert filter_.name == "MyLevelFilter"


class TestLevelFilterProperty:
    """Test LevelFilter.level property"""

    def test_level_getter(self):
        """Test getting level"""
        filter_ = LevelFilter(level=WARNING)
        assert filter_.level == WARNING

    def test_level_setter_with_enum(self):
        """Test setting level with enum"""
        filter_ = LevelFilter(level=DEBUG)
        filter_.level = LogLevel.ERROR
        assert filter_.level == ERROR

    def test_level_setter_with_int(self):
        """Test setting level with integer"""
        filter_ = LevelFilter(level=DEBUG)
        filter_.level = 40
        assert filter_.level == 40

    def test_level_setter_with_string(self):
        """Test setting level with string"""
        filter_ = LevelFilter(level=DEBUG)
        filter_.level = "critical"
        assert filter_.level == CRITICAL


class TestLevelFilterFilter:
    """Test LevelFilter.filter() method"""

    def test_pass_when_level_equal(self):
        """Test that record passes when level equals filter level"""
        filter_ = LevelFilter(level=INFO)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_pass_when_level_higher(self):
        """Test that record passes when level is higher than filter level"""
        filter_ = LevelFilter(level=INFO)
        record = LogRecord(name="test", level=ERROR, msg="Test")
        
        assert filter_.filter(record) is True

    def test_fail_when_level_lower(self):
        """Test that record fails when level is lower than filter level"""
        filter_ = LevelFilter(level=WARNING)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_debug_level_passes_all(self):
        """Test that DEBUG level filter passes all records"""
        filter_ = LevelFilter(level=DEBUG)
        
        for level in [DEBUG, INFO, WARNING, ERROR, CRITICAL]:
            record = LogRecord(name="test", level=level, msg="Test")
            assert filter_.filter(record) is True

    def test_critical_level_only_passes_critical(self):
        """Test that CRITICAL level filter only passes CRITICAL"""
        filter_ = LevelFilter(level=CRITICAL)
        
        for level in [DEBUG, INFO, WARNING, ERROR]:
            record = LogRecord(name="test", level=level, msg="Test")
            assert filter_.filter(record) is False
        
        record = LogRecord(name="test", level=CRITICAL, msg="Test")
        assert filter_.filter(record) is True

    def test_filter_all_levels(self):
        """Test filtering with all log levels"""
        test_cases = [
            (DEBUG, [DEBUG, INFO, WARNING, ERROR, CRITICAL]),
            (INFO, [INFO, WARNING, ERROR, CRITICAL]),
            (WARNING, [WARNING, ERROR, CRITICAL]),
            (ERROR, [ERROR, CRITICAL]),
            (CRITICAL, [CRITICAL]),
        ]
        
        for filter_level, expected_pass in test_cases:
            filter_ = LevelFilter(level=filter_level)
            
            for level in LogLevel:
                record = LogRecord(name="test", level=level, msg="Test")
                result = filter_.filter(record)
                
                if level in expected_pass:
                    assert result is True, f"Level {level} should pass filter {filter_level}"
                else:
                    assert result is False, f"Level {level} should fail filter {filter_level}"


class TestLevelFilterRepr:
    """Test LevelFilter.__repr__() method"""

    def test_repr_contains_level_name(self):
        """Test that repr contains level name"""
        filter_ = LevelFilter(level=WARNING)
        repr_str = repr(filter_)
        
        assert "LevelFilter" in repr_str
        assert "WARNING" in repr_str

    def test_repr_for_all_levels(self):
        """Test repr for all log levels"""
        for level in LogLevel:
            filter_ = LevelFilter(level=level)
            repr_str = repr(filter_)
            
            assert level.name in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
