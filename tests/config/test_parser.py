"""
Tests for logify.config.parser module

Tests for ConfigParser class
"""

import json
import tempfile
import pytest
from pathlib import Path

from logify.config.parser import ConfigParser
from logify.config.loader import ConfigLoader
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR
from logify.core.manager import LoggerManager
from logify.formatters.text import TextFormatter
from logify.formatters.json_formatter import JsonFormatter
from logify.formatters.color import ColorFormatter
from logify.filters.level_filter import LevelFilter
from logify.filters.regex_filter import RegexFilter
from logify.filters.context_filter import ContextFilter
from logify.handlers.console import ConsoleHandler
from logify.handlers.file import FileHandler
from logify.handlers.rotating import RotatingFileHandler, TimedRotatingFileHandler
from logify.formatters.base import BaseFormatter
from logify.handlers.base import BaseHandler
from logify.filters.base import BaseFilter


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_logger_manager():
    """Reset LoggerManager singleton before each test"""
    # Store original state
    manager = LoggerManager()
    original_loggers = manager._loggers.copy()
    
    yield
    
    # Restore original state
    manager._loggers.clear()
    manager._loggers.update(original_loggers)


# ============================================
# ConfigParser Initialization Tests
# ============================================

class TestConfigParserInit:
    """Test ConfigParser initialization"""
    
    def test_default_initialization(self):
        """Test default initialization without config"""
        parser = ConfigParser()
        assert parser._config == {}
        assert parser._formatters == {}
        assert parser._filters == {}
        assert parser._handlers == {}
    
    def test_initialization_with_dict(self):
        """Test initialization with dictionary config"""
        config = {'version': 1, 'level': 'DEBUG'}
        parser = ConfigParser(config)
        assert parser._config == config
    
    def test_initialization_with_config_loader(self):
        """Test initialization with ConfigLoader"""
        loader = ConfigLoader()
        loader.load_from_dict({'version': 1, 'level': 'DEBUG'})
        
        parser = ConfigParser(loader)
        assert parser._config['version'] == 1
        assert parser._config['level'] == 'DEBUG'


# ============================================
# ConfigParser.parse Tests
# ============================================

class TestConfigParserParse:
    """Test ConfigParser parse method"""
    
    def test_parse_empty_config(self):
        """Test parsing empty config"""
        parser = ConfigParser({})
        parser.parse()  # Should not raise
    
    def test_parse_calls_all_parsers(self):
        """Test parse calls all component parsers"""
        config = {
            'formatters': {'simple': {'class': 'TextFormatter'}},
            'filters': {'level': {'class': 'LevelFilter'}},
            'handlers': {'console': {'class': 'ConsoleHandler'}},
            'loggers': {}
        }
        parser = ConfigParser(config)
        parser.parse()
        
        assert 'simple' in parser._formatters
        assert 'level' in parser._filters
        assert 'console' in parser._handlers


# ============================================
# ConfigParser Formatter Tests
# ============================================

class TestConfigParserFormatters:
    """Test ConfigParser formatter parsing"""
    
    def test_create_text_formatter(self):
        """Test creating TextFormatter"""
        config = {
            'formatters': {
                'simple': {'class': 'TextFormatter'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        formatter = parser.get_formatter('simple')
        assert isinstance(formatter, TextFormatter)
    
    def test_create_text_formatter_with_format(self):
        """Test creating TextFormatter with format string"""
        config = {
            'formatters': {
                'simple': {
                    'class': 'TextFormatter',
                    'format': '%(message)s'
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        formatter = parser.get_formatter('simple')
        assert isinstance(formatter, TextFormatter)
    
    def test_create_json_formatter(self):
        """Test creating JsonFormatter"""
        config = {
            'formatters': {
                'json': {'class': 'JsonFormatter'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        formatter = parser.get_formatter('json')
        assert isinstance(formatter, JsonFormatter)
    
    def test_create_color_formatter(self):
        """Test creating ColorFormatter"""
        config = {
            'formatters': {
                'color': {'class': 'ColorFormatter'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        formatter = parser.get_formatter('color')
        assert isinstance(formatter, ColorFormatter)
    
    def test_unknown_formatter_raises_error(self):
        """Test unknown formatter class raises error"""
        config = {
            'formatters': {
                'unknown': {'class': 'UnknownFormatter'}
            }
        }
        parser = ConfigParser(config)
        
        with pytest.raises(ValueError, match="Unknown formatter class"):
            parser.parse()
    
    def test_default_formatter_class(self):
        """Test default formatter class is TextFormatter"""
        config = {
            'formatters': {
                'default': {}  # No class specified
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        formatter = parser.get_formatter('default')
        assert isinstance(formatter, TextFormatter)
    
    def test_get_nonexistent_formatter(self):
        """Test getting nonexistent formatter returns None"""
        parser = ConfigParser({})
        parser.parse()
        
        assert parser.get_formatter('missing') is None


# ============================================
# ConfigParser Filter Tests
# ============================================

class TestConfigParserFilters:
    """Test ConfigParser filter parsing"""
    
    def test_create_level_filter(self):
        """Test creating LevelFilter"""
        config = {
            'filters': {
                'level': {'class': 'LevelFilter', 'level': 'INFO'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        filter_ = parser.get_filter('level')
        assert isinstance(filter_, LevelFilter)
        assert filter_.level == INFO
    
    def test_create_level_filter_with_int(self):
        """Test creating LevelFilter with int level"""
        config = {
            'filters': {
                'level': {'class': 'LevelFilter', 'level': 20}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        filter_ = parser.get_filter('level')
        assert filter_.level == 20
    
    def test_create_regex_filter(self):
        """Test creating RegexFilter"""
        config = {
            'filters': {
                'regex': {'class': 'RegexFilter', 'pattern': r'error\d+'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        filter_ = parser.get_filter('regex')
        assert isinstance(filter_, RegexFilter)
    
    def test_create_context_filter(self):
        """Test creating ContextFilter"""
        config = {
            'filters': {
                'context': {
                    'class': 'ContextFilter',
                    'allowed_names': {'myapp', 'mymodule'}
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        filter_ = parser.get_filter('context')
        assert isinstance(filter_, ContextFilter)
    
    def test_unknown_filter_raises_error(self):
        """Test unknown filter class raises error"""
        config = {
            'filters': {
                'unknown': {'class': 'UnknownFilter'}
            }
        }
        parser = ConfigParser(config)
        
        with pytest.raises(ValueError, match="Unknown filter class"):
            parser.parse()
    
    def test_default_filter_class(self):
        """Test default filter class is LevelFilter"""
        config = {
            'filters': {
                'default': {}  # No class specified
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        filter_ = parser.get_filter('default')
        assert isinstance(filter_, LevelFilter)
    
    def test_get_nonexistent_filter(self):
        """Test getting nonexistent filter returns None"""
        parser = ConfigParser({})
        parser.parse()
        
        assert parser.get_filter('missing') is None


# ============================================
# ConfigParser Handler Tests
# ============================================

class TestConfigParserHandlers:
    """Test ConfigParser handler parsing"""
    
    def test_create_console_handler(self):
        """Test creating ConsoleHandler"""
        config = {
            'handlers': {
                'console': {'class': 'ConsoleHandler'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('console')
        assert isinstance(handler, ConsoleHandler)
    
    def test_create_console_handler_with_level(self):
        """Test creating ConsoleHandler with level"""
        config = {
            'handlers': {
                'console': {'class': 'ConsoleHandler', 'level': 'WARNING'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('console')
        assert handler.level == WARNING
    
    def test_create_file_handler(self, temp_dir):
        """Test creating FileHandler"""
        log_file = temp_dir / "app.log"
        config = {
            'handlers': {
                'file': {
                    'class': 'FileHandler',
                    'filename': str(log_file),
                    'delay': True
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('file')
        try:
            assert isinstance(handler, FileHandler)
        finally:
            handler.close()
    
    def test_create_rotating_file_handler(self, temp_dir):
        """Test creating RotatingFileHandler"""
        log_file = temp_dir / "app.log"
        config = {
            'handlers': {
                'rotating': {
                    'class': 'RotatingFileHandler',
                    'filename': str(log_file),
                    'max_bytes': 10000,
                    'backup_count': 3
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('rotating')
        try:
            assert isinstance(handler, RotatingFileHandler)
            assert handler.max_bytes == 10000
            assert handler.backup_count == 3
        finally:
            handler.close()
    
    def test_create_timed_rotating_handler(self, temp_dir):
        """Test creating TimedRotatingFileHandler"""
        log_file = temp_dir / "app.log"
        config = {
            'handlers': {
                'timed': {
                    'class': 'TimedRotatingFileHandler',
                    'filename': str(log_file),
                    'when': 'D',
                    'backup_count': 7
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('timed')
        try:
            assert isinstance(handler, TimedRotatingFileHandler)
        finally:
            handler.close()
    
    def test_handler_with_formatter(self):
        """Test handler with formatter reference"""
        config = {
            'formatters': {
                'simple': {'class': 'TextFormatter', 'format': '%(message)s'}
            },
            'handlers': {
                'console': {
                    'class': 'ConsoleHandler',
                    'formatter': 'simple'
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('console')
        assert handler.formatter is parser.get_formatter('simple')
    
    def test_handler_with_filters(self):
        """Test handler with filter references"""
        config = {
            'filters': {
                'level': {'class': 'LevelFilter', 'level': 'INFO'}
            },
            'handlers': {
                'console': {
                    'class': 'ConsoleHandler',
                    'filters': ['level']
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('console')
        assert len(handler._filter_chain._filters) == 1
    
    def test_unknown_handler_raises_error(self):
        """Test unknown handler class raises error"""
        config = {
            'handlers': {
                'unknown': {'class': 'UnknownHandler'}
            }
        }
        parser = ConfigParser(config)
        
        with pytest.raises(ValueError, match="Unknown handler class"):
            parser.parse()
    
    def test_default_handler_class(self):
        """Test default handler class is ConsoleHandler"""
        config = {
            'handlers': {
                'default': {}  # No class specified
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        handler = parser.get_handler('default')
        assert isinstance(handler, ConsoleHandler)
    
    def test_get_nonexistent_handler(self):
        """Test getting nonexistent handler returns None"""
        parser = ConfigParser({})
        parser.parse()
        
        assert parser.get_handler('missing') is None


# ============================================
# ConfigParser Logger Tests
# ============================================

class TestConfigParserLoggers:
    """Test ConfigParser logger parsing"""
    
    def test_configure_logger_level(self):
        """Test configuring logger level"""
        config = {
            'loggers': {
                'myapp': {'level': 'WARNING'}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        from logify.core.manager import get_logger
        logger = get_logger('myapp')
        assert logger.level == WARNING
    
    def test_configure_logger_with_handlers(self):
        """Test configuring logger with handlers"""
        config = {
            'handlers': {
                'console': {'class': 'ConsoleHandler'}
            },
            'loggers': {
                'myapp': {
                    'level': 'DEBUG',
                    'handlers': ['console']
                }
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        from logify.core.manager import get_logger
        logger = get_logger('myapp')
        assert len(logger.handlers) >= 1
    
    def test_configure_logger_propagate(self):
        """Test configuring logger propagate flag"""
        config = {
            'loggers': {
                'myapp.module': {'propagate': False}
            }
        }
        parser = ConfigParser(config)
        parser.parse()
        
        from logify.core.manager import get_logger
        logger = get_logger('myapp.module')
        assert logger.propagate is False


# ============================================
# ConfigParser._parse_level Tests
# ============================================

class TestConfigParserParseLevel:
    """Test ConfigParser._parse_level method"""
    
    def test_parse_level_string(self):
        """Test parsing level from string"""
        parser = ConfigParser()
        
        assert parser._parse_level('DEBUG') == DEBUG
        assert parser._parse_level('INFO') == INFO
        assert parser._parse_level('WARNING') == WARNING
        assert parser._parse_level('ERROR') == ERROR
    
    def test_parse_level_int(self):
        """Test parsing level from int"""
        parser = ConfigParser()
        
        assert parser._parse_level(10) == 10
        assert parser._parse_level(20) == 20
    
    def test_parse_level_unknown_defaults_to_debug(self):
        """Test unknown level defaults to DEBUG"""
        parser = ConfigParser()
        
        assert parser._parse_level('UNKNOWN') == DEBUG


# ============================================
# ConfigParser.from_file Tests
# ============================================

class TestConfigParserFromFile:
    """Test ConfigParser.from_file class method"""
    
    def test_from_json_file(self, temp_dir):
        """Test creating parser from JSON file"""
        config_file = temp_dir / "config.json"
        config = {
            'formatters': {
                'simple': {'class': 'TextFormatter'}
            }
        }
        config_file.write_text(json.dumps(config))
        
        parser = ConfigParser.from_file(str(config_file))
        
        assert parser.get_formatter('simple') is not None


# ============================================
# ConfigParser.register_* Tests
# ============================================

class TestConfigParserRegister:
    """Test ConfigParser registration methods"""
    
    def test_register_custom_formatter(self):
        """Test registering custom formatter class"""
        class CustomFormatter(BaseFormatter):
            def format(self, record):
                return "custom"
        
        ConfigParser.register_formatter('CustomFormatter', CustomFormatter)
        
        try:
            config = {
                'formatters': {
                    'custom': {'class': 'CustomFormatter'}
                }
            }
            parser = ConfigParser(config)
            parser.parse()
            
            formatter = parser.get_formatter('custom')
            assert isinstance(formatter, CustomFormatter)
        finally:
            # Cleanup
            del ConfigParser.FORMATTER_CLASSES['CustomFormatter']
    
    def test_register_custom_handler(self):
        """Test registering custom handler class"""
        class CustomHandler(BaseHandler):
            def emit(self, record):
                pass
        
        ConfigParser.register_handler('CustomHandler', CustomHandler)
        
        try:
            config = {
                'handlers': {
                    'custom': {'class': 'CustomHandler'}
                }
            }
            parser = ConfigParser(config)
            parser.parse()
            
            handler = parser.get_handler('custom')
            assert isinstance(handler, CustomHandler)
        finally:
            # Cleanup
            del ConfigParser.HANDLER_CLASSES['CustomHandler']
    
    def test_register_custom_filter(self):
        """Test registering custom filter class"""
        class CustomFilter(BaseFilter):
            def filter(self, record):
                return True
        
        ConfigParser.register_filter('CustomFilter', CustomFilter)
        
        try:
            config = {
                'filters': {
                    'custom': {'class': 'CustomFilter'}
                }
            }
            parser = ConfigParser(config)
            parser.parse()
            
            filter_ = parser.get_filter('custom')
            assert isinstance(filter_, CustomFilter)
        finally:
            # Cleanup
            del ConfigParser.FILTER_CLASSES['CustomFilter']


# ============================================
# ConfigParser.__repr__ Tests
# ============================================

class TestConfigParserRepr:
    """Test ConfigParser __repr__ method"""
    
    def test_repr_empty(self):
        """Test repr with empty parser"""
        parser = ConfigParser({})
        repr_str = repr(parser)
        
        assert 'ConfigParser' in repr_str
        assert 'formatters=0' in repr_str
        assert 'filters=0' in repr_str
        assert 'handlers=0' in repr_str
    
    def test_repr_with_components(self):
        """Test repr with parsed components"""
        config = {
            'formatters': {'simple': {'class': 'TextFormatter'}},
            'filters': {'level': {'class': 'LevelFilter'}},
            'handlers': {'console': {'class': 'ConsoleHandler'}}
        }
        parser = ConfigParser(config)
        parser.parse()
        
        repr_str = repr(parser)
        assert 'formatters=1' in repr_str
        assert 'filters=1' in repr_str
        assert 'handlers=1' in repr_str


# ============================================
# ConfigParser Integration Tests
# ============================================

class TestConfigParserIntegration:
    """Integration tests for ConfigParser"""
    
    def test_complete_config_parsing(self, temp_dir):
        """Test complete configuration parsing"""
        log_file = temp_dir / "app.log"
        config = {
            'version': 1,
            'formatters': {
                'simple': {
                    'class': 'TextFormatter',
                    'format': '%(levelname)s - %(message)s'
                },
                'json': {
                    'class': 'JsonFormatter'
                }
            },
            'filters': {
                'info_and_above': {
                    'class': 'LevelFilter',
                    'level': 'INFO'
                }
            },
            'handlers': {
                'console': {
                    'class': 'ConsoleHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple'
                },
                'file': {
                    'class': 'FileHandler',
                    'filename': str(log_file),
                    'level': 'INFO',
                    'formatter': 'json',
                    'filters': ['info_and_above'],
                    'delay': True
                }
            },
            'loggers': {
                'myapp': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file']
                }
            }
        }
        
        parser = ConfigParser(config)
        parser.parse()
        
        # Verify formatters
        assert isinstance(parser.get_formatter('simple'), TextFormatter)
        assert isinstance(parser.get_formatter('json'), JsonFormatter)
        
        # Verify filters
        assert isinstance(parser.get_filter('info_and_above'), LevelFilter)
        
        # Verify handlers
        console = parser.get_handler('console')
        file_handler = parser.get_handler('file')
        try:
            assert isinstance(console, ConsoleHandler)
            assert isinstance(file_handler, FileHandler)
            assert file_handler.formatter is parser.get_formatter('json')
            assert len(file_handler._filter_chain._filters) == 1
        finally:
            file_handler.close()
    
    def test_config_from_json_file(self, temp_dir):
        """Test loading complete config from JSON file"""
        config_file = temp_dir / "logging.json"
        config = {
            'formatters': {
                'simple': {'class': 'TextFormatter'}
            },
            'handlers': {
                'console': {
                    'class': 'ConsoleHandler',
                    'formatter': 'simple'
                }
            }
        }
        config_file.write_text(json.dumps(config))
        
        parser = ConfigParser.from_file(str(config_file))
        
        assert parser.get_formatter('simple') is not None
        assert parser.get_handler('console') is not None
