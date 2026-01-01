"""
Test cases for logify.filters.regex_filter module
"""

import re
import pytest
from logify.filters.regex_filter import RegexFilter
from logify.core.record import LogRecord
from logify.core.levels import INFO


class TestRegexFilterCreation:
    """Test RegexFilter initialization"""

    def test_create_with_string_pattern(self):
        """Test creating with string pattern"""
        filter_ = RegexFilter(pattern=r"error")
        
        assert filter_.pattern.pattern == "error"

    def test_create_with_compiled_pattern(self):
        """Test creating with pre-compiled pattern"""
        compiled = re.compile(r"warning", re.IGNORECASE)
        filter_ = RegexFilter(pattern=compiled)
        
        assert filter_.pattern is compiled

    def test_create_with_flags(self):
        """Test creating with regex flags"""
        filter_ = RegexFilter(pattern=r"error", flags=re.IGNORECASE)
        
        # The pattern should be case-insensitive
        assert filter_.pattern.flags & re.IGNORECASE

    def test_default_match_pass_is_true(self):
        """Test that default match_pass is True"""
        filter_ = RegexFilter(pattern=r"test")
        
        assert filter_.match_pass is True

    def test_create_with_match_pass_false(self):
        """Test creating with match_pass=False"""
        filter_ = RegexFilter(pattern=r"test", match_pass=False)
        
        assert filter_.match_pass is False

    def test_create_with_custom_name(self):
        """Test creating with custom filter name"""
        filter_ = RegexFilter(pattern=r"test", name="MyRegexFilter")
        
        assert filter_.name == "MyRegexFilter"


class TestRegexFilterProperties:
    """Test RegexFilter properties"""

    def test_pattern_property(self):
        """Test pattern property"""
        filter_ = RegexFilter(pattern=r"error\d+")
        
        assert filter_.pattern.pattern == r"error\d+"

    def test_match_pass_property(self):
        """Test match_pass property"""
        filter1 = RegexFilter(pattern=r"test", match_pass=True)
        filter2 = RegexFilter(pattern=r"test", match_pass=False)
        
        assert filter1.match_pass is True
        assert filter2.match_pass is False


class TestRegexFilterMatchPass:
    """Test RegexFilter with match_pass=True (match to pass)"""

    def test_match_passes(self):
        """Test that matching message passes"""
        filter_ = RegexFilter(pattern=r"error")
        record = LogRecord(name="test", level=INFO, msg="An error occurred")
        
        assert filter_.filter(record) is True

    def test_no_match_fails(self):
        """Test that non-matching message fails"""
        filter_ = RegexFilter(pattern=r"error")
        record = LogRecord(name="test", level=INFO, msg="All is well")
        
        assert filter_.filter(record) is False

    def test_partial_match(self):
        """Test that partial match works (search, not match)"""
        filter_ = RegexFilter(pattern=r"warn")
        record = LogRecord(name="test", level=INFO, msg="This is a warning message")
        
        assert filter_.filter(record) is True

    def test_case_sensitive_by_default(self):
        """Test that matching is case-sensitive by default"""
        filter_ = RegexFilter(pattern=r"ERROR")
        
        record1 = LogRecord(name="test", level=INFO, msg="ERROR occurred")
        record2 = LogRecord(name="test", level=INFO, msg="error occurred")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is False

    def test_case_insensitive_with_flag(self):
        """Test case-insensitive matching with flag"""
        filter_ = RegexFilter(pattern=r"error", flags=re.IGNORECASE)
        
        record1 = LogRecord(name="test", level=INFO, msg="ERROR occurred")
        record2 = LogRecord(name="test", level=INFO, msg="Error occurred")
        record3 = LogRecord(name="test", level=INFO, msg="error occurred")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is True
        assert filter_.filter(record3) is True


class TestRegexFilterMatchReject:
    """Test RegexFilter with match_pass=False (match to reject)"""

    def test_match_rejects(self):
        """Test that matching message is rejected"""
        filter_ = RegexFilter(pattern=r"password", match_pass=False)
        record = LogRecord(name="test", level=INFO, msg="User password: secret123")
        
        assert filter_.filter(record) is False

    def test_no_match_passes(self):
        """Test that non-matching message passes"""
        filter_ = RegexFilter(pattern=r"password", match_pass=False)
        record = LogRecord(name="test", level=INFO, msg="User logged in successfully")
        
        assert filter_.filter(record) is True

    def test_filter_sensitive_data(self):
        """Test filtering out sensitive data patterns"""
        filter_ = RegexFilter(
            pattern=r"(password|secret|api.?key|token)",
            match_pass=False,
            flags=re.IGNORECASE
        )
        
        # Should be rejected
        sensitive_messages = [
            "password: 12345",
            "SECRET data here",
            "API_KEY=abc123",
            "apikey exposed",
            "Token: xyz789",
        ]
        
        for msg in sensitive_messages:
            record = LogRecord(name="test", level=INFO, msg=msg)
            assert filter_.filter(record) is False, f"Should reject: {msg}"
        
        # Should pass
        safe_messages = [
            "User logged in",
            "Request processed",
            "Connection established",
        ]
        
        for msg in safe_messages:
            record = LogRecord(name="test", level=INFO, msg=msg)
            assert filter_.filter(record) is True, f"Should pass: {msg}"


class TestRegexFilterComplexPatterns:
    """Test RegexFilter with complex regex patterns"""

    def test_digit_pattern(self):
        """Test pattern matching digits"""
        filter_ = RegexFilter(pattern=r"\d{3}-\d{4}")
        
        record1 = LogRecord(name="test", level=INFO, msg="Phone: 123-4567")
        record2 = LogRecord(name="test", level=INFO, msg="No phone number")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is False

    def test_email_pattern(self):
        """Test pattern matching email-like strings"""
        filter_ = RegexFilter(pattern=r"\S+@\S+\.\S+")
        
        record1 = LogRecord(name="test", level=INFO, msg="Contact: user@example.com")
        record2 = LogRecord(name="test", level=INFO, msg="No email here")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is False

    def test_ip_address_pattern(self):
        """Test pattern matching IP addresses"""
        filter_ = RegexFilter(pattern=r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        
        record1 = LogRecord(name="test", level=INFO, msg="Server: 192.168.1.1")
        record2 = LogRecord(name="test", level=INFO, msg="Server: localhost")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is False

    def test_start_anchor(self):
        """Test pattern with start anchor"""
        filter_ = RegexFilter(pattern=r"^ERROR:")
        
        record1 = LogRecord(name="test", level=INFO, msg="ERROR: Something failed")
        record2 = LogRecord(name="test", level=INFO, msg="This is not an ERROR: message")
        
        assert filter_.filter(record1) is True
        assert filter_.filter(record2) is False

    def test_alternation(self):
        """Test pattern with alternation"""
        filter_ = RegexFilter(pattern=r"(error|warning|critical)", flags=re.IGNORECASE)
        
        for msg in ["Error occurred", "WARNING: low disk", "CRITICAL failure"]:
            record = LogRecord(name="test", level=INFO, msg=msg)
            assert filter_.filter(record) is True
        
        record = LogRecord(name="test", level=INFO, msg="All is well")
        assert filter_.filter(record) is False


class TestRegexFilterFormattedMessage:
    """Test RegexFilter uses formatted message"""

    def test_uses_formatted_message(self):
        """Test that filter uses the formatted message property"""
        filter_ = RegexFilter(pattern=r"User: john")
        
        # Message with formatting args
        record = LogRecord(
            name="test",
            level=INFO,
            msg="User: %s",
            args=("john",)
        )
        
        # The formatted message should be "User: john"
        assert filter_.filter(record) is True

    def test_formatted_message_with_numbers(self):
        """Test formatted message with number formatting"""
        filter_ = RegexFilter(pattern=r"Count: 42")
        
        record = LogRecord(
            name="test",
            level=INFO,
            msg="Count: %d",
            args=(42,)
        )
        
        assert filter_.filter(record) is True


class TestRegexFilterRepr:
    """Test RegexFilter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        filter_ = RegexFilter(pattern=r"test")
        repr_str = repr(filter_)
        
        assert "RegexFilter" in repr_str

    def test_repr_contains_pattern(self):
        """Test that repr contains pattern"""
        filter_ = RegexFilter(pattern=r"error\d+")
        repr_str = repr(filter_)
        
        # Pattern is escaped in repr, so check for the pattern string
        assert "error" in repr_str
        assert "pattern=" in repr_str

    def test_repr_contains_match_pass(self):
        """Test that repr contains match_pass value"""
        filter1 = RegexFilter(pattern=r"test", match_pass=True)
        filter2 = RegexFilter(pattern=r"test", match_pass=False)
        
        assert "True" in repr(filter1)
        assert "False" in repr(filter2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
