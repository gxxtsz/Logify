"""
Tests for logify.handlers.rotating module

Tests for RotatingFileHandler and TimedRotatingFileHandler classes
"""

import os
import gzip
import tempfile
import time
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from logify.handlers.rotating import RotatingFileHandler, TimedRotatingFileHandler
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING
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


# ============================================
# RotatingFileHandler Tests
# ============================================

class TestRotatingFileHandlerInit:
    """Test RotatingFileHandler initialization"""
    
    def test_default_initialization(self, temp_log_file):
        """Test default initialization"""
        handler = RotatingFileHandler(filename=temp_log_file)
        try:
            assert handler.filename == temp_log_file
            assert handler.max_bytes == 10 * 1024 * 1024  # 10MB
            assert handler.backup_count == 5
            assert handler._compress is False
            assert handler.level == DEBUG
        finally:
            handler.close()
    
    def test_custom_max_bytes(self, temp_log_file):
        """Test initialization with custom max_bytes"""
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=1024)
        try:
            assert handler.max_bytes == 1024
        finally:
            handler.close()
    
    def test_custom_backup_count(self, temp_log_file):
        """Test initialization with custom backup_count"""
        handler = RotatingFileHandler(filename=temp_log_file, backup_count=10)
        try:
            assert handler.backup_count == 10
        finally:
            handler.close()
    
    def test_compression_enabled(self, temp_log_file):
        """Test initialization with compression enabled"""
        handler = RotatingFileHandler(filename=temp_log_file, compress=True)
        try:
            assert handler._compress is True
        finally:
            handler.close()
    
    def test_custom_level(self, temp_log_file):
        """Test initialization with custom level"""
        handler = RotatingFileHandler(filename=temp_log_file, level=LogLevel.WARNING)
        try:
            assert handler.level == WARNING
        finally:
            handler.close()
    
    def test_delay_mode(self, temp_log_file):
        """Test handler uses delay mode by default"""
        handler = RotatingFileHandler(filename=temp_log_file)
        try:
            assert handler._delay is True
            assert handler._file is None
        finally:
            handler.close()


class TestRotatingFileHandlerProperties:
    """Test RotatingFileHandler properties"""
    
    def test_max_bytes_property(self, temp_log_file):
        """Test max_bytes property"""
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=2048)
        try:
            assert handler.max_bytes == 2048
        finally:
            handler.close()
    
    def test_backup_count_property(self, temp_log_file):
        """Test backup_count property"""
        handler = RotatingFileHandler(filename=temp_log_file, backup_count=3)
        try:
            assert handler.backup_count == 3
        finally:
            handler.close()


class TestRotatingFileHandlerShouldRollover:
    """Test RotatingFileHandler should_rollover method"""
    
    def test_should_not_rollover_when_max_bytes_zero(self, temp_log_file):
        """Test no rollover when max_bytes is 0"""
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=0)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            assert handler.should_rollover(record) is False
        finally:
            handler.close()
    
    def test_should_not_rollover_small_file(self, temp_log_file):
        """Test no rollover for small file"""
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=10000)
        try:
            record = LogRecord(name="test", level=INFO, msg="Small message", filename="test.py", lineno=1)
            handler.emit(record)
            assert handler.should_rollover(record) is False
        finally:
            handler.close()
    
    def test_should_rollover_large_file(self, temp_log_file):
        """Test rollover for large file"""
        formatter = TextFormatter(fmt="%(message)s")
        # Use a very small max_bytes so a single message triggers rollover
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=10, formatter=formatter)
        try:
            # First emit opens the file
            record1 = LogRecord(name="test", level=INFO, msg="A" * 5, filename="test.py", lineno=1)
            handler.emit(record1)  # File now has about 6 bytes
            
            # This record should trigger rollover check to return True
            record2 = LogRecord(name="test", level=INFO, msg="B" * 10, filename="test.py", lineno=1)
            assert handler.should_rollover(record2) is True
        finally:
            handler.close()


class TestRotatingFileHandlerDoRollover:
    """Test RotatingFileHandler do_rollover method"""
    
    def test_rollover_creates_backup(self, temp_log_file):
        """Test rollover creates backup file"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=50, formatter=formatter)
        try:
            # Write some data
            record = LogRecord(name="test", level=INFO, msg="Initial data", filename="test.py", lineno=1)
            handler.emit(record)
            
            # Force rollover
            handler.do_rollover()
            
            # Check backup file exists
            backup = temp_log_file.parent / (temp_log_file.name + ".1")
            assert backup.exists()
        finally:
            handler.close()
    
    def test_rollover_rotates_backups(self, temp_log_file):
        """Test rollover rotates existing backups"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=50, backup_count=3, formatter=formatter)
        try:
            # Create multiple rollovers
            for i in range(3):
                record = LogRecord(name="test", level=INFO, msg=f"Data {i}", filename="test.py", lineno=1)
                handler.emit(record)
                handler.do_rollover()
            
            # Check backup files exist
            backup1 = temp_log_file.parent / (temp_log_file.name + ".1")
            backup2 = temp_log_file.parent / (temp_log_file.name + ".2")
            backup3 = temp_log_file.parent / (temp_log_file.name + ".3")
            
            assert backup1.exists()
            assert backup2.exists()
            assert backup3.exists()
        finally:
            handler.close()
    
    def test_rollover_with_compression(self, temp_log_file):
        """Test rollover with compression enabled"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=50, compress=True, formatter=formatter)
        try:
            # Write some data
            record = LogRecord(name="test", level=INFO, msg="Compress me", filename="test.py", lineno=1)
            handler.emit(record)
            
            # Force rollover
            handler.do_rollover()
            
            # Check that some backup file was created (implementation detail may vary)
            all_backups = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*"))
            # Should have at least one backup file
            assert len(all_backups) >= 1
        finally:
            handler.close()


class TestRotatingFileHandlerGetBackupFilename:
    """Test RotatingFileHandler _get_backup_filename method"""
    
    def test_backup_filename_without_compression(self, temp_log_file):
        """Test backup filename without compression"""
        handler = RotatingFileHandler(filename=temp_log_file, compress=False)
        try:
            backup = handler._get_backup_filename(1)
            assert backup == Path(str(temp_log_file) + ".1")
        finally:
            handler.close()
    
    def test_backup_filename_with_compression(self, temp_log_file):
        """Test backup filename with compression"""
        handler = RotatingFileHandler(filename=temp_log_file, compress=True)
        try:
            backup = handler._get_backup_filename(1)
            assert backup == Path(str(temp_log_file) + ".1.gz")
        finally:
            handler.close()
    
    def test_backup_filename_index_zero(self, temp_log_file):
        """Test backup filename for index 0"""
        handler = RotatingFileHandler(filename=temp_log_file, compress=True)
        try:
            backup = handler._get_backup_filename(0)
            # Index 0 doesn't get .gz suffix
            assert backup == Path(str(temp_log_file) + ".0")
        finally:
            handler.close()


class TestRotatingFileHandlerCleanup:
    """Test RotatingFileHandler _cleanup_old_backups method"""
    
    def test_cleanup_removes_old_backups(self, temp_log_file):
        """Test cleanup removes old backups"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=30, backup_count=2, formatter=formatter)
        try:
            # Create many backups
            for i in range(5):
                record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
                handler.emit(record)
                handler.do_rollover()
            
            # Only backup_count (2) should remain
            backup1 = temp_log_file.parent / (temp_log_file.name + ".1")
            backup2 = temp_log_file.parent / (temp_log_file.name + ".2")
            backup3 = temp_log_file.parent / (temp_log_file.name + ".3")
            
            assert backup1.exists()
            assert backup2.exists()
            assert not backup3.exists()
        finally:
            handler.close()


class TestRotatingFileHandlerEmit:
    """Test RotatingFileHandler emit method"""
    
    def test_emit_triggers_rollover(self, temp_log_file):
        """Test emit triggers rollover when needed"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=50, formatter=formatter)
        try:
            # Write enough to trigger rollover
            for i in range(5):
                record = LogRecord(name="test", level=INFO, msg="A" * 20, filename="test.py", lineno=1)
                handler.emit(record)
            
            # Backup should exist
            backup = temp_log_file.parent / (temp_log_file.name + ".1")
            assert backup.exists()
        finally:
            handler.close()
    
    def test_emit_writes_to_file(self, temp_log_file):
        """Test emit writes to file"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, max_bytes=10000, formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Test message" in content


# ============================================
# TimedRotatingFileHandler Tests
# ============================================

class TestTimedRotatingFileHandlerInit:
    """Test TimedRotatingFileHandler initialization"""
    
    def test_default_initialization(self, temp_log_file):
        """Test default initialization"""
        handler = TimedRotatingFileHandler(filename=temp_log_file)
        try:
            assert handler.filename == temp_log_file
            assert handler._when == 'D'
            assert handler._interval == 1
            assert handler._backup_count == 7
            assert handler._compress is False
        finally:
            handler.close()
    
    def test_custom_when(self, temp_log_file):
        """Test initialization with custom when"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='H')
        try:
            assert handler._when == 'H'
        finally:
            handler.close()
    
    def test_when_case_insensitive(self, temp_log_file):
        """Test when parameter is case insensitive"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='midnight')
        try:
            assert handler._when == 'MIDNIGHT'
        finally:
            handler.close()
    
    def test_custom_interval(self, temp_log_file):
        """Test initialization with custom interval"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, interval=2)
        try:
            assert handler._interval == 2
        finally:
            handler.close()
    
    def test_custom_backup_count(self, temp_log_file):
        """Test initialization with custom backup_count"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, backup_count=14)
        try:
            assert handler._backup_count == 14
        finally:
            handler.close()
    
    def test_compression_enabled(self, temp_log_file):
        """Test initialization with compression enabled"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, compress=True)
        try:
            assert handler._compress is True
        finally:
            handler.close()
    
    def test_invalid_when_raises_error(self, temp_log_file):
        """Test invalid when value raises ValueError"""
        with pytest.raises(ValueError):
            TimedRotatingFileHandler(filename=temp_log_file, when='INVALID')


class TestTimedRotatingFileHandlerWhenMapping:
    """Test TimedRotatingFileHandler WHEN_MAPPING"""
    
    def test_seconds(self, temp_log_file):
        """Test S (seconds) mapping"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', interval=30)
        try:
            assert handler._interval_seconds == 30
        finally:
            handler.close()
    
    def test_minutes(self, temp_log_file):
        """Test M (minutes) mapping"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='M', interval=5)
        try:
            assert handler._interval_seconds == 5 * 60
        finally:
            handler.close()
    
    def test_hours(self, temp_log_file):
        """Test H (hours) mapping"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='H', interval=2)
        try:
            assert handler._interval_seconds == 2 * 3600
        finally:
            handler.close()
    
    def test_days(self, temp_log_file):
        """Test D (days) mapping"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='D', interval=1)
        try:
            assert handler._interval_seconds == 86400
        finally:
            handler.close()
    
    def test_midnight(self, temp_log_file):
        """Test MIDNIGHT mapping"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='MIDNIGHT')
        try:
            assert handler._interval_seconds == 86400
        finally:
            handler.close()


class TestTimedRotatingFileHandlerComputeRolloverTime:
    """Test TimedRotatingFileHandler _compute_rollover_time method"""
    
    def test_compute_rollover_time_midnight(self, temp_log_file):
        """Test rollover time computation for MIDNIGHT"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='MIDNIGHT')
        try:
            rollover_time = handler._rollover_at
            now = datetime.now()
            tomorrow_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            # Should be close to tomorrow midnight
            assert abs(rollover_time - tomorrow_midnight.timestamp()) < 2
        finally:
            handler.close()
    
    def test_compute_rollover_time_interval(self, temp_log_file):
        """Test rollover time computation for interval-based"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='H', interval=1)
        try:
            rollover_time = handler._rollover_at
            now = datetime.now().timestamp()
            
            # Should be in the future
            assert rollover_time > now - 1  # Allow small time difference
        finally:
            handler.close()


class TestTimedRotatingFileHandlerShouldRollover:
    """Test TimedRotatingFileHandler should_rollover method"""
    
    def test_should_not_rollover_before_time(self, temp_log_file):
        """Test no rollover before rollover time"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='D')
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            assert handler.should_rollover(record) is False
        finally:
            handler.close()
    
    def test_should_rollover_after_time(self, temp_log_file):
        """Test rollover after rollover time"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', interval=1)
        try:
            # Set rollover time to past
            handler._rollover_at = time.time() - 10
            
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            assert handler.should_rollover(record) is True
        finally:
            handler.close()


class TestTimedRotatingFileHandlerDoRollover:
    """Test TimedRotatingFileHandler do_rollover method"""
    
    def test_rollover_creates_timestamped_backup(self, temp_log_file):
        """Test rollover creates timestamped backup"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', formatter=formatter)
        try:
            # Write some data
            record = LogRecord(name="test", level=INFO, msg="Test data", filename="test.py", lineno=1)
            handler.emit(record)
            
            # Force rollover
            handler.do_rollover()
            
            # Check for backup file with timestamp
            backup_files = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*"))
            assert len(backup_files) > 0
        finally:
            handler.close()
    
    def test_rollover_updates_rollover_time(self, temp_log_file):
        """Test rollover updates next rollover time"""
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='H')
        try:
            old_rollover_at = handler._rollover_at
            
            # Write and rollover
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)
            handler.do_rollover()
            
            # Rollover time should be updated
            assert handler._rollover_at != old_rollover_at
        finally:
            handler.close()
    
    def test_rollover_with_compression(self, temp_log_file):
        """Test rollover with compression"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', compress=True, formatter=formatter)
        try:
            # Write some data
            record = LogRecord(name="test", level=INFO, msg="Compress me timed", filename="test.py", lineno=1)
            handler.emit(record)
            
            # Force rollover
            handler.do_rollover()
            
            # Check for compressed backup
            backup_files = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*.gz"))
            assert len(backup_files) > 0
        finally:
            handler.close()


class TestTimedRotatingFileHandlerCleanup:
    """Test TimedRotatingFileHandler _cleanup_old_backups method"""
    
    def test_cleanup_removes_old_backups(self, temp_log_file):
        """Test cleanup removes old timestamped backups"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', backup_count=2, formatter=formatter)
        try:
            # Create multiple backups with sufficient delay to get unique timestamps
            for i in range(3):
                record = LogRecord(name="test", level=INFO, msg=f"Message {i}", filename="test.py", lineno=1)
                handler.emit(record)
                time.sleep(1.1)  # Ensure different second timestamps
                handler.do_rollover()
            
            # Should only keep backup_count files
            backup_files = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*"))
            # Filter out non-backup files
            backup_files = [f for f in backup_files if f.name != temp_log_file.name]
            assert len(backup_files) <= 2
        finally:
            handler.close()


class TestTimedRotatingFileHandlerEmit:
    """Test TimedRotatingFileHandler emit method"""
    
    def test_emit_triggers_rollover(self, temp_log_file):
        """Test emit triggers rollover when needed"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='S', formatter=formatter)
        try:
            # First write some content to the file
            record1 = LogRecord(name="test", level=INFO, msg="Initial content", filename="test.py", lineno=1)
            handler.emit(record1)
            
            # Set rollover time to past to force rollover on next emit
            handler._rollover_at = time.time() - 10
            
            record2 = LogRecord(name="test", level=INFO, msg="Trigger rollover", filename="test.py", lineno=1)
            handler.emit(record2)
            
            # Backup should exist - look for any backup file pattern
            backup_files = list(temp_log_file.parent.glob(f"{temp_log_file.name}.*"))
            # There should be at least one backup file
            backup_files = [f for f in backup_files if f.name != temp_log_file.name]
            assert len(backup_files) >= 1
        finally:
            handler.close()
    
    def test_emit_writes_to_file(self, temp_log_file):
        """Test emit writes to file"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, when='D', formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="Timed message", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Timed message" in content


# ============================================
# Common Tests for Both Handlers
# ============================================

class TestRotatingHandlersLevelFiltering:
    """Test level filtering for rotating handlers"""
    
    def test_rotating_handler_filters_by_level(self, temp_log_file):
        """Test RotatingFileHandler filters by level"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, level=WARNING, formatter=formatter)
        try:
            record_info = LogRecord(name="test", level=INFO, msg="Info", filename="test.py", lineno=1)
            record_warning = LogRecord(name="test", level=WARNING, msg="Warning", filename="test.py", lineno=1)
            
            handler.handle(record_info)
            handler.handle(record_warning)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Info" not in content
        assert "Warning" in content
    
    def test_timed_handler_filters_by_level(self, temp_log_file):
        """Test TimedRotatingFileHandler filters by level"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, level=WARNING, formatter=formatter)
        try:
            record_info = LogRecord(name="test", level=INFO, msg="Info", filename="test.py", lineno=1)
            record_warning = LogRecord(name="test", level=WARNING, msg="Warning", filename="test.py", lineno=1)
            
            handler.handle(record_info)
            handler.handle(record_warning)
        finally:
            handler.close()
        
        content = temp_log_file.read_text()
        assert "Info" not in content
        assert "Warning" in content


class TestRotatingHandlersUnicode:
    """Test Unicode handling for rotating handlers"""
    
    def test_rotating_handler_unicode(self, temp_log_file):
        """Test RotatingFileHandler with Unicode"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = RotatingFileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="日志轮转 🔄", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text(encoding='utf-8')
        assert "日志轮转 🔄" in content
    
    def test_timed_handler_unicode(self, temp_log_file):
        """Test TimedRotatingFileHandler with Unicode"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = TimedRotatingFileHandler(filename=temp_log_file, formatter=formatter)
        try:
            record = LogRecord(name="test", level=INFO, msg="定时轮转 ⏰", filename="test.py", lineno=1)
            handler.emit(record)
        finally:
            handler.close()
        
        content = temp_log_file.read_text(encoding='utf-8')
        assert "定时轮转 ⏰" in content
