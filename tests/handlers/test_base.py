"""
Tests for logify.handlers.base module

Tests for BaseHandler and HandlerChain classes
"""

import threading
import pytest

from logify.handlers.base import BaseHandler, HandlerChain
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logify.core.record import LogRecord
from logify.formatters.text import TextFormatter
from logify.filters.level_filter import LevelFilter
from logify.filters.base import BaseFilter


# Concrete implementation for testing
class MockHandler(BaseHandler):
    """Mock handler for testing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records = []
        self.emit_error = False
    
    def emit(self, record: LogRecord) -> None:
        if self.emit_error:
            raise RuntimeError("Emit error")
        self.records.append(record)


class TestBaseHandlerInit:
    """Test BaseHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = MockHandler()
        assert handler.level == DEBUG
        assert handler.name == "MockHandler"
        assert isinstance(handler.formatter, TextFormatter)
        assert handler._closed is False
    
    def test_custom_level_with_enum(self):
        """Test initialization with LogLevel enum"""
        handler = MockHandler(level=LogLevel.WARNING)
        assert handler.level == WARNING
    
    def test_custom_level_with_int(self):
        """Test initialization with int level"""
        handler = MockHandler(level=30)
        assert handler.level == 30
    
    def test_custom_formatter(self):
        """Test initialization with custom formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = MockHandler(formatter=formatter)
        assert handler.formatter is formatter
    
    def test_custom_name(self):
        """Test initialization with custom name"""
        handler = MockHandler(name="MyHandler")
        assert handler.name == "MyHandler"


class TestBaseHandlerLevel:
    """Test BaseHandler level property"""
    
    def test_level_getter(self):
        """Test level property getter"""
        handler = MockHandler(level=LogLevel.INFO)
        assert handler.level == INFO
    
    def test_level_setter_with_enum(self):
        """Test level property setter with LogLevel enum"""
        handler = MockHandler()
        handler.level = LogLevel.ERROR
        assert handler.level == ERROR
    
    def test_level_setter_with_int(self):
        """Test level property setter with int"""
        handler = MockHandler()
        handler.level = 40
        assert handler.level == 40


class TestBaseHandlerFormatter:
    """Test BaseHandler formatter property"""
    
    def test_formatter_getter(self):
        """Test formatter property getter"""
        formatter = TextFormatter()
        handler = MockHandler(formatter=formatter)
        assert handler.formatter is formatter
    
    def test_formatter_setter(self):
        """Test formatter property setter"""
        handler = MockHandler()
        new_formatter = TextFormatter(fmt="%(message)s")
        handler.formatter = new_formatter
        assert handler.formatter is new_formatter


class TestBaseHandlerFilters:
    """Test BaseHandler filter methods"""
    
    def test_add_filter(self):
        """Test add_filter method"""
        handler = MockHandler()
        filter_ = LevelFilter(level=INFO)
        result = handler.add_filter(filter_)
        assert result is handler  # Returns self for chaining
    
    def test_add_filter_chain_call(self):
        """Test add_filter chain call"""
        handler = MockHandler()
        filter1 = LevelFilter(level=INFO)
        filter2 = LevelFilter(level=ERROR)
        handler.add_filter(filter1).add_filter(filter2)
        assert len(handler._filter_chain._filters) == 2
    
    def test_remove_filter(self):
        """Test remove_filter method"""
        handler = MockHandler()
        filter_ = LevelFilter(level=INFO)
        handler.add_filter(filter_)
        result = handler.remove_filter(filter_)
        assert result is handler  # Returns self for chaining
    
    def test_filter_passes(self):
        """Test filter method returns True when filter passes"""
        handler = MockHandler()
        handler.add_filter(LevelFilter(level=DEBUG))
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        assert handler.filter(record) is True
    
    def test_filter_blocks(self):
        """Test filter method returns False when filter blocks"""
        handler = MockHandler()
        handler.add_filter(LevelFilter(level=WARNING))
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        assert handler.filter(record) is False


class TestBaseHandlerFormat:
    """Test BaseHandler format method"""
    
    def test_format_uses_formatter(self):
        """Test format method uses the configured formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = MockHandler(formatter=formatter)
        record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
        result = handler.format(record)
        assert result == "Test message"


class TestBaseHandlerHandle:
    """Test BaseHandler handle method"""
    
    def test_handle_success(self):
        """Test handle method returns True on success"""
        handler = MockHandler(level=DEBUG)
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        assert result is True
        assert len(handler.records) == 1
    
    def test_handle_level_filter(self):
        """Test handle method filters by level"""
        handler = MockHandler(level=WARNING)
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        assert result is False
        assert len(handler.records) == 0
    
    def test_handle_custom_filter(self):
        """Test handle method uses custom filters"""
        handler = MockHandler()
        handler.add_filter(LevelFilter(level=WARNING))
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        assert result is False
        assert len(handler.records) == 0
    
    def test_handle_when_closed(self):
        """Test handle method returns False when closed"""
        handler = MockHandler()
        handler.close()
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        assert result is False
    
    def test_handle_emit_error(self):
        """Test handle method returns False on emit error"""
        handler = MockHandler()
        handler.emit_error = True
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        result = handler.handle(record)
        assert result is False


class TestBaseHandlerClose:
    """Test BaseHandler close method"""
    
    def test_close_sets_closed_flag(self):
        """Test close method sets _closed flag"""
        handler = MockHandler()
        assert handler._closed is False
        handler.close()
        assert handler._closed is True
    
    def test_close_multiple_calls(self):
        """Test close can be called multiple times"""
        handler = MockHandler()
        handler.close()
        handler.close()  # Should not raise
        assert handler._closed is True


class TestBaseHandlerFlush:
    """Test BaseHandler flush method"""
    
    def test_flush_does_nothing_by_default(self):
        """Test flush method does nothing by default"""
        handler = MockHandler()
        handler.flush()  # Should not raise


class TestBaseHandlerRepr:
    """Test BaseHandler __repr__ method"""
    
    def test_repr_format(self):
        """Test __repr__ format"""
        handler = MockHandler(level=LogLevel.INFO)
        repr_str = repr(handler)
        assert "MockHandler" in repr_str
        assert "INFO" in repr_str
    
    def test_repr_with_different_levels(self):
        """Test __repr__ with different levels"""
        for level in [DEBUG, INFO, WARNING, ERROR, CRITICAL]:
            handler = MockHandler(level=level)
            repr_str = repr(handler)
            assert LogLevel.get_name(level) in repr_str


class TestBaseHandlerThreadSafety:
    """Test BaseHandler thread safety"""
    
    def test_concurrent_handle(self):
        """Test concurrent handle calls"""
        handler = MockHandler()
        records = []
        
        def handle_record(i):
            record = LogRecord(name="test", level=INFO, msg=f"Test {i}", filename="test.py", lineno=1)
            handler.handle(record)
        
        threads = [threading.Thread(target=handle_record, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(handler.records) == 10


# ============================================
# HandlerChain Tests
# ============================================

class TestHandlerChainInit:
    """Test HandlerChain initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        chain = HandlerChain()
        assert len(chain) == 0
        assert chain.handlers == []


class TestHandlerChainAddHandler:
    """Test HandlerChain add_handler method"""
    
    def test_add_handler(self):
        """Test add_handler method"""
        chain = HandlerChain()
        handler = MockHandler()
        result = chain.add_handler(handler)
        assert result is chain  # Returns self for chaining
        assert len(chain) == 1
        assert handler in chain.handlers
    
    def test_add_handler_chain_call(self):
        """Test add_handler chain call"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        assert len(chain) == 2
    
    def test_add_same_handler_twice(self):
        """Test adding same handler twice is ignored"""
        chain = HandlerChain()
        handler = MockHandler()
        chain.add_handler(handler)
        chain.add_handler(handler)
        assert len(chain) == 1


class TestHandlerChainRemoveHandler:
    """Test HandlerChain remove_handler method"""
    
    def test_remove_handler(self):
        """Test remove_handler method"""
        chain = HandlerChain()
        handler = MockHandler()
        chain.add_handler(handler)
        result = chain.remove_handler(handler)
        assert result is chain  # Returns self for chaining
        assert len(chain) == 0
    
    def test_remove_non_existent_handler(self):
        """Test removing non-existent handler does nothing"""
        chain = HandlerChain()
        handler = MockHandler()
        chain.remove_handler(handler)  # Should not raise
        assert len(chain) == 0


class TestHandlerChainHandle:
    """Test HandlerChain handle method"""
    
    def test_handle_distributes_to_all(self):
        """Test handle distributes to all handlers"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        count = chain.handle(record)
        
        assert count == 2
        assert len(handler1.records) == 1
        assert len(handler2.records) == 1
    
    def test_handle_counts_successful_only(self):
        """Test handle counts only successful handlers"""
        chain = HandlerChain()
        handler1 = MockHandler(level=DEBUG)
        handler2 = MockHandler(level=ERROR)  # Will filter out INFO
        chain.add_handler(handler1).add_handler(handler2)
        
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        count = chain.handle(record)
        
        assert count == 1
        assert len(handler1.records) == 1
        assert len(handler2.records) == 0
    
    def test_handle_empty_chain(self):
        """Test handle on empty chain"""
        chain = HandlerChain()
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        count = chain.handle(record)
        assert count == 0


class TestHandlerChainFlush:
    """Test HandlerChain flush method"""
    
    def test_flush_all_handlers(self):
        """Test flush calls flush on all handlers"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        chain.flush()  # Should not raise


class TestHandlerChainClose:
    """Test HandlerChain close method"""
    
    def test_close_all_handlers(self):
        """Test close calls close on all handlers"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        chain.close()
        assert handler1._closed is True
        assert handler2._closed is True


class TestHandlerChainClear:
    """Test HandlerChain clear method"""
    
    def test_clear(self):
        """Test clear method"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        chain.clear()
        assert len(chain) == 0


class TestHandlerChainHandlers:
    """Test HandlerChain handlers property"""
    
    def test_handlers_returns_copy(self):
        """Test handlers property returns a copy"""
        chain = HandlerChain()
        handler = MockHandler()
        chain.add_handler(handler)
        handlers = chain.handlers
        handlers.append(MockHandler())  # Modify the copy
        assert len(chain) == 1  # Original not affected


class TestHandlerChainRepr:
    """Test HandlerChain __repr__ method"""
    
    def test_repr_format(self):
        """Test __repr__ format"""
        chain = HandlerChain()
        handler1 = MockHandler()
        handler2 = MockHandler()
        chain.add_handler(handler1).add_handler(handler2)
        repr_str = repr(chain)
        assert "HandlerChain" in repr_str
        assert "handlers=2" in repr_str


class TestHandlerChainLen:
    """Test HandlerChain __len__ method"""
    
    def test_len(self):
        """Test __len__ method"""
        chain = HandlerChain()
        assert len(chain) == 0
        chain.add_handler(MockHandler())
        assert len(chain) == 1
        chain.add_handler(MockHandler())
        assert len(chain) == 2


class TestHandlerChainThreadSafety:
    """Test HandlerChain thread safety"""
    
    def test_concurrent_add_handler(self):
        """Test concurrent add_handler calls"""
        chain = HandlerChain()
        
        def add_handler(i):
            handler = MockHandler(name=f"Handler-{i}")
            chain.add_handler(handler)
        
        threads = [threading.Thread(target=add_handler, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(chain) == 10
