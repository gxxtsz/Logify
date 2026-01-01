"""
Tests for logify.handlers.file module

Tests for FileHandler class
"""

import os
import tempfile
import pytest
from pathlib import Path

from logify.handlers.file import FileHandler
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR
from logify.core.record import LogRecord
from logify.formatters.text import TextFormatter


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_log_file(temp_dir):
    """Create a temporary log file path"""
    return temp_dir / "test.log"


class TestFileHandlerInit:
    """Test FileHandler initialization"""
    
    def test_default_initialization(self, temp_log_file):
        """Test default initialization"""
        handler = FileHandler(filename=temp_log_file)
        try:
            assert handler.filename == temp_log_file
            assert handler.level == DEBUG
            assert handler._mode == 'a'
            assert handler._encoding == 'utf-8'
            assert handler._delay is False
            assert handler._file is not None  # File is opened immediately
        finally:
            handler.close()
    
    def test_custom_mode_write(self, temp_log_file):
        """Test initialization with write mode"""
        handler = FileHandler(filename=temp_log_file, mode='w')
        try:
            assert handler._mode == 'w'
        finally:
            handler.close()
    
    def test_custom_encoding(self, temp_log_file):
        """Test initialization with custom encoding"""
        handler = FileHandler(filename=temp_log_file, encoding='latin-1')
        try:
            assert handler._encoding == 'latin-1'
        finally:
            handler.close()
    
    def test_custom_level(self, temp_log_file):
        """Test initialization with custom level"""
        handler = FileHandler(filename=temp_log_file, level=LogLevel.WARNING)
        try:
            assert handler.level == WARNING
        finally:
            handler.close()
    
    def test_custom_formatter(self, temp_log_file):
        """Test initialization with custom formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            assert handler.formatter is formatter
        finally:
            handler.close()
    
    def test_delay_mode(self, temp_log_file):
        """Test initialization with delay mode"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            assert handler._delay is True
            assert handler._file is None  # File is not opened yet
        finally:
            handler.close()
    
    def test_custom_name(self, temp_log_file):
        """Test initialization with custom name"""
        handler = FileHandler(filename=temp_log_file, name="MyFileHandler")
        try:
            assert handler.name == "MyFileHandler"
        finally:
            handler.close()
    
    def test_creates_parent_directory(self, temp_dir):
        """Test handler creates parent directory if not exists"""
        nested_path = temp_dir / "subdir1" / "subdir2" / "test.log"
        handler = FileHandler(filename=nested_path, delay=True)
        try:
            assert nested_path.parent.exists()
        finally:
            handler.close()
    
    def test_string_path(self, temp_dir):
        """Test initialization with string path"""
        path_str = str(temp_dir / "test.log")
        handler = FileHandler(filename=path_str)
        try:
            assert handler.filename == Path(path_str)
        finally:
            handler.close()


class TestFileHandlerFilename:
    """Test FileHandler filename property"""
    
    def test_filename_getter(self, temp_log_file):
        """Test filename property getter"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            assert handler.filename == temp_log_file
        finally:
            handler.close()
    
    def test_base_filename(self, temp_log_file):
        """Test base_filename property"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            assert handler.base_filename == str(temp_log_file)
        finally:
            handler.close()


class TestFileHandlerOpen:
    """Test FileHandler _open method"""
    
    def test_open_on_init_without_delay(self, temp_log_file):
        """Test file is opened on init when delay is False"""
        handler = FileHandler(filename=temp_log_file, delay=False)
        try:
            assert handler._file is not None
            assert not handler._file.closed
        finally:
            handler.close()
    
    def test_open_on_emit_with_delay(self, temp_log_file):
        """Test file is opened on emit when delay is True"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            assert handler._file is None
            
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)
            
            assert handler._file is not None
        finally:
            handler.close()
    
    def test_open_idempotent(self, temp_log_file):
        """Test _open is idempotent"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            handler._open()
            file1 = handler._file
            handler._open()  # Call again
            assert handler._file is file1  # Same file object
        finally:
            handler.close()


class TestFileHandlerEmit:
    """Test FileHandler emit method"""
    
    def test_emit_writes_to_file(self, temp_log_file):
        """Test emit writes formatted message to file"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Test message" in content
    
    def test_emit_multiple_records(self, temp_log_file):
        """Test emit writes multiple records"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            for i in range(3):
                record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
                handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Message 0" in content
        assert "Message 1" in content
        assert "Message 2" in content
    
    def test_emit_with_args(self, temp_log_file):
        """Test emit with message arguments"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record = LogRecord(
                name="test", level=INFO, msg="Hello %s", 
                args=("World",), filename="test.py", lineno=1
            )
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Hello World" in content
    
    def test_emit_with_delay(self, temp_log_file):
        """Test emit with delay mode opens file"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter, delay=True)
        try:
            assert handler._file is None
            
            record = LogRecord(name="test", level=INFO, msg="Delayed message", filename="test.py", lineno=1)
            handler.emit(record)
            
            assert handler._file is not None
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Delayed message" in content
    
    def test_emit_appends_newline(self, temp_log_file):
        """Test emit appends newline after each message"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record1 = LogRecord(name="test", level=INFO, msg="Line 1", filename="test.py", lineno=1)
            record2 = LogRecord(name="test", level=INFO, msg="Line 2", filename="test.py", lineno=1)
            handler.emit(record1)
            handler.emit(record2)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 2
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"


class TestFileHandlerFlush:
    """Test FileHandler flush method"""
    
    def test_flush_when_file_open(self, temp_log_file):
        """Test flush when file is open"""
        handler = FileHandler(filename=temp_log_file)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)
            handler.flush()  # Should not raise
        finally:
            handler.close()
    
    def test_flush_when_file_not_open(self, temp_log_file):
        """Test flush when file is not open"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            handler.flush()  # Should not raise
        finally:
            handler.close()


class TestFileHandlerClose:
    """Test FileHandler close method"""
    
    def test_close_sets_closed_flag(self, temp_log_file):
        """Test close sets _closed flag"""
        handler = FileHandler(filename=temp_log_file)
        assert handler._closed is False
        handler.close()
        assert handler._closed is True
    
    def test_close_closes_file(self, temp_log_file):
        """Test close closes the file"""
        handler = FileHandler(filename=temp_log_file)
        assert handler._file is not None
        handler.close()
        assert handler._file is None
    
    def test_close_multiple_calls(self, temp_log_file):
        """Test close can be called multiple times"""
        handler = FileHandler(filename=temp_log_file)
        handler.close()
        handler.close()  # Should not raise


class TestFileHandlerRepr:
    """Test FileHandler __repr__ method"""
    
    def test_repr_format(self, temp_log_file):
        """Test __repr__ format"""
        handler = FileHandler(filename=temp_log_file, delay=True)
        try:
            repr_str = repr(handler)
            assert "FileHandler" in repr_str
            assert "filename=" in repr_str
            assert "test.log" in repr_str
        finally:
            handler.close()


class TestFileHandlerAppendMode:
    """Test FileHandler append mode"""
    
    def test_append_mode_preserves_content(self, temp_log_file):
        """Test append mode preserves existing content"""
        # Write initial content
        temp_log_file.write_text("Initial content\n")
        
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, mode='a', formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="New message", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Initial content" in content
        assert "New message" in content


class TestFileHandlerWriteMode:
    """Test FileHandler write mode"""
    
    def test_write_mode_overwrites_content(self, temp_log_file):
        """Test write mode overwrites existing content"""
        # Write initial content
        temp_log_file.write_text("Initial content\n")
        
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, mode='w', formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="New message", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Initial content" not in content
        assert "New message" in content


class TestFileHandlerUnicode:
    """Test FileHandler with Unicode content"""
    
    def test_unicode_message(self, temp_log_file):
        """Test writing Unicode message"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="日志消息 🎉", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text(encoding='utf-8')
        assert "日志消息 🎉" in content
    
    def test_unicode_with_different_encoding(self, temp_log_file):
        """Test writing Unicode with specific encoding"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter, encoding='utf-8')
        try:
            record = LogRecord(name="test", level=INFO, msg="中文测试", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text(encoding='utf-8')
        assert "中文测试" in content


class TestFileHandlerLevelFiltering:
    """Test FileHandler level filtering"""
    
    def test_filters_by_level(self, temp_log_file):
        """Test handler filters by level"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = FileHandler(filename=temp_log_file, formatter=formatter, level=WARNING)
        try:
            record_info = LogRecord(name="test", level=INFO, msg="Info message", filename="test.py", lineno=1)
            record_warning = LogRecord(name="test", level=WARNING, msg="Warning message", filename="test.py", lineno=1)
            
            handler.handle(record_info)
            handler.handle(record_warning)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Info message" not in content
        assert "Warning message" in content
