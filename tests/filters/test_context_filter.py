"""
Test cases for logify.filters.context_filter module
"""

import os
import threading
import pytest
from logify.filters.context_filter import ContextFilter
from logify.core.record import LogRecord
from logify.core.levels import INFO


class TestContextFilterCreation:
    """Test ContextFilter initialization"""

    def test_default_creation(self):
        """Test creating filter with no parameters"""
        filter_ = ContextFilter()
        
        assert filter_._allowed_names is None
        assert filter_._denied_names == set()
        assert filter_._allowed_threads is None
        assert filter_._allowed_processes is None
        assert filter_._custom_check is None

    def test_create_with_allowed_names(self):
        """Test creating with allowed names"""
        allowed = {"app", "mylogger"}
        filter_ = ContextFilter(allowed_names=allowed)
        
        assert filter_._allowed_names == allowed

    def test_create_with_denied_names(self):
        """Test creating with denied names"""
        denied = {"debug", "verbose"}
        filter_ = ContextFilter(denied_names=denied)
        
        assert filter_._denied_names == denied

    def test_create_with_allowed_threads(self):
        """Test creating with allowed threads"""
        threads = {123, "MainThread"}
        filter_ = ContextFilter(allowed_threads=threads)
        
        assert filter_._allowed_threads == threads

    def test_create_with_allowed_processes(self):
        """Test creating with allowed processes"""
        processes = {1234, 5678}
        filter_ = ContextFilter(allowed_processes=processes)
        
        assert filter_._allowed_processes == processes

    def test_create_with_custom_check(self):
        """Test creating with custom check function"""
        def my_check(record):
            return True
        
        filter_ = ContextFilter(custom_check=my_check)
        
        assert filter_._custom_check is my_check

    def test_create_with_custom_name(self):
        """Test creating with custom filter name"""
        filter_ = ContextFilter(name="MyContextFilter")
        
        assert filter_.name == "MyContextFilter"


class TestContextFilterDeniedNames:
    """Test ContextFilter denied names filtering"""

    def test_deny_exact_name(self):
        """Test denying exact logger name"""
        filter_ = ContextFilter(denied_names={"blocked"})
        record = LogRecord(name="blocked", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_allow_non_denied_name(self):
        """Test allowing non-denied name"""
        filter_ = ContextFilter(denied_names={"blocked"})
        record = LogRecord(name="allowed", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_deny_multiple_names(self):
        """Test denying multiple names"""
        filter_ = ContextFilter(denied_names={"blocked1", "blocked2", "blocked3"})
        
        for name in ["blocked1", "blocked2", "blocked3"]:
            record = LogRecord(name=name, level=INFO, msg="Test")
            assert filter_.filter(record) is False


class TestContextFilterAllowedNames:
    """Test ContextFilter allowed names filtering"""

    def test_allow_exact_name(self):
        """Test allowing exact logger name"""
        filter_ = ContextFilter(allowed_names={"myapp"})
        record = LogRecord(name="myapp", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_deny_non_allowed_name(self):
        """Test denying non-allowed name"""
        filter_ = ContextFilter(allowed_names={"myapp"})
        record = LogRecord(name="other", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_allow_child_logger(self):
        """Test allowing child logger of allowed name"""
        filter_ = ContextFilter(allowed_names={"myapp"})
        record = LogRecord(name="myapp.module", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_allow_deeply_nested_child(self):
        """Test allowing deeply nested child logger"""
        filter_ = ContextFilter(allowed_names={"myapp"})
        record = LogRecord(name="myapp.module.submodule.component", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_no_restriction_when_allowed_names_none(self):
        """Test no name restriction when allowed_names is None"""
        filter_ = ContextFilter(allowed_names=None)
        
        for name in ["any", "name", "should", "pass"]:
            record = LogRecord(name=name, level=INFO, msg="Test")
            assert filter_.filter(record) is True


class TestContextFilterAllowedThreads:
    """Test ContextFilter allowed threads filtering"""

    def test_allow_by_thread_id(self):
        """Test allowing by thread ID"""
        current_id = threading.current_thread().ident
        filter_ = ContextFilter(allowed_threads={current_id})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_allow_by_thread_name(self):
        """Test allowing by thread name"""
        current_name = threading.current_thread().name
        filter_ = ContextFilter(allowed_threads={current_name})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_deny_non_allowed_thread(self):
        """Test denying non-allowed thread"""
        filter_ = ContextFilter(allowed_threads={99999, "OtherThread"})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_no_restriction_when_allowed_threads_none(self):
        """Test no thread restriction when allowed_threads is None"""
        filter_ = ContextFilter(allowed_threads=None)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True


class TestContextFilterAllowedProcesses:
    """Test ContextFilter allowed processes filtering"""

    def test_allow_current_process(self):
        """Test allowing current process ID"""
        current_pid = os.getpid()
        filter_ = ContextFilter(allowed_processes={current_pid})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_deny_non_allowed_process(self):
        """Test denying non-allowed process"""
        filter_ = ContextFilter(allowed_processes={99999})
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_no_restriction_when_allowed_processes_none(self):
        """Test no process restriction when allowed_processes is None"""
        filter_ = ContextFilter(allowed_processes=None)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True


class TestContextFilterCustomCheck:
    """Test ContextFilter custom check function"""

    def test_custom_check_passes(self):
        """Test custom check that passes"""
        def always_pass(record):
            return True
        
        filter_ = ContextFilter(custom_check=always_pass)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is True

    def test_custom_check_fails(self):
        """Test custom check that fails"""
        def always_fail(record):
            return False
        
        filter_ = ContextFilter(custom_check=always_fail)
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        assert filter_.filter(record) is False

    def test_custom_check_with_condition(self):
        """Test custom check with condition based on record"""
        def check_message(record):
            return "secret" not in record.message.lower()
        
        filter_ = ContextFilter(custom_check=check_message)
        
        # Should pass
        record1 = LogRecord(name="test", level=INFO, msg="Normal message")
        assert filter_.filter(record1) is True
        
        # Should fail
        record2 = LogRecord(name="test", level=INFO, msg="This is SECRET data")
        assert filter_.filter(record2) is False

    def test_custom_check_receives_record(self):
        """Test that custom check receives the log record"""
        received_records = []
        
        def capture_record(record):
            received_records.append(record)
            return True
        
        filter_ = ContextFilter(custom_check=capture_record)
        record = LogRecord(name="test", level=INFO, msg="Test message")
        filter_.filter(record)
        
        assert len(received_records) == 1
        assert received_records[0] is record


class TestContextFilterCombined:
    """Test ContextFilter with multiple conditions"""

    def test_denied_takes_precedence(self):
        """Test that denied names take precedence over allowed"""
        filter_ = ContextFilter(
            allowed_names={"myapp"},
            denied_names={"myapp"}
        )
        record = LogRecord(name="myapp", level=INFO, msg="Test")
        
        # Denied should take precedence
        assert filter_.filter(record) is False

    def test_all_conditions_must_pass(self):
        """Test that all conditions must pass"""
        current_pid = os.getpid()
        current_tid = threading.current_thread().ident
        
        filter_ = ContextFilter(
            allowed_names={"myapp"},
            allowed_threads={current_tid},
            allowed_processes={current_pid}
        )
        
        record = LogRecord(name="myapp", level=INFO, msg="Test")
        assert filter_.filter(record) is True
        
        # Wrong name
        record2 = LogRecord(name="other", level=INFO, msg="Test")
        assert filter_.filter(record2) is False


class TestContextFilterChainMethods:
    """Test ContextFilter chain methods"""

    def test_allow_name_method(self):
        """Test allow_name method"""
        filter_ = ContextFilter()
        
        result = filter_.allow_name("myapp")
        
        assert result is filter_  # Returns self
        assert "myapp" in filter_._allowed_names

    def test_allow_name_creates_set_if_none(self):
        """Test allow_name creates set if None"""
        filter_ = ContextFilter(allowed_names=None)
        
        filter_.allow_name("myapp")
        
        assert filter_._allowed_names == {"myapp"}

    def test_allow_name_chaining(self):
        """Test chaining allow_name calls"""
        filter_ = ContextFilter()
        
        filter_.allow_name("app1").allow_name("app2").allow_name("app3")
        
        assert filter_._allowed_names == {"app1", "app2", "app3"}

    def test_deny_name_method(self):
        """Test deny_name method"""
        filter_ = ContextFilter()
        
        result = filter_.deny_name("blocked")
        
        assert result is filter_  # Returns self
        assert "blocked" in filter_._denied_names

    def test_deny_name_chaining(self):
        """Test chaining deny_name calls"""
        filter_ = ContextFilter()
        
        filter_.deny_name("b1").deny_name("b2").deny_name("b3")
        
        assert filter_._denied_names == {"b1", "b2", "b3"}


class TestContextFilterRepr:
    """Test ContextFilter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        filter_ = ContextFilter()
        repr_str = repr(filter_)
        
        assert "ContextFilter" in repr_str

    def test_repr_contains_allowed_and_denied(self):
        """Test that repr contains allowed and denied names"""
        filter_ = ContextFilter(
            allowed_names={"app"},
            denied_names={"blocked"}
        )
        repr_str = repr(filter_)
        
        assert "allowed_names" in repr_str
        assert "denied_names" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
