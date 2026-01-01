"""
Test cases for logify.formatters.text module
"""

import pytest
import sys
from datetime import datetime
from logify.formatters.text import TextFormatter, DEFAULT_FORMAT, DEFAULT_DATE_FORMAT
from logify.core.record import LogRecord
from logify.core.levels import DEBUG, INFO, WARNING, ERROR, CRITICAL


class TestTextFormatterInit:
    """Test TextFormatter initialization"""

    def test_default_format(self):
        """Test default format string"""
        formatter = TextFormatter()
        assert formatter.format_string == DEFAULT_FORMAT

    def test_default_date_format(self):
        """Test default date format"""
        formatter = TextFormatter()
        assert formatter.date_format == DEFAULT_DATE_FORMAT

    def test_custom_format(self):
        """Test custom format string"""
        custom_fmt = "%(levelname)s - %(message)s"
        formatter = TextFormatter(fmt=custom_fmt)
        assert formatter.format_string == custom_fmt

    def test_custom_date_format(self):
        """Test custom date format"""
        custom_datefmt = "%H:%M:%S"
        formatter = TextFormatter(datefmt=custom_datefmt)
        assert formatter.date_format == custom_datefmt

    def test_custom_name(self):
        """Test custom formatter name"""
        formatter = TextFormatter(name="MyTextFormatter")
        assert formatter.name == "MyTextFormatter"


class TestTextFormatterProperties:
    """Test TextFormatter properties"""

    def test_format_string_property(self):
        """Test format_string property"""
        fmt = "%(name)s: %(message)s"
        formatter = TextFormatter(fmt=fmt)
        assert formatter.format_string == fmt

    def test_date_format_property(self):
        """Test date_format property"""
        datefmt = "%Y/%m/%d"
        formatter = TextFormatter(datefmt=datefmt)
        assert formatter.date_format == datefmt


class TestTextFormatterFormatTime:
    """Test TextFormatter.format_time() method"""

    def test_format_time_default(self):
        """Test format_time with default format"""
        formatter = TextFormatter()
        timestamp = 1609459200.0  # Known timestamp
        record = LogRecord(name="test", level=INFO, msg="Test", timestamp=timestamp)
        
        result = formatter.format_time(record)
        
        # Should match the default date format pattern
        expected = datetime.fromtimestamp(timestamp).strftime(DEFAULT_DATE_FORMAT)
        assert result == expected

    def test_format_time_custom_format(self):
        """Test format_time with custom format"""
        formatter = TextFormatter(datefmt="%H:%M:%S")
        timestamp = 1609459200.0
        record = LogRecord(name="test", level=INFO, msg="Test", timestamp=timestamp)
        
        result = formatter.format_time(record)
        
        expected = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        assert result == expected


class TestTextFormatterFormat:
    """Test TextFormatter.format() method"""

    def test_format_basic(self):
        """Test basic formatting"""
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Hello world")
        
        result = formatter.format(record)
        
        assert result == "INFO: Hello world"

    def test_format_with_name(self):
        """Test formatting with logger name"""
        formatter = TextFormatter(fmt="[%(name)s] %(message)s")
        record = LogRecord(name="myapp.module", level=INFO, msg="Test message")
        
        result = formatter.format(record)
        
        assert result == "[myapp.module] Test message"

    def test_format_with_all_placeholders(self):
        """Test formatting with multiple placeholders"""
        formatter = TextFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M"
        )
        record = LogRecord(
            name="test",
            level=WARNING,
            msg="Warning message",
            timestamp=1609459200.0
        )
        
        result = formatter.format(record)
        
        assert "test" in result
        assert "WARNING" in result
        assert "Warning message" in result

    def test_format_with_filename_and_lineno(self):
        """Test formatting with filename and line number"""
        formatter = TextFormatter(fmt="%(filename)s:%(lineno)d - %(message)s")
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="test_file.py",
            lineno=42
        )
        
        result = formatter.format(record)
        
        assert "test_file.py:42 - Test" == result

    def test_format_with_function_name(self):
        """Test formatting with function name"""
        formatter = TextFormatter(fmt="%(funcName)s: %(message)s")
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Test",
            filename="test.py",
            lineno=1,
            func_name="my_function"
        )
        
        result = formatter.format(record)
        
        assert result == "my_function: Test"

    def test_format_with_thread_info(self):
        """Test formatting with thread information"""
        formatter = TextFormatter(fmt="[%(threadName)s] %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        
        assert "[" in result
        assert "] Test" in result

    def test_format_with_process_info(self):
        """Test formatting with process information"""
        formatter = TextFormatter(fmt="[%(process)d] %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        
        # Should contain process ID in brackets
        assert "[" in result
        assert "] Test" in result

    def test_format_with_level_number(self):
        """Test formatting with level number"""
        formatter = TextFormatter(fmt="%(levelno)d: %(message)s")
        record = LogRecord(name="test", level=WARNING, msg="Test")
        
        result = formatter.format(record)
        
        assert result == "30: Test"

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields"""
        formatter = TextFormatter(fmt="%(message)s [user=%(user_id)s]")
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Login",
            extra={"user_id": "12345"}
        )
        
        result = formatter.format(record)
        
        assert result == "Login [user=12345]"

    def test_format_with_kwargs(self):
        """Test formatting with kwargs fields"""
        formatter = TextFormatter(fmt="%(message)s - request_id=%(request_id)s")
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Request received",
            kwargs={"request_id": "abc-123"}
        )
        
        result = formatter.format(record)
        
        assert result == "Request received - request_id=abc-123"

    def test_format_fallback_on_error(self):
        """Test that formatting falls back on error"""
        formatter = TextFormatter(fmt="%(invalid_field)s: %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Test message")
        
        # Should not raise, but fall back to basic format
        result = formatter.format(record)
        
        assert "test" in result
        assert "INFO" in result
        assert "Test message" in result


class TestTextFormatterWithException:
    """Test TextFormatter with exception info"""

    def test_format_with_exception(self):
        """Test formatting includes exception info"""
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        
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
        
        assert "ERROR: An error occurred" in result
        assert "ValueError" in result
        assert "Test error" in result

    def test_format_without_exception(self):
        """Test formatting without exception info"""
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Normal message")
        
        result = formatter.format(record)
        
        assert result == "INFO: Normal message"
        assert "Traceback" not in result


class TestTextFormatterRepr:
    """Test TextFormatter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        formatter = TextFormatter()
        repr_str = repr(formatter)
        
        assert "TextFormatter" in repr_str

    def test_repr_contains_format(self):
        """Test that repr contains format string"""
        fmt = "%(message)s"
        formatter = TextFormatter(fmt=fmt)
        repr_str = repr(formatter)
        
        assert "fmt=" in repr_str


class TestTextFormatterAllLevels:
    """Test TextFormatter with all log levels"""

    def test_format_all_levels(self):
        """Test formatting works for all log levels"""
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        
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
            assert result == f"{expected_name}: Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
