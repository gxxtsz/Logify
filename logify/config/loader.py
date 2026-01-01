"""
配置加载器模块

从文件（YAML/JSON/TOML）或环境变量加载配置
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigLoader:
    """配置加载器
    
    支持从多种来源加载配置：
    - JSON 文件
    - YAML 文件（需要安装 PyYAML）
    - TOML 文件（需要安装 toml 或使用 Python 3.11+ 的 tomllib）
    - 环境变量
    - 字典
    """
    
    def __init__(self):
        """初始化配置加载器"""
        self._config: Dict[str, Any] = {}
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self._config.copy()
    
    def load_from_dict(self, config: Dict[str, Any]) -> 'ConfigLoader':
        """从字典加载配置
        
        Args:
            config: 配置字典
            
        Returns:
            返回自身，支持链式调用
        """
        self._config.update(config)
        return self
    
    def load_from_file(self, filepath: Union[str, Path]) -> 'ConfigLoader':
        """从文件加载配置
        
        根据文件扩展名自动选择解析器
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            返回自身，支持链式调用
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        suffix = filepath.suffix.lower()
        
        if suffix == '.json':
            config = self._load_json(filepath)
        elif suffix in ('.yaml', '.yml'):
            config = self._load_yaml(filepath)
        elif suffix == '.toml':
            config = self._load_toml(filepath)
        else:
            raise ValueError(f"Unsupported config format: {suffix}")
        
        self._config.update(config)
        return self
    
    def _load_json(self, filepath: Path) -> Dict[str, Any]:
        """加载 JSON 配置文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            配置字典
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """加载 YAML 配置文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            配置字典
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config files. "
                "Install it with: pip install pyyaml"
            )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _load_toml(self, filepath: Path) -> Dict[str, Any]:
        """加载 TOML 配置文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            配置字典
        """
        # Python 3.11+ 内置 tomllib
        try:
            import tomllib
            with open(filepath, 'rb') as f:
                return tomllib.load(f)
        except ImportError:
            pass
        
        # 回退到 toml 库
        try:
            import toml
            with open(filepath, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            raise ImportError(
                "TOML support requires Python 3.11+ or the 'toml' package. "
                "Install it with: pip install toml"
            )
    
    def load_from_env(
        self,
        prefix: str = "LOGIFY_",
        mapping: Optional[Dict[str, str]] = None
    ) -> 'ConfigLoader':
        """从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀
            mapping: 环境变量名到配置键的映射
            
        Returns:
            返回自身，支持链式调用
        """
        if mapping:
            # 使用自定义映射
            for env_name, config_key in mapping.items():
                value = os.environ.get(env_name)
                if value is not None:
                    self._set_nested_value(config_key, self._parse_env_value(value))
        else:
            # 根据前缀自动发现
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    config_key = key[len(prefix):].lower()
                    self._set_nested_value(config_key, self._parse_env_value(value))
        
        return self
    
    def _parse_env_value(self, value: str) -> Any:
        """解析环境变量值
        
        尝试将字符串转换为适当的类型
        
        Args:
            value: 环境变量字符串值
            
        Returns:
            解析后的值
        """
        # 尝试解析为 JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def _set_nested_value(self, key: str, value: Any) -> None:
        """设置嵌套配置值
        
        使用点号分隔的键设置嵌套值，例如 "handlers.console.level"
        
        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键（支持点号分隔）
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def clear(self) -> 'ConfigLoader':
        """清除所有配置
        
        Returns:
            返回自身，支持链式调用
        """
        self._config.clear()
        return self
    
    def merge(self, other: 'ConfigLoader') -> 'ConfigLoader':
        """合并另一个配置加载器的配置
        
        Args:
            other: 另一个配置加载器
            
        Returns:
            返回自身，支持链式调用
        """
        self._deep_merge(self._config, other._config)
        return self
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """深度合并字典
        
        Args:
            base: 基础字典
            override: 覆盖字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def __repr__(self) -> str:
        return f"<ConfigLoader(keys={list(self._config.keys())})>"
