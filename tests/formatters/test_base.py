"""
Test cases for logify.formatters.base module
"""

import pytest
import sys
from logify.formatters.base import BaseFormatter
from logify.core.record import LogRecord
from logify.core.levels import INFO, ERROR


class ConcreteFormatter(BaseFormatter):
    """Concrete implementation of BaseFormatter for testing"""
    
    def format(self, record: LogRecord) -> str:
        return f"{record.level_name}: {record.message}"


class TestBaseFormatterInit:
    """Test BaseFormatter initialization"""

    def test_default_name_is_class_name(self):
        """Test that default name is the class name"""
        formatter = ConcreteFormatter()
        assert formatter.name == "ConcreteFormatter"

    def test_custom_name(self):
        """Test providing a custom name"""
        formatter = ConcreteFormatter(name="MyFormatter")
        assert formatter.name == "MyFormatter"

    def test_empty_name_uses_class_name(self):
        """Test that empty string name uses class name"""
        formatter = ConcreteFormatter(name="")
        assert formatter.name == "ConcreteFormatter"


class TestBaseFormatterFormat:
    """Test BaseFormatter.format() method"""

    def test_format_method_works(self):
        """Test that concrete format method is called"""
        formatter = ConcreteFormatter()
        record = LogRecord(name="test", level=INFO, msg="Hello world")
        
        result = formatter.format(record)
        
        assert result == "INFO: Hello world"

    def test_format_with_different_levels(self):
        """Test format with different log levels"""
        formatter = ConcreteFormatter()
        
        record_info = LogRecord(name="test", level=INFO, msg="Info message")
        record_error = LogRecord(name="test", level=ERROR, msg="Error message")
        
        assert formatter.format(record_info) == "INFO: Info message"
        assert formatter.format(record_error) == "ERROR: Error message"


class TestBaseFormatterFormatException:
    """Test BaseFormatter.format_exception() method"""

    def test_format_exception_with_no_exception(self):
        """Test format_exception returns empty string when no exception"""
        formatter = ConcreteFormatter()
        record = LogRecord(name="test", level=ERROR, msg="Error")
        
        result = formatter.format_exception(record)
        
        assert result == ""

    def test_format_exception_with_none_values(self):
        """Test format_exception with None exception info"""
        formatter = ConcreteFormatter()
        record = LogRecord(
            name="test",
            level=ERROR,
            msg="Error",
            exception_info=(None, None, None)
        )
        
        result = formatter.format_exception(record)
        
        assert result == ""

    def test_format_exception_with_real_exception(self):
        """Test format_exception with actual exception"""
        formatter = ConcreteFormatter()
        
        try:
            raise ValueError("Test error message")
        except ValueError:
            exc_info = sys.exc_info()
            record = LogRecord(
                name="test",
                level=ERROR,
                msg="An error occurred",
                exception_info=exc_info
            )
            
            result = formatter.format_exception(record)
            
            assert "ValueError" in result
            assert "Test error message" in result
            assert "Traceback" in result

    def test_format_exception_includes_traceback(self):
        """Test that format_exception includes full traceback"""
        formatter = ConcreteFormatter()
        
        def inner_function():
            raise RuntimeError("Inner error")
        
        def outer_function():
            inner_function()
        
        try:
            outer_function()
        except RuntimeError:
            exc_info = sys.exc_info()
            record = LogRecord(
                name="test",
                level=ERROR,
                msg="Error",
                exception_info=exc_info
            )
            
            result = formatter.format_exception(record)
            
            assert "inner_function" in result
            assert "outer_function" in result
            assert "RuntimeError" in result


class TestBaseFormatterRepr:
    """Test BaseFormatter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        formatter = ConcreteFormatter()
        repr_str = repr(formatter)
        
        assert "ConcreteFormatter" in repr_str

    def test_repr_contains_name(self):
        """Test that repr contains formatter name"""
        formatter = ConcreteFormatter(name="MyFormatter")
        repr_str = repr(formatter)
        
        assert "MyFormatter" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
