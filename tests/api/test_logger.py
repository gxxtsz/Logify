"""
Tests for logify.api.logger module

Tests for Logger class functionality
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

from logify.api.logger import Logger
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logify.core.record import LogRecord
from logify.handlers.base import BaseHandler
from logify.filters.base import BaseFilter


class MockHandler(BaseHandler):
    """Mock handler for testing"""
    
    def __init__(self, level=LogLevel.DEBUG):
        super().__init__(level=level)
        self.records = []
    
    def emit(self, record):
        self.records.append(record)
    
    def clear(self):
        self.records.clear()


class MockFilter(BaseFilter):
    """Mock filter for testing"""
    
    def __init__(self, should_pass=True):
        super().__init__()
        self.should_pass = should_pass
        self.filtered_records = []
    
    def filter(self, record):
        self.filtered_records.append(record)
        return self.should_pass


class TestLoggerInit:
    """Tests for Logger initialization"""
    
    def test_default_init(self):
        """Test default initialization"""
        logger = Logger()
        assert logger.name == "root"
        assert logger.level == LogLevel.DEBUG.value
        assert logger._manager is None
        assert logger.parent is None
        assert logger.propagate is True
        assert logger.disabled is False
    
    def test_init_with_name(self):
        """Test initialization with name"""
        logger = Logger(name="myapp")
        assert logger.name == "myapp"
    
    def test_init_with_level_enum(self):
        """Test initialization with LogLevel enum"""
        logger = Logger(level=LogLevel.INFO)
        assert logger.level == LogLevel.INFO.value
    
    def test_init_with_level_int(self):
        """Test initialization with integer level"""
        logger = Logger(level=30)
        assert logger.level == 30
    
    def test_init_with_manager(self):
        """Test initialization with manager"""
        mock_manager = Mock()
        logger = Logger(name="test", manager=mock_manager)
        assert logger._manager is mock_manager


class TestLoggerProperties:
    """Tests for Logger properties"""
    
    @pytest.fixture
    def logger(self):
        return Logger(name="test", level=LogLevel.INFO)
    
    def test_name_property(self, logger):
        """Test name property"""
        assert logger.name == "test"
    
    def test_level_property(self, logger):
        """Test level property getter"""
        assert logger.level == LogLevel.INFO.value
    
    def test_level_setter_with_enum(self, logger):
        """Test level setter with LogLevel enum"""
        logger.level = LogLevel.ERROR
        assert logger.level == LogLevel.ERROR.value
    
    def test_level_setter_with_int(self, logger):
        """Test level setter with integer"""
        logger.level = 50
        assert logger.level == 50
    
    def test_parent_property(self, logger):
        """Test parent property"""
        parent = Logger(name="parent")
        logger.parent = parent
        assert logger.parent is parent
    
    def test_propagate_property(self, logger):
        """Test propagate property"""
        assert logger.propagate is True
        logger.propagate = False
        assert logger.propagate is False
    
    def test_disabled_property(self, logger):
        """Test disabled property"""
        assert logger.disabled is False
        logger.disabled = True
        assert logger.disabled is True
    
    def test_handlers_property(self, logger):
        """Test handlers property"""
        handler = MockHandler()
        logger.add_handler(handler)
        assert handler in logger.handlers


class TestHandlerManagement:
    """Tests for handler management"""
    
    @pytest.fixture
    def logger(self):
        return Logger(name="test")
    
    def test_add_handler(self, logger):
        """Test adding handler"""
        handler = MockHandler()
        result = logger.add_handler(handler)
        assert result is logger  # Chain support
        assert handler in logger.handlers
    
    def test_add_multiple_handlers(self, logger):
        """Test adding multiple handlers"""
        handler1 = MockHandler()
        handler2 = MockHandler()
        logger.add_handler(handler1).add_handler(handler2)
        assert len(logger.handlers) == 2
    
    def test_remove_handler(self, logger):
        """Test removing handler"""
        handler = MockHandler()
        logger.add_handler(handler)
        result = logger.remove_handler(handler)
        assert result is logger  # Chain support
        assert handler not in logger.handlers
    
    def test_remove_nonexistent_handler(self, logger):
        """Test removing nonexistent handler"""
        handler = MockHandler()
        # Should not raise
        logger.remove_handler(handler)


class TestFilterManagement:
    """Tests for filter management"""
    
    @pytest.fixture
    def logger(self):
        return Logger(name="test")
    
    def test_add_filter(self, logger):
        """Test adding filter"""
        filter_ = MockFilter()
        result = logger.add_filter(filter_)
        assert result is logger  # Chain support
    
    def test_add_multiple_filters(self, logger):
        """Test adding multiple filters"""
        filter1 = MockFilter()
        filter2 = MockFilter()
        logger.add_filter(filter1).add_filter(filter2)
    
    def test_remove_filter(self, logger):
        """Test removing filter"""
        filter_ = MockFilter()
        logger.add_filter(filter_)
        result = logger.remove_filter(filter_)
        assert result is logger  # Chain support


class TestExtraContext:
    """Tests for extra context management"""
    
    @pytest.fixture
    def logger(self):
        return Logger(name="test")
    
    def test_set_extra(self, logger):
        """Test setting extra context"""
        result = logger.set_extra(user_id="123", request_id="abc")
        assert result is logger  # Chain support
        assert logger._extra == {"user_id": "123", "request_id": "abc"}
    
    def test_set_extra_updates_existing(self, logger):
        """Test that set_extra updates existing values"""
        logger.set_extra(key1="value1")
        logger.set_extra(key1="new_value", key2="value2")
        assert logger._extra == {"key1": "new_value", "key2": "value2"}
    
    def test_clear_extra(self, logger):
        """Test clearing extra context"""
        logger.set_extra(key="value")
        result = logger.clear_extra()
        assert result is logger  # Chain support
        assert logger._extra == {}


class TestIsEnabledFor:
    """Tests for is_enabled_for method"""
    
    def test_enabled_when_level_higher(self):
        """Test enabled when record level is higher than logger level"""
        logger = Logger(level=LogLevel.DEBUG)
        assert logger.is_enabled_for(LogLevel.INFO) is True
        assert logger.is_enabled_for(LogLevel.ERROR) is True
    
    def test_enabled_when_level_equal(self):
        """Test enabled when record level equals logger level"""
        logger = Logger(level=LogLevel.INFO)
        assert logger.is_enabled_for(LogLevel.INFO) is True
    
    def test_disabled_when_level_lower(self):
        """Test disabled when record level is lower than logger level"""
        logger = Logger(level=LogLevel.WARNING)
        assert logger.is_enabled_for(LogLevel.DEBUG) is False
        assert logger.is_enabled_for(LogLevel.INFO) is False
    
    def test_disabled_when_logger_disabled(self):
        """Test disabled when logger is disabled"""
        logger = Logger(level=LogLevel.DEBUG)
        logger.disabled = True
        assert logger.is_enabled_for(LogLevel.CRITICAL) is False
    
    def test_enabled_with_int_level(self):
        """Test enabled with integer level"""
        logger = Logger(level=10)
        assert logger.is_enabled_for(20) is True


class TestLoggingMethods:
    """Tests for logging methods (debug, info, warning, error, critical)"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler  # For easy access in tests
        return logger
    
    def test_debug(self, logger):
        """Test debug logging"""
        logger.debug("Debug message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].msg == "Debug message"
        assert logger._handler.records[0].level == LogLevel.DEBUG
    
    def test_info(self, logger):
        """Test info logging"""
        logger.info("Info message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].msg == "Info message"
        assert logger._handler.records[0].level == LogLevel.INFO
    
    def test_warning(self, logger):
        """Test warning logging"""
        logger.warning("Warning message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].msg == "Warning message"
        assert logger._handler.records[0].level == LogLevel.WARNING
    
    def test_warn_alias(self, logger):
        """Test warn is alias for warning"""
        logger.warn("Warn message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].level == LogLevel.WARNING
    
    def test_error(self, logger):
        """Test error logging"""
        logger.error("Error message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].msg == "Error message"
        assert logger._handler.records[0].level == LogLevel.ERROR
    
    def test_critical(self, logger):
        """Test critical logging"""
        logger.critical("Critical message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].msg == "Critical message"
        assert logger._handler.records[0].level == LogLevel.CRITICAL
    
    def test_fatal_alias(self, logger):
        """Test fatal is alias for critical"""
        logger.fatal("Fatal message")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].level == LogLevel.CRITICAL
    
    def test_log_with_args(self, logger):
        """Test logging with format args"""
        logger.info("Message %s %d", "test", 42)
        record = logger._handler.records[0]
        assert record.msg == "Message %s %d"
        assert record.args == ("test", 42)
    
    def test_log_with_extra(self, logger):
        """Test logging with extra data"""
        logger.info("Test message", extra={"key": "value"})
        record = logger._handler.records[0]
        assert record.extra.get("key") == "value"
    
    def test_log_level_filtering(self, logger):
        """Test that logs below level are filtered"""
        logger.level = LogLevel.ERROR
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        assert len(logger._handler.records) == 1
        assert logger._handler.records[0].level == LogLevel.ERROR


class TestExceptionLogging:
    """Tests for exception logging"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler
        return logger
    
    def test_exception_method(self, logger):
        """Test exception logging method"""
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")
        
        assert len(logger._handler.records) == 1
        record = logger._handler.records[0]
        assert record.level == LogLevel.ERROR
        assert record.exception_info is not None
    
    def test_exc_info_true(self, logger):
        """Test logging with exc_info=True"""
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error("Error", exc_info=True)
        
        record = logger._handler.records[0]
        assert record.exception_info is not None
    
    def test_exc_info_tuple(self, logger):
        """Test logging with exc_info as tuple"""
        exc_info = (ValueError, ValueError("Test"), None)
        logger.error("Error", exc_info=exc_info)
        record = logger._handler.records[0]
        assert record.exception_info == exc_info


class TestLogMethod:
    """Tests for generic log method"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler
        return logger
    
    def test_log_with_level_enum(self, logger):
        """Test log with LogLevel enum"""
        logger.log(LogLevel.WARNING, "Warning message")
        assert logger._handler.records[0].level == LogLevel.WARNING
    
    def test_log_with_level_int(self, logger):
        """Test log with integer level"""
        logger.log(30, "Warning message")
        assert logger._handler.records[0].level == LogLevel.WARNING
    
    def test_log_with_unknown_int_level(self, logger):
        """Test log with unknown integer level defaults to DEBUG"""
        logger.log(15, "Unknown level")
        assert logger._handler.records[0].level == LogLevel.DEBUG


class TestContextManager:
    """Tests for context manager"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler
        return logger
    
    def test_context_adds_extra(self, logger):
        """Test context manager adds extra data"""
        with logger.context(request_id="123"):
            logger.info("Inside context")
        
        record = logger._handler.records[0]
        assert record.extra.get("request_id") == "123"
    
    def test_context_restores_extra_after(self, logger):
        """Test context manager restores extra after exit"""
        logger.set_extra(permanent="value")
        
        with logger.context(temporary="temp"):
            assert "temporary" in logger._extra
        
        assert "temporary" not in logger._extra
        assert logger._extra.get("permanent") == "value"
    
    def test_context_yields_logger(self, logger):
        """Test context manager yields logger"""
        with logger.context(key="value") as ctx_logger:
            assert ctx_logger is logger
    
    def test_context_restores_on_exception(self, logger):
        """Test context manager restores extra even on exception"""
        logger.set_extra(original="value")
        
        try:
            with logger.context(temporary="temp"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert "temporary" not in logger._extra
        assert logger._extra.get("original") == "value"
    
    def test_nested_context(self, logger):
        """Test nested context managers"""
        with logger.context(level1="a"):
            with logger.context(level2="b"):
                logger.info("Nested")
                record = logger._handler.records[0]
                assert record.extra.get("level1") == "a"
                assert record.extra.get("level2") == "b"


class TestTraceDecorator:
    """Tests for trace decorator"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler
        return logger
    
    def test_trace_basic(self, logger):
        """Test basic trace decorator"""
        @logger.trace
        def my_function():
            return "result"
        
        result = my_function()
        assert result == "result"
        assert len(logger._handler.records) == 2
        assert "Entering my_function" in logger._handler.records[0].msg
        assert "Exiting my_function" in logger._handler.records[1].msg
    
    def test_trace_with_level(self, logger):
        """Test trace decorator with custom level"""
        @logger.trace(level=LogLevel.INFO)
        def my_function():
            pass
        
        my_function()
        assert logger._handler.records[0].level == LogLevel.INFO
    
    def test_trace_on_exception(self, logger):
        """Test trace decorator logs exception"""
        @logger.trace
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        assert len(logger._handler.records) == 2
        assert "Entering failing_function" in logger._handler.records[0].msg
        assert "Exception in failing_function" in logger._handler.records[1].msg
        assert logger._handler.records[1].level == LogLevel.ERROR
    
    def test_trace_preserves_function_name(self, logger):
        """Test trace decorator preserves function metadata"""
        @logger.trace
        def documented_function():
            """This is a docstring"""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a docstring"


class TestFilterChain:
    """Tests for filter chain integration"""
    
    @pytest.fixture
    def logger(self):
        logger = Logger(name="test", level=LogLevel.DEBUG)
        handler = MockHandler()
        logger.add_handler(handler)
        logger._handler = handler
        return logger
    
    def test_filter_blocks_record(self, logger):
        """Test filter can block record"""
        blocking_filter = MockFilter(should_pass=False)
        logger.add_filter(blocking_filter)
        
        logger.info("Should be blocked")
        assert len(logger._handler.records) == 0
        assert len(blocking_filter.filtered_records) == 1
    
    def test_filter_passes_record(self, logger):
        """Test filter can pass record"""
        passing_filter = MockFilter(should_pass=True)
        logger.add_filter(passing_filter)
        
        logger.info("Should pass")
        assert len(logger._handler.records) == 1
    
    def test_multiple_filters(self, logger):
        """Test multiple filters in chain"""
        filter1 = MockFilter(should_pass=True)
        filter2 = MockFilter(should_pass=True)
        logger.add_filter(filter1).add_filter(filter2)
        
        logger.info("Test")
        assert len(filter1.filtered_records) == 1
        assert len(filter2.filtered_records) == 1
    
    def test_filter_chain_short_circuit(self, logger):
        """Test filter chain stops on first failure"""
        filter1 = MockFilter(should_pass=False)
        filter2 = MockFilter(should_pass=True)
        logger.add_filter(filter1).add_filter(filter2)
        
        logger.info("Test")
        assert len(filter1.filtered_records) == 1
        assert len(filter2.filtered_records) == 0  # Not reached


class TestLogPropagation:
    """Tests for log propagation to parent"""
    
    def test_propagation_to_parent(self):
        """Test logs propagate to parent handler"""
        parent = Logger(name="parent")
        parent_handler = MockHandler()
        parent.add_handler(parent_handler)
        
        child = Logger(name="parent.child")
        child_handler = MockHandler()
        child.add_handler(child_handler)
        child.parent = parent
        
        child.info("Test message")
        
        assert len(child_handler.records) == 1
        assert len(parent_handler.records) == 1
    
    def test_propagation_disabled(self):
        """Test propagation can be disabled"""
        parent = Logger(name="parent")
        parent_handler = MockHandler()
        parent.add_handler(parent_handler)
        
        child = Logger(name="parent.child")
        child_handler = MockHandler()
        child.add_handler(child_handler)
        child.parent = parent
        child.propagate = False
        
        child.info("Test message")
        
        assert len(child_handler.records) == 1
        assert len(parent_handler.records) == 0
    
    def test_no_parent(self):
        """Test logging without parent"""
        logger = Logger(name="orphan")
        handler = MockHandler()
        logger.add_handler(handler)
        
        logger.info("Test")
        assert len(handler.records) == 1


class TestGetChild:
    """Tests for get_child method"""
    
    def test_get_child_without_manager(self):
        """Test get_child creates child without manager"""
        parent = Logger(name="parent", level=LogLevel.INFO)
        child = parent.get_child("child")
        
        assert child.name == "parent.child"
        assert child.level == LogLevel.INFO.value
        assert child.parent is parent
    
    def test_get_child_from_root(self):
        """Test get_child from root logger without manager"""
        root = Logger(name="root")
        child = root.get_child("mymodule")
        
        # Without manager, root prefix is kept
        assert child.name == "root.mymodule"
    
    def test_get_child_with_manager(self):
        """Test get_child with manager delegates to manager"""
        mock_manager = Mock()
        mock_child = Logger(name="parent.child")
        mock_manager.get_logger.return_value = mock_child
        
        parent = Logger(name="parent", manager=mock_manager)
        child = parent.get_child("child")
        
        mock_manager.get_logger.assert_called_with("parent.child")
        assert child is mock_child


class TestFlushAndClose:
    """Tests for flush and close methods"""
    
    def test_flush(self):
        """Test flush calls handler flush"""
        logger = Logger(name="test")
        handler = MockHandler()
        handler.flush = Mock()
        logger.add_handler(handler)
        
        logger.flush()
        handler.flush.assert_called_once()
    
    def test_close(self):
        """Test close calls handler close"""
        logger = Logger(name="test")
        handler = MockHandler()
        handler.close = Mock()
        logger.add_handler(handler)
        
        logger.close()
        handler.close.assert_called_once()


class TestRepr:
    """Tests for __repr__ method"""
    
    def test_repr_debug_level(self):
        """Test repr with DEBUG level"""
        logger = Logger(name="mylogger", level=LogLevel.DEBUG)
        assert repr(logger) == "<Logger(name='mylogger', level=DEBUG)>"
    
    def test_repr_info_level(self):
        """Test repr with INFO level"""
        logger = Logger(name="app", level=LogLevel.INFO)
        assert repr(logger) == "<Logger(name='app', level=INFO)>"
    
    def test_repr_custom_int_level(self):
        """Test repr with custom int level"""
        logger = Logger(name="test", level=25)
        assert "<Logger" in repr(logger)


class TestMakeRecord:
    """Tests for _make_record method"""
    
    @pytest.fixture
    def logger(self):
        return Logger(name="test")
    
    def test_make_record_basic(self, logger):
        """Test basic record creation"""
        record = logger._make_record(LogLevel.INFO, "Test", ())
        assert record.name == "test"
        assert record.level == LogLevel.INFO
        assert record.msg == "Test"
    
    def test_make_record_with_args(self, logger):
        """Test record creation with args"""
        record = logger._make_record(LogLevel.INFO, "Test %s", ("value",))
        assert record.args == ("value",)
    
    def test_make_record_with_exc_info(self, logger):
        """Test record creation with exception info"""
        exc_info = (ValueError, ValueError("error"), None)
        record = logger._make_record(LogLevel.ERROR, "Error", (), exc_info=exc_info)
        assert record.exception_info == exc_info
    
    def test_make_record_merges_extra(self, logger):
        """Test record creation merges logger extra with kwargs extra"""
        logger.set_extra(logger_key="logger_value")
        record = logger._make_record(
            LogLevel.INFO, "Test", (),
            extra={"record_key": "record_value"}
        )
        assert record.extra.get("logger_key") == "logger_value"
        assert record.extra.get("record_key") == "record_value"
    
    def test_make_record_extra_override(self, logger):
        """Test record extra can override logger extra"""
        logger.set_extra(key="old_value")
        record = logger._make_record(
            LogLevel.INFO, "Test", (),
            extra={"key": "new_value"}
        )
        assert record.extra.get("key") == "new_value"


class TestLoggerDisabled:
    """Tests for disabled logger behavior"""
    
    def test_disabled_logger_does_not_log(self):
        """Test disabled logger does not emit logs"""
        logger = Logger(name="test")
        handler = MockHandler()
        logger.add_handler(handler)
        logger.disabled = True
        
        logger.debug("Debug")
        logger.info("Info")
        logger.error("Error")
        logger.critical("Critical")
        
        assert len(handler.records) == 0
    
    def test_enable_logger(self):
        """Test re-enabling logger"""
        logger = Logger(name="test")
        handler = MockHandler()
        logger.add_handler(handler)
        
        logger.disabled = True
        logger.info("Should not log")
        
        logger.disabled = False
        logger.info("Should log")
        
        assert len(handler.records) == 1


class TestIntegration:
    """Integration tests for Logger"""
    
    def test_complete_logging_flow(self):
        """Test complete logging flow with multiple features"""
        # Setup
        logger = Logger(name="app", level=LogLevel.INFO)
        handler = MockHandler()
        filter_ = MockFilter(should_pass=True)
        
        logger.add_handler(handler).add_filter(filter_).set_extra(app="myapp")
        
        # Log
        with logger.context(request_id="req-123"):
            logger.info("Processing request")
            logger.warning("Something suspicious")
        
        # Verify
        assert len(handler.records) == 2
        for record in handler.records:
            assert record.extra.get("app") == "myapp"
            assert record.extra.get("request_id") == "req-123"
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy with propagation"""
        root = Logger(name="root")
        root_handler = MockHandler()
        root.add_handler(root_handler)
        
        app = Logger(name="app")
        app.parent = root
        
        module = Logger(name="app.module")
        module.parent = app
        module_handler = MockHandler()
        module.add_handler(module_handler)
        
        module.info("Module log")
        
        # Should be in both handlers
        assert len(module_handler.records) == 1
        assert len(root_handler.records) == 1
    
    def test_chain_api_style(self):
        """Test fluent chain API style"""
        handler = MockHandler()
        filter_ = MockFilter()
        
        logger = (Logger(name="test")
                 .add_handler(handler)
                 .add_filter(filter_)
                 .set_extra(key="value"))
        
        assert isinstance(logger, Logger)
        assert len(logger.handlers) == 1
