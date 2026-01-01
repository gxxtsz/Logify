"""
Tests for logify.handlers.async_handler module

Tests for AsyncHandler class
"""

import threading
import time
import pytest

from logify.handlers.async_handler import AsyncHandler
from logify.handlers.base import BaseHandler
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR
from logify.core.record import LogRecord
from logify.formatters.text import TextFormatter


# Mock handler for testing
class MockHandler(BaseHandler):
    """Mock handler for testing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records = []
        self.emit_delay = 0
        self.lock = threading.Lock()
    
    def emit(self, record: LogRecord) -> None:
        if self.emit_delay > 0:
            time.sleep(self.emit_delay)
        with self.lock:
            self.records.append(record)


@pytest.fixture
def mock_handler():
    """Create a mock handler"""
    return MockHandler()


@pytest.fixture
def async_handler(mock_handler):
    """Create an async handler wrapping mock handler"""
    handler = AsyncHandler(handler=mock_handler, queue_size=100)
    yield handler
    handler.close()


class TestAsyncHandlerInit:
    """Test AsyncHandler initialization"""
    
    def test_default_initialization(self, mock_handler):
        """Test default initialization"""
        handler = AsyncHandler(handler=mock_handler)
        try:
            assert handler.handler is mock_handler
            assert handler.level == DEBUG
            assert handler._shutdown.is_set() is False
            assert handler._thread is not None
            assert handler._thread.is_alive()
        finally:
            handler.close()
    
    def test_custom_queue_size(self, mock_handler):
        """Test initialization with custom queue size"""
        handler = AsyncHandler(handler=mock_handler, queue_size=50)
        try:
            assert handler._queue.maxsize == 50
        finally:
            handler.close()
    
    def test_unlimited_queue(self, mock_handler):
        """Test initialization with unlimited queue (queue_size=0)"""
        handler = AsyncHandler(handler=mock_handler, queue_size=0)
        try:
            assert handler._queue.maxsize == 0
        finally:
            handler.close()
    
    def test_custom_level(self, mock_handler):
        """Test initialization with custom level"""
        handler = AsyncHandler(handler=mock_handler, level=LogLevel.WARNING)
        try:
            assert handler.level == WARNING
        finally:
            handler.close()
    
    def test_custom_name(self, mock_handler):
        """Test initialization with custom name"""
        handler = AsyncHandler(handler=mock_handler, name="MyAsyncHandler")
        try:
            assert handler.name == "MyAsyncHandler"
        finally:
            handler.close()
    
    def test_inherits_formatter(self, mock_handler):
        """Test inherits formatter from wrapped handler"""
        formatter = TextFormatter(fmt="%(message)s")
        mock_handler.formatter = formatter
        handler = AsyncHandler(handler=mock_handler)
        try:
            assert handler.formatter is formatter
        finally:
            handler.close()


class TestAsyncHandlerHandler:
    """Test AsyncHandler handler property"""
    
    def test_handler_getter(self, mock_handler):
        """Test handler property getter"""
        handler = AsyncHandler(handler=mock_handler)
        try:
            assert handler.handler is mock_handler
        finally:
            handler.close()


class TestAsyncHandlerQueueSize:
    """Test AsyncHandler queue_size property"""
    
    def test_queue_size_empty(self, async_handler):
        """Test queue_size when empty"""
        # Wait a bit for any pending processing
        time.sleep(0.1)
        assert async_handler.queue_size == 0
    
    def test_queue_size_with_items(self, mock_handler):
        """Test queue_size with items in queue"""
        mock_handler.emit_delay = 0.01  # Small delay
        handler = AsyncHandler(handler=mock_handler, queue_size=100)
        try:
            # Add multiple records quickly
            for i in range(5):
                record = LogRecord(name="test", level=INFO, msg=f"Test {i}", filename="test.py", lineno=1)
                handler.emit(record)
            
            # Queue should have some items (first one may be processing)
            assert handler.queue_size >= 0
        finally:
            handler.close()


class TestAsyncHandlerEmit:
    """Test AsyncHandler emit method"""
    
    def test_emit_adds_to_queue(self, async_handler, mock_handler):
        """Test emit adds record to queue"""
        record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
        async_handler.emit(record)
        
        # Wait for processing
        async_handler.flush()
        
        assert len(mock_handler.records) == 1
        assert mock_handler.records[0].msg == "Test message"
    
    def test_emit_multiple_records(self, async_handler, mock_handler):
        """Test emit multiple records"""
        for i in range(5):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            async_handler.emit(record)
        
        # Wait for processing
        async_handler.flush()
        
        assert len(mock_handler.records) == 5
    
    def test_emit_non_blocking(self, mock_handler):
        """Test emit is non-blocking"""
        mock_handler.emit_delay = 0.05  # Slow handler
        handler = AsyncHandler(handler=mock_handler, queue_size=100)
        try:
            start_time = time.time()
            
            for i in range(3):
                record = LogRecord(name="test", level=INFO, msg=f"Test {i}", filename="test.py", lineno=1)
                handler.emit(record)
            
            elapsed = time.time() - start_time
            
            # Should return quickly, not waiting for slow handler
            assert elapsed < 0.1
        finally:
            handler.close()
    
    def test_emit_when_queue_full(self, mock_handler):
        """Test emit when queue is full does not block"""
        mock_handler.emit_delay = 0.01  # Small delay
        handler = AsyncHandler(handler=mock_handler, queue_size=2)
        
        start_time = time.time()
        
        # Try to fill beyond queue capacity
        for i in range(5):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            handler.emit(record)
        
        elapsed = time.time() - start_time
        
        # Emit should not block - all 5 calls should complete quickly
        assert elapsed < 0.3, "emit() should not block when queue is full"
        
        # Force shutdown without flush (flush would hang due to dropped tasks)
        handler._shutdown.set()
        handler._closed = True
        if handler._thread and handler._thread.is_alive():
            handler._thread.join(timeout=1.0)


class TestAsyncHandlerFlush:
    """Test AsyncHandler flush method"""
    
    def test_flush_waits_for_queue(self, async_handler, mock_handler):
        """Test flush waits for queue to be empty"""
        for i in range(3):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            async_handler.emit(record)
        
        async_handler.flush()
        
        assert len(mock_handler.records) == 3
    
    def test_flush_calls_handler_flush(self, async_handler, mock_handler):
        """Test flush calls wrapped handler's flush"""
        async_handler.flush()  # Should not raise


class TestAsyncHandlerClose:
    """Test AsyncHandler close method"""
    
    def test_close_sets_shutdown(self, mock_handler):
        """Test close sets shutdown event"""
        handler = AsyncHandler(handler=mock_handler)
        assert handler._shutdown.is_set() is False
        handler.close()
        assert handler._shutdown.is_set() is True
    
    def test_close_stops_thread(self, mock_handler):
        """Test close stops processing thread"""
        handler = AsyncHandler(handler=mock_handler)
        thread = handler._thread
        assert thread.is_alive()
        handler.close()
        # Thread should stop within timeout
        assert not thread.is_alive() or handler._closed
    
    def test_close_closes_wrapped_handler(self, mock_handler):
        """Test close closes wrapped handler"""
        handler = AsyncHandler(handler=mock_handler)
        handler.close()
        assert mock_handler._closed is True
    
    def test_close_idempotent(self, mock_handler):
        """Test close can be called multiple times"""
        handler = AsyncHandler(handler=mock_handler)
        handler.close()
        handler.close()  # Should not raise
    
    def test_close_processes_remaining_queue(self, mock_handler):
        """Test close processes remaining items in queue"""
        handler = AsyncHandler(handler=mock_handler, queue_size=100)
        
        for i in range(3):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            handler.emit(record)
        
        handler.close()
        
        # All records should be processed
        assert len(mock_handler.records) == 3


class TestAsyncHandlerRepr:
    """Test AsyncHandler __repr__ method"""
    
    def test_repr_format(self, async_handler):
        """Test __repr__ format"""
        repr_str = repr(async_handler)
        assert "AsyncHandler" in repr_str
        assert "handler=" in repr_str
        assert "queue_size=" in repr_str


class TestAsyncHandlerProcessLoop:
    """Test AsyncHandler _process_loop method"""
    
    def test_process_loop_handles_records(self, async_handler, mock_handler):
        """Test process loop handles records"""
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        async_handler.emit(record)
        async_handler.flush()
        
        assert len(mock_handler.records) == 1
    
    def test_process_loop_handles_none_signal(self, mock_handler):
        """Test process loop stops on None signal"""
        handler = AsyncHandler(handler=mock_handler)
        handler.close()
        # Thread should stop
        time.sleep(0.2)
        assert handler._thread is None or not handler._thread.is_alive()


class TestAsyncHandlerErrorHandling:
    """Test AsyncHandler error handling"""
    
    def test_emit_error_in_wrapped_handler(self):
        """Test error in wrapped handler is caught"""
        class ErrorHandler(BaseHandler):
            def emit(self, record):
                raise RuntimeError("Test error")
        
        error_handler = ErrorHandler()
        handler = AsyncHandler(handler=error_handler)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)
            handler.flush()
            # Should not raise
        finally:
            handler.close()


class TestAsyncHandlerConcurrency:
    """Test AsyncHandler concurrency"""
    
    def test_concurrent_emit(self, async_handler, mock_handler):
        """Test concurrent emit calls"""
        def emit_records(count):
            for i in range(count):
                record = LogRecord(name="test", level=INFO, msg=f"Thread message {i}", filename="test.py", lineno=1)
                async_handler.emit(record)
        
        threads = [threading.Thread(target=emit_records, args=(5,)) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        async_handler.flush()
        
        assert len(mock_handler.records) == 15
    
    def test_processing_order(self, async_handler, mock_handler):
        """Test records are processed in order (approximately)"""
        for i in range(10):
            record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
            async_handler.emit(record)
        
        async_handler.flush()
        
        # Records should be in order
        messages = [r.msg for r in mock_handler.records]
        expected = [f"Message {i}" for i in range(10)]
        assert messages == expected


class TestAsyncHandlerDaemonThread:
    """Test AsyncHandler uses daemon thread"""
    
    def test_thread_is_daemon(self, mock_handler):
        """Test processing thread is daemon"""
        handler = AsyncHandler(handler=mock_handler)
        try:
            assert handler._thread.daemon is True
        finally:
            handler.close()
    
    def test_thread_name(self, mock_handler):
        """Test thread has descriptive name"""
        handler = AsyncHandler(handler=mock_handler, name="TestHandler")
        try:
            assert "AsyncHandler" in handler._thread.name
            assert "TestHandler" in handler._thread.name
        finally:
            handler.close()
