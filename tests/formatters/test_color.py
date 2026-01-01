"""
Test cases for logify.formatters.color module
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from logify.formatters.color import ColorFormatter, Colors, DEFAULT_LEVEL_COLORS
from logify.core.record import LogRecord
from logify.core.levels import DEBUG, INFO, WARNING, ERROR, CRITICAL, LogLevel


class TestColors:
    """Test Colors class constants"""

    def test_reset_code(self):
        """Test RESET code"""
        assert Colors.RESET == "\033[0m"

    def test_basic_colors_exist(self):
        """Test basic color codes exist"""
        assert hasattr(Colors, 'BLACK')
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'YELLOW')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'MAGENTA')
        assert hasattr(Colors, 'CYAN')
        assert hasattr(Colors, 'WHITE')

    def test_bright_colors_exist(self):
        """Test bright color codes exist"""
        assert hasattr(Colors, 'BRIGHT_RED')
        assert hasattr(Colors, 'BRIGHT_GREEN')
        assert hasattr(Colors, 'BRIGHT_YELLOW')
        assert hasattr(Colors, 'BRIGHT_BLUE')

    def test_style_codes_exist(self):
        """Test style codes exist"""
        assert hasattr(Colors, 'BOLD')
        assert hasattr(Colors, 'DIM')
        assert hasattr(Colors, 'ITALIC')
        assert hasattr(Colors, 'UNDERLINE')

    def test_color_codes_format(self):
        """Test color codes are ANSI escape sequences"""
        assert Colors.RED.startswith("\033[")
        assert Colors.GREEN.startswith("\033[")
        assert Colors.BOLD.startswith("\033[")


class TestDefaultLevelColors:
    """Test DEFAULT_LEVEL_COLORS mapping"""

    def test_debug_color(self):
        """Test DEBUG level color"""
        assert DEBUG in DEFAULT_LEVEL_COLORS
        assert DEFAULT_LEVEL_COLORS[DEBUG] == Colors.CYAN

    def test_info_color(self):
        """Test INFO level color"""
        assert INFO in DEFAULT_LEVEL_COLORS
        assert DEFAULT_LEVEL_COLORS[INFO] == Colors.GREEN

    def test_warning_color(self):
        """Test WARNING level color"""
        assert WARNING in DEFAULT_LEVEL_COLORS
        assert DEFAULT_LEVEL_COLORS[WARNING] == Colors.YELLOW

    def test_error_color(self):
        """Test ERROR level color"""
        assert ERROR in DEFAULT_LEVEL_COLORS
        assert DEFAULT_LEVEL_COLORS[ERROR] == Colors.RED

    def test_critical_color(self):
        """Test CRITICAL level color"""
        assert CRITICAL in DEFAULT_LEVEL_COLORS
        # CRITICAL uses bright red + bold
        assert Colors.BRIGHT_RED in DEFAULT_LEVEL_COLORS[CRITICAL]
        assert Colors.BOLD in DEFAULT_LEVEL_COLORS[CRITICAL]


class TestColorFormatterInit:
    """Test ColorFormatter initialization"""

    def test_default_init(self):
        """Test default initialization"""
        formatter = ColorFormatter()
        
        assert formatter._colorize_message is True
        assert formatter._colorize_level is True
        assert formatter._force_colors is False

    def test_custom_level_colors(self):
        """Test initialization with custom level colors"""
        custom_colors = {DEBUG: Colors.BLUE, INFO: Colors.MAGENTA}
        formatter = ColorFormatter(level_colors=custom_colors)
        
        assert formatter._level_colors == custom_colors

    def test_colorize_message_false(self):
        """Test initialization with colorize_message=False"""
        formatter = ColorFormatter(colorize_message=False)
        
        assert formatter._colorize_message is False

    def test_colorize_level_false(self):
        """Test initialization with colorize_level=False"""
        formatter = ColorFormatter(colorize_level=False)
        
        assert formatter._colorize_level is False

    def test_force_colors(self):
        """Test initialization with force_colors=True"""
        formatter = ColorFormatter(force_colors=True)
        
        assert formatter._force_colors is True

    def test_custom_format(self):
        """Test initialization with custom format"""
        custom_fmt = "%(levelname)s: %(message)s"
        formatter = ColorFormatter(fmt=custom_fmt)
        
        assert formatter._fmt == custom_fmt

    def test_custom_date_format(self):
        """Test initialization with custom date format"""
        custom_datefmt = "%H:%M:%S"
        formatter = ColorFormatter(datefmt=custom_datefmt)
        
        assert formatter._datefmt == custom_datefmt


class TestColorFormatterGetLevelColor:
    """Test ColorFormatter._get_level_color() method"""

    def test_get_color_for_known_level(self):
        """Test getting color for known level"""
        formatter = ColorFormatter(force_colors=True)
        
        assert formatter._get_level_color(DEBUG) == Colors.CYAN
        assert formatter._get_level_color(INFO) == Colors.GREEN
        assert formatter._get_level_color(WARNING) == Colors.YELLOW
        assert formatter._get_level_color(ERROR) == Colors.RED

    def test_get_color_for_unknown_level(self):
        """Test getting color for unknown level returns empty string"""
        formatter = ColorFormatter(force_colors=True)
        
        assert formatter._get_level_color(999) == ""


class TestColorFormatterColorize:
    """Test ColorFormatter._colorize() method"""

    def test_colorize_adds_color_codes(self):
        """Test that _colorize adds color codes"""
        formatter = ColorFormatter(force_colors=True)
        
        result = formatter._colorize("Hello", Colors.RED)
        
        assert result.startswith(Colors.RED)
        assert result.endswith(Colors.RESET)
        assert "Hello" in result

    def test_colorize_with_empty_color(self):
        """Test that _colorize with empty color returns original text"""
        formatter = ColorFormatter(force_colors=True)
        
        result = formatter._colorize("Hello", "")
        
        assert result == "Hello"

    def test_colorize_format(self):
        """Test exact colorize format"""
        formatter = ColorFormatter(force_colors=True)
        
        result = formatter._colorize("Test", Colors.GREEN)
        
        assert result == f"{Colors.GREEN}Test{Colors.RESET}"


class TestColorFormatterFormat:
    """Test ColorFormatter.format() method"""

    def test_format_with_force_colors(self):
        """Test format with force_colors=True includes color codes"""
        formatter = ColorFormatter(
            fmt="%(levelname)s: %(message)s",
            force_colors=True
        )
        record = LogRecord(name="test", level=INFO, msg="Hello")
        
        result = formatter.format(record)
        
        # Should contain ANSI escape codes
        assert "\033[" in result
        assert Colors.RESET in result

    def test_format_colorizes_level(self):
        """Test that format colorizes level name"""
        formatter = ColorFormatter(
            fmt="%(levelname)s",
            force_colors=True,
            colorize_level=True,
            colorize_message=False
        )
        record = LogRecord(name="test", level=INFO, msg="Test")
        
        result = formatter.format(record)
        
        assert Colors.GREEN in result  # INFO is green
        assert "INFO" in result

    def test_format_colorizes_message(self):
        """Test that format colorizes message"""
        formatter = ColorFormatter(
            fmt="%(message)s",
            force_colors=True,
            colorize_level=False,
            colorize_message=True
        )
        record = LogRecord(name="test", level=WARNING, msg="Warning!")
        
        result = formatter.format(record)
        
        assert Colors.YELLOW in result  # WARNING is yellow
        assert "Warning!" in result

    def test_format_without_colorize_level(self):
        """Test format with colorize_level=False"""
        formatter = ColorFormatter(
            fmt="%(levelname)s: %(message)s",
            force_colors=True,
            colorize_level=False,
            colorize_message=True
        )
        record = LogRecord(name="test", level=ERROR, msg="Error!")
        
        result = formatter.format(record)
        
        # Level should not have color codes around it specifically
        # but message should
        assert "ERROR" in result

    def test_format_without_colorize_message(self):
        """Test format with colorize_message=False"""
        formatter = ColorFormatter(
            fmt="%(levelname)s: %(message)s",
            force_colors=True,
            colorize_level=True,
            colorize_message=False
        )
        record = LogRecord(name="test", level=INFO, msg="Plain message")
        
        result = formatter.format(record)
        
        assert "Plain message" in result

    def test_format_all_levels_have_colors(self):
        """Test that all log levels have appropriate colors"""
        formatter = ColorFormatter(fmt="%(levelname)s", force_colors=True)
        
        level_colors = [
            (DEBUG, Colors.CYAN),
            (INFO, Colors.GREEN),
            (WARNING, Colors.YELLOW),
            (ERROR, Colors.RED),
        ]
        
        for level, expected_color in level_colors:
            record = LogRecord(name="test", level=level, msg="Test")
            result = formatter.format(record)
            
            assert expected_color in result, f"Level {level} should have color {expected_color}"


class TestColorFormatterSupportsColor:
    """Test ColorFormatter._supports_color() method"""

    def test_force_colors_always_supports(self):
        """Test that force_colors=True always returns True"""
        formatter = ColorFormatter(force_colors=True)
        
        assert formatter._supports_color() is True

    def test_no_force_colors_checks_tty(self):
        """Test that without force_colors, TTY is checked"""
        formatter = ColorFormatter(force_colors=False)
        
        # We can't easily test TTY detection, but we can verify the method exists
        result = formatter._supports_color()
        assert isinstance(result, bool)


class TestColorFormatterNoColorFallback:
    """Test ColorFormatter falls back to plain text when colors not supported"""

    @patch.object(ColorFormatter, '_supports_color', return_value=False)
    def test_format_without_color_support(self, mock_supports):
        """Test format falls back to parent when colors not supported"""
        formatter = ColorFormatter(fmt="%(levelname)s: %(message)s")
        record = LogRecord(name="test", level=INFO, msg="Plain text")
        
        result = formatter.format(record)
        
        # Should not contain ANSI codes
        assert "\033[" not in result
        assert result == "INFO: Plain text"


class TestColorFormatterSetLevelColor:
    """Test ColorFormatter.set_level_color() method"""

    def test_set_level_color(self):
        """Test setting a custom level color"""
        formatter = ColorFormatter(force_colors=True)
        
        formatter.set_level_color(INFO, Colors.MAGENTA)
        
        assert formatter._level_colors[INFO] == Colors.MAGENTA

    def test_set_level_color_affects_output(self):
        """Test that set_level_color affects format output"""
        formatter = ColorFormatter(
            fmt="%(levelname)s",
            force_colors=True,
            colorize_level=True
        )
        formatter.set_level_color(INFO, Colors.BLUE)
        
        record = LogRecord(name="test", level=INFO, msg="Test")
        result = formatter.format(record)
        
        assert Colors.BLUE in result


class TestColorFormatterWithException:
    """Test ColorFormatter with exception info"""

    def test_format_exception_in_red(self):
        """Test that exception is formatted in red"""
        formatter = ColorFormatter(
            fmt="%(levelname)s: %(message)s",
            force_colors=True
        )
        
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
        
        # Exception should be in red
        assert Colors.RED in result
        assert "ValueError" in result


class TestColorFormatterRepr:
    """Test ColorFormatter.__repr__() method"""

    def test_repr_contains_class_name(self):
        """Test that repr contains class name"""
        formatter = ColorFormatter()
        repr_str = repr(formatter)
        
        assert "ColorFormatter" in repr_str

    def test_repr_contains_colorize_message(self):
        """Test that repr contains colorize_message value"""
        formatter = ColorFormatter(colorize_message=False)
        repr_str = repr(formatter)
        
        assert "colorize_message=" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
