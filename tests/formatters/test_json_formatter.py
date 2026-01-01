"""
Test cases for logify.formatters.json_formatter module
"""

import json
import pytest
import sys
from datetime import datetime
from logify.formatters.json_formatter import JsonFormatter
from logify.core.record import LogRecord
from logify.core.levels import DEBUG, INFO, WARNING, ERROR, CRITICAL


class TestJsonFormatterInit:
    """Test JsonFormatter initialization"""

    def test_default_init(self):
        """Test default initialization"""
        formatter = JsonFormatter()
        
        assert formatter._fields is None
        assert formatter._indent is None
        assert formatter._ensure_ascii is False
        assert formatter._timestamp_format == "iso"
        assert formatter._extra_fields == {}
        assert formatter._json_encoder is None

    def test_custom_fields(self):
        """Test initialization with custom fields"""
        fields = ["timestamp", "level", "message"]
        formatter = JsonFormatter(fields=fields)
        
        assert formatter._fields == fields

    def test_custom_indent(self):
        """Test initialization with custom indent"""
        formatter = JsonFormatter(indent=2)
        
        assert formatter._indent == 2

    def test_ensure_ascii(self):
        """Test initialization with ensure_ascii"""
        formatter = JsonFormatter(ensure_ascii=True)
        
        assert formatter._ensure_ascii is True

    def test_timestamp_format_epoch(self):
        """Test initialization with epoch timestamp format"""
        formatter = JsonFormatter(timestamp_format="epoch")
        
        assert formatter._timestamp_format == "epoch"

    def test_extra_fields(self):
        """Test initialization with extra fields"""
        extra = {"app": "myapp", "version": "1.0"}
        formatter = JsonFormatter(extra_fields=extra)
        
        assert formatter._extra_fields == extra

    def test_custom_encoder(self):
        """Test initialization with custom encoder"""
        def my_encoder(obj):
            return str(obj)
        
        formatter = JsonFormatter(json_encoder=my_encoder)
        
        assert formatter._json_encoder is my_encoder

    def test_custom_name(self):
        """Test initialization with custom name"""
        formatter = JsonFormatter(name="MyJsonFormatter")
        
        assert formatter.name == "MyJsonFormatter"


class TestJsonFormatterFormatTimestamp:
    """Test JsonFormatter._format_timestamp() method"""

    def test_iso_format(self):
        """Test ISO timestamp format"""
        formatter = JsonFormatter(timestamp_format="iso")
        timestamp = 1609459200.0
        
        result = formatter._format_timestamp(timestamp)
        
        expected = datetime.fromtimestamp(timestamp).isoformat()
        assert result == expected

    def test_epoch_format(self):
        """Test epoch timestamp format"""
        formatter = JsonFormatter(timestamp_format="epoch")
        timestamp = 1609459200.0
        
        result = formatter._format_timestamp(timestamp)
        
        assert result == "1609459200.0"


class TestJsonFormatterFormat:
    """Test JsonFormatter.format() method"""

    def test_format_returns_valid_json(self):
        """Test that format returns valid JSON"""
        formatter = JsonFormatter()
        record = LogRecord(name="test", level=INFO, msg="Hello world")
        
        result = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_contains_basic_fields(self):
        """Test that formatted JSON contains basic fields"""
        formatter = JsonFormatter()
        record = LogRecord(name="mylogger", level=WARNING, msg="Warning message")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["logger"] == "mylogger"
        assert parsed["level"] == "WARNING"
        assert parsed["message"] == "Warning message"

    def test_format_contains_level_no(self):
        """Test that formatted JSON contains level number"""
        formatter = JsonFormatter()
        record = LogRecord(name="test", level=ERROR, msg="Test")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["level_no"] == ERROR

    def test_format_contains_timestamp(self):
        """Test that formatted JSON contains timestamp"""
        formatter = JsonFormatter()
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed

    def test_format_contains_location_info(self):
        """Test that formatted JSON contains location info"""
        formatter = JsonFormatter()
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="test.py",
            lineno=42,
            func_name="test_func"
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["filename"] == "test.py"
        assert parsed["lineno"] == 42
        assert parsed["func_name"] == "test_func"

    def test_format_contains_thread_and_process(self):
        """Test that formatted JSON contains thread and process info"""
        formatter = JsonFormatter()
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "thread_id" in parsed
        assert "thread_name" in parsed
        assert "process_id" in parsed

    def test_format_with_indent(self):
        """Test that format with indent produces indented JSON"""
        formatter = JsonFormatter(indent=2)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        
        # Indented JSON should have newlines
        assert "\n" in result
        # Should still be valid JSON
        parsed = json.loads(result)
        assert parsed["message"] == "Test"

    def test_format_without_indent(self):
        """Test that format without indent produces compact JSON"""
        formatter = JsonFormatter(indent=None)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        
        # Compact JSON should be on one line (no newlines except in values)
        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_format_with_ensure_ascii(self):
        """Test format with ensure_ascii=True"""
        formatter = JsonFormatter(ensure_ascii=True)
        record = LogRecord(name="test", level=INFO, msg="你好世界")
        
        result = formatter.format(record)
        
        # Chinese characters should be escaped
        assert "\\u" in result
        # But should still parse correctly
        parsed = json.loads(result)
        assert parsed["message"] == "你好世界"

    def test_format_without_ensure_ascii(self):
        """Test format with ensure_ascii=False"""
        formatter = JsonFormatter(ensure_ascii=False)
        record = LogRecord(name="test", level=INFO, msg="你好世界")
        
        result = formatter.format(record)
        
        # Chinese characters should be preserved
        assert "你好世界" in result

    def test_format_with_extra_fields(self):
        """Test format includes extra fields from record"""
        formatter = JsonFormatter()
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            extra={"user_id": 123, "session": "abc"}
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["user_id"] == 123
        assert parsed["session"] == "abc"

    def test_format_with_kwargs(self):
        """Test format includes kwargs from record"""
        formatter = JsonFormatter()
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            kwargs={"request_id": "xyz-789"}
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["request_id"] == "xyz-789"

    def test_format_with_fixed_extra_fields(self):
        """Test format includes fixed extra fields from formatter"""
        formatter = JsonFormatter(extra_fields={"app": "myapp", "env": "prod"})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["app"] == "myapp"
        assert parsed["env"] == "prod"


class TestJsonFormatterWithFieldsFilter:
    """Test JsonFormatter with fields filter"""

    def test_format_with_specific_fields(self):
        """Test format only includes specified fields"""
        formatter = JsonFormatter(fields=["timestamp", "level", "message"])
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed
        assert "logger" not in parsed
        assert "filename" not in parsed

    def test_format_with_single_field(self):
        """Test format with only message field"""
        formatter = JsonFormatter(fields=["message"])
        record = LogRecord(name="test", level=INFO, msg="Only message")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert len(parsed) == 1
        assert parsed["message"] == "Only message"

    def test_format_ignores_nonexistent_fields(self):
        """Test that nonexistent fields are ignored"""
        formatter = JsonFormatter(fields=["message", "nonexistent_field"])
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "message" in parsed
        assert "nonexistent_field" not in parsed


class TestJsonFormatterWithException:
    """Test JsonFormatter with exception info"""

    def test_format_with_exception(self):
        """Test format includes exception info"""
        formatter = JsonFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            record = LogRecord(
                name="test",
                level=ERROR,
                msg="An error occurred",
                exception_info=sys.exc_info()
            )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test error" in parsed["exception"]

    def test_format_without_exception(self):
        """Test format without exception has no exception field"""
        formatter = JsonFormatter()
        record = LogRecord(name="test", level=INFO, msg="Normal message")
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "exception" not in parsed


class TestJsonFormatterCustomEncoder:
    """Test JsonFormatter with custom encoder"""

    def test_format_with_custom_encoder(self):
        """Test format uses custom encoder for non-serializable objects"""
        class CustomObject:
            def __init__(self, value):
                self.value = value
            
            def __str__(self):
                return f"CustomObject({self.value})"
        
        formatter = JsonFormatter()
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            extra={"custom": CustomObject(42)}
        )
        
        # Should not raise, should use default str() encoder
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "CustomObject(42)" in parsed["custom"]


class TestJsonFormatterFormattedMessage:
    """Test JsonFormatter uses formatted message"""

    def test_format_uses_formatted_message(self):
        """Test that message field contains formatted message"""
        formatter = JsonFormatter()
        record = LogRecord(
            name="test",
            level=INFO,
            msg="User %s logged in",
            args=("john",)
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["message"] == "User john logged in"


class TestJsonFormatterRepr:
    """Test JsonFormatter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        formatter = JsonFormatter()
        repr_str = repr(formatter)
        
        assert "JsonFormatter" in repr_str

    def test_repr_contains_fields(self):
        """Test that repr contains fields info"""
        formatter = JsonFormatter(fields=["message"])
        repr_str = repr(formatter)
        
        assert "fields=" in repr_str


class TestJsonFormatterAllLevels:
    """Test JsonFormatter with all log levels"""

    def test_format_all_levels(self):
        """Test formatting works for all log levels"""
        formatter = JsonFormatter()
        
        levels = [
            (DEBUG, "DEBUG"),
            (INFO, "INFO"),
            (WARNING, "WARNING"),
            (ERROR, "ERROR"),
            (CRITICAL, "CRITICAL"),
        ]
        
        for level, expected_name in levels:
            record = LogRecord(name="test", level=level, msg="Test")
            result = formatter.format(record)
            parsed = json.loads(result)
            
            assert parsed["level"] == expected_name
            assert parsed["level_no"] == level


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
