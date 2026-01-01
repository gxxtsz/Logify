"""
Test cases for logify.core.record module
"""

import os
import time
import threading
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from logify.core.record import LogRecord
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR


class TestLogRecordCreation:
    """Test LogRecord creation and default values"""

    def test_create_basic_record(self):
        """Test creating a basic log record with required fields"""
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        assert record.name == "test"
        assert record.level == INFO
        assert record.msg == "Test message"

    def test_default_args_and_kwargs(self):
        """Test that args and kwargs default to empty"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert record.args == ()
        assert record.kwargs == {}

    def test_default_timestamp(self):
        """Test that timestamp is set automatically"""
        before = time.time()
        record = LogRecord(name="test", level=INFO, msg="Test")
        after = time.time()
        
        assert before <= record.timestamp <= after

    def test_custom_timestamp(self):
        """Test providing a custom timestamp"""
        custom_time = 1234567890.123
        record = LogRecord(name="test", level=INFO, msg="Test", timestamp=custom_time)
        
        assert record.timestamp == custom_time

    def test_default_thread_info(self):
        """Test that thread info is captured automatically"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert record.thread_id == threading.current_thread().ident
        assert record.thread_name == threading.current_thread().name

    def test_default_process_id(self):
        """Test that process ID is captured automatically"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert record.process_id == os.getpid()

    def test_default_exception_info(self):
        """Test that exception_info defaults to None"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert record.exception_info is None

    def test_default_extra(self):
        """Test that extra defaults to empty dict"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert record.extra == {}

    def test_custom_extra(self):
        """Test providing custom extra data"""
        extra_data = {"user_id": 123, "request_id": "abc"}
        record = LogRecord(name="test", level=INFO, msg="Test", extra=extra_data)
        
        assert record.extra == extra_data

    def test_all_log_levels(self):
        """Test creating records with all log levels"""
        for level in LogLevel:
            record = LogRecord(name="test", level=level, msg="Test")
            assert record.level == level


class TestLogRecordWithArgs:
    """Test LogRecord with message arguments"""

    def test_with_tuple_args(self):
        """Test creating record with positional args"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="User %s logged in from %s",
            args=("john", "192.168.1.1")
        )
        
        assert record.args == ("john", "192.168.1.1")

    def test_with_kwargs(self):
        """Test creating record with keyword args for structured logging"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="User action",
            kwargs={"user_id": 123, "action": "login"}
        )
        
        assert record.kwargs == {"user_id": 123, "action": "login"}


class TestLevelNameProperty:
    """Test LogRecord.level_name property"""

    def test_level_name_debug(self):
        """Test level_name for DEBUG level"""
        record = LogRecord(name="test", level=DEBUG, msg="Test")
        assert record.level_name == "DEBUG"

    def test_level_name_info(self):
        """Test level_name for INFO level"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        assert record.level_name == "INFO"

    def test_level_name_warning(self):
        """Test level_name for WARNING level"""
        record = LogRecord(name="test", level=WARNING, msg="Test")
        assert record.level_name == "WARNING"

    def test_level_name_error(self):
        """Test level_name for ERROR level"""
        record = LogRecord(name="test", level=ERROR, msg="Test")
        assert record.level_name == "ERROR"


class TestDatetimeProperty:
    """Test LogRecord.datetime property"""

    def test_datetime_type(self):
        """Test that datetime property returns datetime object"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert isinstance(record.datetime, datetime)

    def test_datetime_matches_timestamp(self):
        """Test that datetime matches the timestamp"""
        timestamp = 1609459200.0  # 2021-01-01 00:00:00 UTC
        record = LogRecord(name="test", level=INFO, msg="Test", timestamp=timestamp)
        
        expected = datetime.fromtimestamp(timestamp)
        assert record.datetime == expected


class TestFormattedTimeProperty:
    """Test LogRecord.formatted_time property"""

    def test_formatted_time_format(self):
        """Test formatted_time has correct format"""
        # Use a known timestamp
        timestamp = 1609459200.0  # Will vary by timezone
        record = LogRecord(name="test", level=INFO, msg="Test", timestamp=timestamp)
        
        # Should match format: YYYY-MM-DD HH:MM:SS
        import re
        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        assert re.match(pattern, record.formatted_time)

    def test_formatted_time_matches_datetime(self):
        """Test formatted_time matches datetime strftime"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        expected = record.datetime.strftime("%Y-%m-%d %H:%M:%S")
        assert record.formatted_time == expected


class TestMessageProperty:
    """Test LogRecord.message property"""

    def test_message_without_args(self):
        """Test message property with no args returns msg as-is"""
        record = LogRecord(name="test", level=INFO, msg="Simple message")
        
        assert record.message == "Simple message"

    def test_message_with_string_formatting(self):
        """Test message property with % string formatting"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Hello %s, you have %d messages",
            args=("John", 5)
        )
        
        assert record.message == "Hello John, you have 5 messages"

    def test_message_with_single_arg(self):
        """Test message with single argument"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="User: %s",
            args=("admin",)
        )
        
        assert record.message == "User: admin"

    def test_message_formatting_error_returns_original(self):
        """Test that formatting errors return original message"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Invalid %d format",
            args=("not_a_number",)  # Wrong type for %d
        )
        
        # Should return original msg when formatting fails
        assert record.message == "Invalid %d format"

    def test_message_with_empty_args(self):
        """Test message with empty args tuple"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Message with %s placeholder",
            args=()
        )
        
        # Empty args should return original message
        assert record.message == "Message with %s placeholder"


class TestToDict:
    """Test LogRecord.to_dict() method"""

    def test_to_dict_returns_dict(self):
        """Test that to_dict returns a dictionary"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = record.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_basic_fields(self):
        """Test that to_dict contains all basic fields"""
        record = LogRecord(name="mylogger", level=WARNING, msg="Warning message")
        
        result = record.to_dict()
        
        assert result["name"] == "mylogger"
        assert result["level"] == WARNING
        assert result["level_name"] == "WARNING"
        assert result["message"] == "Warning message"

    def test_to_dict_contains_time_fields(self):
        """Test that to_dict contains time-related fields"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = record.to_dict()
        
        assert "timestamp" in result
        assert "formatted_time" in result
        assert isinstance(result["timestamp"], float)
        assert isinstance(result["formatted_time"], str)

    def test_to_dict_contains_location_fields(self):
        """Test that to_dict contains source location fields"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="test.py",
            lineno=42,
            func_name="test_func"
        )
        
        result = record.to_dict()
        
        assert result["filename"] == "test.py"
        assert result["lineno"] == 42
        assert result["func_name"] == "test_func"

    def test_to_dict_contains_thread_and_process(self):
        """Test that to_dict contains thread and process info"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = record.to_dict()
        
        assert "thread_id" in result
        assert "thread_name" in result
        assert "process_id" in result

    def test_to_dict_contains_extra(self):
        """Test that to_dict contains extra data"""
        extra = {"custom_field": "custom_value"}
        record = LogRecord(name="test", level=INFO, msg="Test", extra=extra)
        
        result = record.to_dict()
        
        assert result["extra"] == extra

    def test_to_dict_includes_kwargs(self):
        """Test that to_dict includes kwargs at top level"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            kwargs={"user_id": 123, "action": "test"}
        )
        
        result = record.to_dict()
        
        # kwargs should be merged into the dict
        assert result["user_id"] == 123
        assert result["action"] == "test"

    def test_to_dict_formatted_message(self):
        """Test that to_dict contains formatted message"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Count: %d",
            args=(42,)
        )
        
        result = record.to_dict()
        
        assert result["message"] == "Count: 42"


class TestFindCaller:
    """Test LogRecord._find_caller() method"""

    def test_auto_find_caller_when_no_location(self):
        """Test that caller info is found automatically when not provided"""
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        # Should have attempted to find caller
        # Note: actual values depend on call stack
        assert isinstance(record.filename, str)
        assert isinstance(record.lineno, int)
        assert isinstance(record.func_name, str)

    def test_no_auto_find_when_location_provided(self):
        """Test that _find_caller is not called when location is provided"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="provided.py",
            lineno=100
        )
        
        # Should keep provided values
        assert record.filename == "provided.py"
        assert record.lineno == 100

    def test_find_caller_with_filename_only(self):
        """Test behavior when only filename is provided"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="test.py"
        )
        
        # lineno is 0, so _find_caller should NOT be called
        # (condition is: not self.filename AND not self.lineno)
        assert record.filename == "test.py"

    def test_find_caller_with_lineno_only(self):
        """Test behavior when only lineno is provided"""
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            lineno=50
        )
        
        # filename is empty but lineno is set, so _find_caller should NOT be called
        assert record.lineno == 50


class TestLogRecordInDifferentThread:
    """Test LogRecord captures correct thread info"""

    def test_record_in_different_thread(self):
        """Test that record captures the creating thread's info"""
        result = {}
        
        def create_record():
            record = LogRecord(name="test", level=INFO, msg="From thread")
            result["thread_id"] = record.thread_id
            result["thread_name"] = record.thread_name
            result["current_thread_id"] = threading.current_thread().ident
            result["current_thread_name"] = threading.current_thread().name
        
        thread = threading.Thread(target=create_record, name="TestThread")
        thread.start()
        thread.join()
        
        assert result["thread_id"] == result["current_thread_id"]
        assert result["thread_name"] == result["current_thread_name"]
        assert result["thread_name"] == "TestThread"


class TestLogRecordExceptionInfo:
    """Test LogRecord with exception info"""

    def test_with_exception_info(self):
        """Test creating record with exception info"""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            record = LogRecord(
                name="test",
                level=ERROR,
                msg="Error occurred",
                exception_info=exc_info
            )
            
            assert record.exception_info is not None
            assert record.exception_info[0] is ValueError
            assert str(record.exception_info[1]) == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
