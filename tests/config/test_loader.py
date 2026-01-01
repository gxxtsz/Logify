"""
Tests for logify.config.loader module

Tests for ConfigLoader class
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from logify.config.loader import ConfigLoader


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def loader():
    """Create a fresh ConfigLoader"""
    return ConfigLoader()


# ============================================
# ConfigLoader Initialization Tests
# ============================================

class TestConfigLoaderInit:
    """Test ConfigLoader initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        loader = ConfigLoader()
        assert loader.config == {}
    
    def test_config_property_returns_copy(self):
        """Test config property returns a copy"""
        loader = ConfigLoader()
        loader.load_from_dict({'key': 'value'})
        config = loader.config
        config['new_key'] = 'new_value'
        assert 'new_key' not in loader.config


# ============================================
# ConfigLoader.load_from_dict Tests
# ============================================

class TestConfigLoaderLoadFromDict:
    """Test ConfigLoader load_from_dict method"""
    
    def test_load_simple_dict(self, loader):
        """Test loading simple dictionary"""
        config = {'level': 'DEBUG', 'name': 'test'}
        result = loader.load_from_dict(config)
        
        assert result is loader  # Returns self for chaining
        assert loader.config == config
    
    def test_load_nested_dict(self, loader):
        """Test loading nested dictionary"""
        config = {
            'handlers': {
                'console': {'level': 'DEBUG'},
                'file': {'level': 'INFO'}
            }
        }
        loader.load_from_dict(config)
        assert loader.config['handlers']['console']['level'] == 'DEBUG'
    
    def test_load_updates_existing(self, loader):
        """Test load updates existing config"""
        loader.load_from_dict({'a': 1, 'b': 2})
        loader.load_from_dict({'b': 3, 'c': 4})
        
        assert loader.config == {'a': 1, 'b': 3, 'c': 4}
    
    def test_chain_loading(self, loader):
        """Test chain loading"""
        loader.load_from_dict({'a': 1}).load_from_dict({'b': 2})
        assert loader.config == {'a': 1, 'b': 2}


# ============================================
# ConfigLoader.load_from_file Tests - JSON
# ============================================

class TestConfigLoaderLoadFromFileJson:
    """Test ConfigLoader load_from_file with JSON files"""
    
    def test_load_json_file(self, loader, temp_dir):
        """Test loading JSON config file"""
        config_file = temp_dir / "config.json"
        config = {'level': 'DEBUG', 'handlers': ['console']}
        config_file.write_text(json.dumps(config))
        
        result = loader.load_from_file(config_file)
        
        assert result is loader
        assert loader.config == config
    
    def test_load_json_nested(self, loader, temp_dir):
        """Test loading nested JSON config"""
        config_file = temp_dir / "config.json"
        config = {
            'formatters': {
                'simple': {'format': '%(message)s'}
            }
        }
        config_file.write_text(json.dumps(config))
        
        loader.load_from_file(config_file)
        assert loader.config['formatters']['simple']['format'] == '%(message)s'
    
    def test_load_json_unicode(self, loader, temp_dir):
        """Test loading JSON with Unicode content"""
        config_file = temp_dir / "config.json"
        config = {'message': '日志配置 🎉'}
        config_file.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
        
        loader.load_from_file(config_file)
        assert loader.config['message'] == '日志配置 🎉'
    
    def test_load_json_with_string_path(self, loader, temp_dir):
        """Test loading JSON with string path"""
        config_file = temp_dir / "config.json"
        config_file.write_text('{"key": "value"}')
        
        loader.load_from_file(str(config_file))
        assert loader.config['key'] == 'value'


# ============================================
# ConfigLoader.load_from_file Tests - YAML
# ============================================

class TestConfigLoaderLoadFromFileYaml:
    """Test ConfigLoader load_from_file with YAML files"""
    
    def test_load_yaml_file(self, loader, temp_dir):
        """Test loading YAML config file"""
        pytest.importorskip('yaml')
        
        config_file = temp_dir / "config.yaml"
        config_file.write_text("level: DEBUG\nname: test\n")
        
        loader.load_from_file(config_file)
        assert loader.config['level'] == 'DEBUG'
        assert loader.config['name'] == 'test'
    
    def test_load_yml_extension(self, loader, temp_dir):
        """Test loading .yml extension file"""
        pytest.importorskip('yaml')
        
        config_file = temp_dir / "config.yml"
        config_file.write_text("key: value\n")
        
        loader.load_from_file(config_file)
        assert loader.config['key'] == 'value'
    
    def test_load_yaml_nested(self, loader, temp_dir):
        """Test loading nested YAML config"""
        pytest.importorskip('yaml')
        
        config_file = temp_dir / "config.yaml"
        yaml_content = """
handlers:
  console:
    level: DEBUG
  file:
    level: INFO
"""
        config_file.write_text(yaml_content)
        
        loader.load_from_file(config_file)
        assert loader.config['handlers']['console']['level'] == 'DEBUG'
    
    def test_load_yaml_empty_file(self, loader, temp_dir):
        """Test loading empty YAML file"""
        pytest.importorskip('yaml')
        
        config_file = temp_dir / "config.yaml"
        config_file.write_text("")
        
        loader.load_from_file(config_file)
        assert loader.config == {}


# ============================================
# ConfigLoader.load_from_file Tests - TOML
# ============================================

class TestConfigLoaderLoadFromFileToml:
    """Test ConfigLoader load_from_file with TOML files"""
    
    def test_load_toml_file(self, loader, temp_dir):
        """Test loading TOML config file"""
        # Skip if neither tomllib nor toml is available
        try:
            import tomllib
        except ImportError:
            try:
                import toml
            except ImportError:
                pytest.skip("TOML support not available")
        
        config_file = temp_dir / "config.toml"
        config_file.write_text('level = "DEBUG"\nname = "test"\n')
        
        loader.load_from_file(config_file)
        assert loader.config['level'] == 'DEBUG'
        assert loader.config['name'] == 'test'


# ============================================
# ConfigLoader.load_from_file Error Tests
# ============================================

class TestConfigLoaderLoadFromFileErrors:
    """Test ConfigLoader load_from_file error handling"""
    
    def test_file_not_found(self, loader):
        """Test FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            loader.load_from_file("/nonexistent/config.json")
    
    def test_unsupported_format(self, loader, temp_dir):
        """Test ValueError for unsupported format"""
        config_file = temp_dir / "config.xyz"
        config_file.write_text("content")
        
        with pytest.raises(ValueError, match="Unsupported config format"):
            loader.load_from_file(config_file)


# ============================================
# ConfigLoader.load_from_env Tests
# ============================================

class TestConfigLoaderLoadFromEnv:
    """Test ConfigLoader load_from_env method"""
    
    def test_load_with_prefix(self, loader):
        """Test loading env vars with prefix"""
        with patch.dict(os.environ, {'LOGIFY_LEVEL': 'DEBUG', 'LOGIFY_NAME': 'test'}):
            result = loader.load_from_env(prefix='LOGIFY_')
        
        assert result is loader
        assert loader.config['level'] == 'DEBUG'
        assert loader.config['name'] == 'test'
    
    def test_load_with_custom_mapping(self, loader):
        """Test loading env vars with custom mapping"""
        with patch.dict(os.environ, {'MY_LOG_LEVEL': 'INFO', 'MY_LOG_FILE': 'app.log'}):
            loader.load_from_env(mapping={
                'MY_LOG_LEVEL': 'level',
                'MY_LOG_FILE': 'filename'
            })
        
        assert loader.config['level'] == 'INFO'
        assert loader.config['filename'] == 'app.log'
    
    def test_load_nested_keys(self, loader):
        """Test loading nested keys from env vars"""
        with patch.dict(os.environ, {'MY_HANDLER_LEVEL': 'DEBUG'}):
            loader.load_from_env(mapping={
                'MY_HANDLER_LEVEL': 'handlers.console.level'
            })
        
        assert loader.config['handlers']['console']['level'] == 'DEBUG'
    
    def test_parse_boolean_true(self, loader):
        """Test parsing boolean true values"""
        # Note: '1' gets parsed as int by JSON parser before boolean check
        test_values = ['true', 'True', 'TRUE', 'yes', 'YES']
        for val in test_values:
            loader.clear()
            with patch.dict(os.environ, {'LOGIFY_ENABLED': val}):
                loader.load_from_env()
            assert loader.config['enabled'] is True, f"Failed for {val}"
    
    def test_parse_boolean_false(self, loader):
        """Test parsing boolean false values"""
        # Note: '0' gets parsed as int by JSON parser before boolean check
        test_values = ['false', 'False', 'FALSE', 'no', 'NO']
        for val in test_values:
            loader.clear()
            with patch.dict(os.environ, {'LOGIFY_ENABLED': val}):
                loader.load_from_env()
            assert loader.config['enabled'] is False, f"Failed for {val}"
    
    def test_parse_integer(self, loader):
        """Test parsing integer values"""
        with patch.dict(os.environ, {'LOGIFY_PORT': '8080'}):
            loader.load_from_env()
        assert loader.config['port'] == 8080
        assert isinstance(loader.config['port'], int)
    
    def test_parse_float(self, loader):
        """Test parsing float values"""
        with patch.dict(os.environ, {'LOGIFY_TIMEOUT': '5.5'}):
            loader.load_from_env()
        assert loader.config['timeout'] == 5.5
        assert isinstance(loader.config['timeout'], float)
    
    def test_parse_json_array(self, loader):
        """Test parsing JSON array from env var"""
        with patch.dict(os.environ, {'LOGIFY_HANDLERS': '["console", "file"]'}):
            loader.load_from_env()
        assert loader.config['handlers'] == ['console', 'file']
    
    def test_parse_json_object(self, loader):
        """Test parsing JSON object from env var"""
        with patch.dict(os.environ, {'LOGIFY_OPTIONS': '{"debug": true}'}):
            loader.load_from_env()
        assert loader.config['options'] == {'debug': True}
    
    def test_parse_string_fallback(self, loader):
        """Test fallback to string for unparseable values"""
        with patch.dict(os.environ, {'LOGIFY_NAME': 'my-app'}):
            loader.load_from_env()
        assert loader.config['name'] == 'my-app'
        assert isinstance(loader.config['name'], str)


# ============================================
# ConfigLoader.get Tests
# ============================================

class TestConfigLoaderGet:
    """Test ConfigLoader get method"""
    
    def test_get_simple_key(self, loader):
        """Test getting simple key"""
        loader.load_from_dict({'level': 'DEBUG'})
        assert loader.get('level') == 'DEBUG'
    
    def test_get_nested_key(self, loader):
        """Test getting nested key with dot notation"""
        loader.load_from_dict({
            'handlers': {
                'console': {'level': 'DEBUG'}
            }
        })
        assert loader.get('handlers.console.level') == 'DEBUG'
    
    def test_get_missing_key_returns_default(self, loader):
        """Test getting missing key returns default"""
        assert loader.get('missing') is None
        assert loader.get('missing', 'default') == 'default'
    
    def test_get_missing_nested_key(self, loader):
        """Test getting missing nested key"""
        loader.load_from_dict({'a': {'b': 1}})
        assert loader.get('a.c.d') is None
        assert loader.get('a.c.d', 'default') == 'default'
    
    def test_get_partial_nested_key(self, loader):
        """Test getting partial nested structure"""
        loader.load_from_dict({'a': {'b': {'c': 1}}})
        result = loader.get('a.b')
        assert result == {'c': 1}


# ============================================
# ConfigLoader.clear Tests
# ============================================

class TestConfigLoaderClear:
    """Test ConfigLoader clear method"""
    
    def test_clear_removes_all_config(self, loader):
        """Test clear removes all config"""
        loader.load_from_dict({'a': 1, 'b': 2})
        result = loader.clear()
        
        assert result is loader
        assert loader.config == {}
    
    def test_clear_chain_call(self, loader):
        """Test clear with chain call"""
        loader.load_from_dict({'a': 1})
        loader.clear().load_from_dict({'b': 2})
        
        assert loader.config == {'b': 2}


# ============================================
# ConfigLoader.merge Tests
# ============================================

class TestConfigLoaderMerge:
    """Test ConfigLoader merge method"""
    
    def test_merge_simple(self, loader):
        """Test merging simple configs"""
        loader.load_from_dict({'a': 1})
        other = ConfigLoader()
        other.load_from_dict({'b': 2})
        
        result = loader.merge(other)
        
        assert result is loader
        assert loader.config == {'a': 1, 'b': 2}
    
    def test_merge_override(self, loader):
        """Test merge overrides existing values"""
        loader.load_from_dict({'a': 1, 'b': 2})
        other = ConfigLoader()
        other.load_from_dict({'b': 3})
        
        loader.merge(other)
        assert loader.config == {'a': 1, 'b': 3}
    
    def test_merge_deep_nested(self, loader):
        """Test deep merge of nested dicts"""
        loader.load_from_dict({
            'handlers': {
                'console': {'level': 'DEBUG', 'formatter': 'simple'}
            }
        })
        other = ConfigLoader()
        other.load_from_dict({
            'handlers': {
                'console': {'level': 'INFO'},
                'file': {'level': 'DEBUG'}
            }
        })
        
        loader.merge(other)
        
        # Console level should be overridden, formatter preserved
        assert loader.config['handlers']['console']['level'] == 'INFO'
        assert loader.config['handlers']['console']['formatter'] == 'simple'
        # File handler should be added
        assert loader.config['handlers']['file']['level'] == 'DEBUG'


# ============================================
# ConfigLoader.__repr__ Tests
# ============================================

class TestConfigLoaderRepr:
    """Test ConfigLoader __repr__ method"""
    
    def test_repr_empty(self, loader):
        """Test repr with empty config"""
        repr_str = repr(loader)
        assert 'ConfigLoader' in repr_str
        assert 'keys=[]' in repr_str
    
    def test_repr_with_config(self, loader):
        """Test repr with config"""
        loader.load_from_dict({'level': 'DEBUG', 'name': 'test'})
        repr_str = repr(loader)
        assert 'ConfigLoader' in repr_str
        assert 'level' in repr_str or 'name' in repr_str


# ============================================
# ConfigLoader Integration Tests
# ============================================

class TestConfigLoaderIntegration:
    """Integration tests for ConfigLoader"""
    
    def test_complete_workflow(self, temp_dir):
        """Test complete config loading workflow"""
        # Create JSON config file
        config_file = temp_dir / "base.json"
        config_file.write_text(json.dumps({
            'level': 'DEBUG',
            'handlers': {
                'console': {'enabled': True}
            }
        }))
        
        loader = ConfigLoader()
        
        # Load from file
        loader.load_from_file(config_file)
        
        # Override with dict
        loader.load_from_dict({'level': 'INFO'})
        
        # Load from env
        with patch.dict(os.environ, {'LOGIFY_NAME': 'myapp'}):
            loader.load_from_env()
        
        assert loader.get('level') == 'INFO'
        assert loader.get('handlers.console.enabled') is True
        assert loader.get('name') == 'myapp'
    
    def test_multiple_file_merge(self, temp_dir):
        """Test merging multiple config files"""
        base_file = temp_dir / "base.json"
        base_file.write_text(json.dumps({
            'level': 'DEBUG',
            'formatters': {'simple': {'format': '%(message)s'}}
        }))
        
        override_file = temp_dir / "override.json"
        override_file.write_text(json.dumps({
            'level': 'INFO',
            'handlers': {'console': {}}
        }))
        
        loader = ConfigLoader()
        loader.load_from_file(base_file)
        loader.load_from_file(override_file)
        
        assert loader.get('level') == 'INFO'
        assert loader.get('formatters.simple.format') == '%(message)s'
        assert 'console' in loader.get('handlers')
