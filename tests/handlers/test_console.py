"""
Tests for logify.handlers.console module

Tests for ConsoleHandler class
"""

import io
import sys
import pytest

from logify.handlers.console import ConsoleHandler
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logify.core.record import LogRecord
from logify.formatters.text import TextFormatter
from logify.formatters.color import ColorFormatter


class TestConsoleHandlerInit:
    """Test ConsoleHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = ConsoleHandler()
        assert handler.stream is sys.stdout
        assert handler.level == DEBUG
        assert isinstance(handler.formatter, ColorFormatter)
        assert handler._use_stderr_for_errors is True
    
    def test_custom_stream(self):
        """Test initialization with custom stream"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        assert handler.stream is stream
    
    def test_custom_level(self):
        """Test initialization with custom level"""
        handler = ConsoleHandler(level=LogLevel.WARNING)
        assert handler.level == WARNING
    
    def test_custom_formatter(self):
        """Test initialization with custom formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = ConsoleHandler(formatter=formatter)
        assert handler.formatter is formatter
        assert isinstance(handler.formatter, TextFormatter)
    
    def test_use_stderr_for_errors_disabled(self):
        """Test initialization with use_stderr_for_errors disabled"""
        handler = ConsoleHandler(use_stderr_for_errors=False)
        assert handler._use_stderr_for_errors is False
    
    def test_custom_name(self):
        """Test initialization with custom name"""
        handler = ConsoleHandler(name="MyConsoleHandler")
        assert handler.name == "MyConsoleHandler"


class TestConsoleHandlerStream:
    """Test ConsoleHandler stream property"""
    
    def test_stream_getter(self):
        """Test stream property getter"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        assert handler.stream is stream
    
    def test_stream_setter(self):
        """Test stream property setter"""
        handler = ConsoleHandler()
        new_stream = io.StringIO()
        handler.stream = new_stream
        assert handler.stream is new_stream


class TestConsoleHandlerGetStream:
    """Test ConsoleHandler _get_stream method"""
    
    def test_get_stream_for_info(self):
        """Test _get_stream returns stdout for INFO level"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=True)
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        assert handler._get_stream(record) is stream
    
    def test_get_stream_for_warning(self):
        """Test _get_stream returns stdout for WARNING level"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=True)
        record = LogRecord(name="test", level=WARNING, msg="Test", filename="test.py", lineno=1)
        assert handler._get_stream(record) is stream
    
    def test_get_stream_for_error(self):
        """Test _get_stream returns stderr for ERROR level"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=True)
        record = LogRecord(name="test", level=ERROR, msg="Test", filename="test.py", lineno=1)
        assert handler._get_stream(record) is sys.stderr
    
    def test_get_stream_for_critical(self):
        """Test _get_stream returns stderr for CRITICAL level"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=True)
        record = LogRecord(name="test", level=CRITICAL, msg="Test", filename="test.py", lineno=1)
        assert handler._get_stream(record) is sys.stderr
    
    def test_get_stream_error_to_stdout(self):
        """Test _get_stream returns stdout for ERROR when use_stderr_for_errors is False"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=False)
        record = LogRecord(name="test", level=ERROR, msg="Test", filename="test.py", lineno=1)
        assert handler._get_stream(record) is stream


class TestConsoleHandlerEmit:
    """Test ConsoleHandler emit method"""
    
    def test_emit_writes_to_stream(self):
        """Test emit writes formatted message to stream"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter)
        record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
        
        handler.emit(record)
        
        output = stream.getvalue()
        assert "Test message" in output
        assert output.endswith('\n')
    
    def test_emit_multiple_records(self):
        """Test emit writes multiple records"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter)
        
        for i in range(3):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            handler.emit(record)
        
        output = stream.getvalue()
        assert "Message 0" in output
        assert "Message 1" in output
        assert "Message 2" in output
    
    def test_emit_with_args(self):
        """Test emit with message arguments"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter)
        record = LogRecord(
            name="test", level=INFO, msg="Hello %s", 
            args=("World",), filename="test.py", lineno=1
        )
        
        handler.emit(record)
        
        output = stream.getvalue()
        assert "Hello World" in output


class TestConsoleHandlerFlush:
    """Test ConsoleHandler flush method"""
    
    def test_flush_without_errors(self):
        """Test flush method does not raise"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        handler.flush()  # Should not raise
    
    def test_flush_with_stderr_enabled(self):
        """Test flush method flushes stderr when enabled"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, use_stderr_for_errors=True)
        handler.flush()  # Should not raise


class TestConsoleHandlerRepr:
    """Test ConsoleHandler __repr__ method"""
    
    def test_repr_with_stdout(self):
        """Test __repr__ with stdout"""
        handler = ConsoleHandler()
        repr_str = repr(handler)
        assert "ConsoleHandler" in repr_str
        assert "stream=" in repr_str
    
    def test_repr_with_custom_stream(self):
        """Test __repr__ with custom stream"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        repr_str = repr(handler)
        assert "ConsoleHandler" in repr_str


class TestConsoleHandlerHandle:
    """Test ConsoleHandler handle method (inherited from BaseHandler)"""
    
    def test_handle_filters_by_level(self):
        """Test handle filters by handler level"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter, level=WARNING)
        
        record_info = LogRecord(name="test", level=INFO, msg="Info message", filename="test.py", lineno=1)
        record_warning = LogRecord(name="test", level=WARNING, msg="Warning message", filename="test.py", lineno=1)
        
        handler.handle(record_info)
        handler.handle(record_warning)
        
        output = stream.getvalue()
        assert "Info message" not in output
        assert "Warning message" in output
    
    def test_handle_when_closed(self):
        """Test handle returns False when handler is closed"""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        handler.close()
        
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        
        assert result is False


class TestConsoleHandlerWithColorFormatter:
    """Test ConsoleHandler with ColorFormatter"""
    
    def test_default_uses_color_formatter(self):
        """Test default handler uses ColorFormatter"""
        handler = ConsoleHandler()
        assert isinstance(handler.formatter, ColorFormatter)
    
    def test_color_output(self):
        """Test colored output is produced"""
        stream = io.StringIO()
        formatter = ColorFormatter(force_colors=True)
        # Disable stderr redirect for ERROR to test stream output
        handler = ConsoleHandler(stream=stream, formatter=formatter, use_stderr_for_errors=False)
        
        record = LogRecord(name="test", level=ERROR, msg="Error message", filename="test.py", lineno=1)
        handler.emit(record)
        
        output = stream.getvalue()
        # ColorFormatter adds ANSI codes
        assert "Error message" in output


class TestConsoleHandlerLevelOutput:
    """Test ConsoleHandler with different log levels"""
    
    def test_debug_output(self):
        """Test DEBUG level output"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter, level=DEBUG)
        
        record = LogRecord(name="test", level=DEBUG, msg="Debug message", filename="test.py", lineno=1)
        handler.handle(record)
        
        output = stream.getvalue()
        assert "DEBUG" in output
        assert "Debug message" in output
    
    def test_info_output(self):
        """Test INFO level output"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter)
        
        record = LogRecord(name="test", level=INFO, msg="Info message", filename="test.py", lineno=1)
        handler.handle(record)
        
        output = stream.getvalue()
        assert "INFO" in output
        assert "Info message" in output
    
    def test_warning_output(self):
        """Test WARNING level output"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter)
        
        record = LogRecord(name="test", level=WARNING, msg="Warning message", filename="test.py", lineno=1)
        handler.handle(record)
        
        output = stream.getvalue()
        assert "WARNING" in output
        assert "Warning message" in output
    
    def test_error_output(self):
        """Test ERROR level output"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter, use_stderr_for_errors=False)
        
        record = LogRecord(name="test", level=ERROR, msg="Error message", filename="test.py", lineno=1)
        handler.handle(record)
        
        output = stream.getvalue()
        assert "ERROR" in output
        assert "Error message" in output
    
    def test_critical_output(self):
        """Test CRITICAL level output"""
        stream = io.StringIO()
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        handler = ConsoleHandler(stream=stream, formatter=formatter, use_stderr_for_errors=False)
        
        record = LogRecord(name="test", level=CRITICAL, msg="Critical message", filename="test.py", lineno=1)
        handler.handle(record)
        
        output = stream.getvalue()
        assert "CRITICAL" in output
        assert "Critical message" in output
