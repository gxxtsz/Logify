"""
配置解析器模块

解析配置并初始化相应的 Logger、Handler、Formatter 等组件
"""

from typing import Any, Dict, List, Optional, Type, Union

from .loader import ConfigLoader
from ..core.levels import LogLevel
from ..core.manager import LoggerManager, get_logger
from ..filters.base import BaseFilter
from ..filters.level_filter import LevelFilter
from ..filters.regex_filter import RegexFilter
from ..filters.context_filter import ContextFilter
from ..formatters.base import BaseFormatter
from ..formatters.text import TextFormatter
from ..formatters.json_formatter import JsonFormatter
from ..formatters.color import ColorFormatter
from ..handlers.base import BaseHandler
from ..handlers.console import ConsoleHandler
from ..handlers.file import FileHandler
from ..handlers.rotating import RotatingFileHandler, TimedRotatingFileHandler


class ConfigParser:
    """配置解析器
    
    解析配置字典并创建相应的日志组件
    
    配置格式示例：
    ```
    {
        "version": 1,
        "formatters": {
            "simple": {
                "class": "TextFormatter",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {
                "class": "JsonFormatter"
            }
        },
        "filters": {
            "level_filter": {
                "class": "LevelFilter",
                "level": "INFO"
            }
        },
        "handlers": {
            "console": {
                "class": "ConsoleHandler",
                "level": "DEBUG",
                "formatter": "simple"
            },
            "file": {
                "class": "FileHandler",
                "filename": "app.log",
                "level": "INFO",
                "formatter": "simple"
            }
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["console", "file"]
            },
            "app": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": false
            }
        }
    }
    ```
    """
    
    # 内置组件类映射
    FORMATTER_CLASSES: Dict[str, Type[BaseFormatter]] = {
        'TextFormatter': TextFormatter,
        'JsonFormatter': JsonFormatter,
        'ColorFormatter': ColorFormatter,
    }
    
    HANDLER_CLASSES: Dict[str, Type[BaseHandler]] = {
        'ConsoleHandler': ConsoleHandler,
        'FileHandler': FileHandler,
        'RotatingFileHandler': RotatingFileHandler,
        'TimedRotatingFileHandler': TimedRotatingFileHandler,
    }
    
    FILTER_CLASSES: Dict[str, Type[BaseFilter]] = {
        'LevelFilter': LevelFilter,
        'RegexFilter': RegexFilter,
        'ContextFilter': ContextFilter,
    }
    
    def __init__(self, config: Optional[Union[Dict[str, Any], ConfigLoader]] = None):
        """初始化配置解析器
        
        Args:
            config: 配置字典或 ConfigLoader 实例
        """
        if config is None:
            self._config: Dict[str, Any] = {}
        elif isinstance(config, ConfigLoader):
            self._config = config.config
        else:
            self._config = config
        
        self._formatters: Dict[str, BaseFormatter] = {}
        self._filters: Dict[str, BaseFilter] = {}
        self._handlers: Dict[str, BaseHandler] = {}
    
    def parse(self) -> None:
        """解析配置并创建所有组件"""
        # 按顺序解析：formatters -> filters -> handlers -> loggers
        self._parse_formatters()
        self._parse_filters()
        self._parse_handlers()
        self._parse_loggers()
    
    def _parse_formatters(self) -> None:
        """解析格式化器配置"""
        formatters_config = self._config.get('formatters', {})
        
        for name, config in formatters_config.items():
            formatter = self._create_formatter(config)
            self._formatters[name] = formatter
    
    def _create_formatter(self, config: Dict[str, Any]) -> BaseFormatter:
        """创建格式化器实例
        
        Args:
            config: 格式化器配置
            
        Returns:
            格式化器实例
        """
        class_name = config.get('class', 'TextFormatter')
        
        # 获取类
        formatter_class = self.FORMATTER_CLASSES.get(class_name)
        if formatter_class is None:
            raise ValueError(f"Unknown formatter class: {class_name}")
        
        # 提取参数
        kwargs = {k: v for k, v in config.items() if k != 'class'}
        
        # TextFormatter 特殊处理
        if class_name == 'TextFormatter':
            if 'format' in kwargs:
                kwargs['fmt'] = kwargs.pop('format')
        
        return formatter_class(**kwargs)
    
    def _parse_filters(self) -> None:
        """解析过滤器配置"""
        filters_config = self._config.get('filters', {})
        
        for name, config in filters_config.items():
            filter_ = self._create_filter(config)
            self._filters[name] = filter_
    
    def _create_filter(self, config: Dict[str, Any]) -> BaseFilter:
        """创建过滤器实例
        
        Args:
            config: 过滤器配置
            
        Returns:
            过滤器实例
        """
        class_name = config.get('class', 'LevelFilter')
        
        filter_class = self.FILTER_CLASSES.get(class_name)
        if filter_class is None:
            raise ValueError(f"Unknown filter class: {class_name}")
        
        # 提取参数
        kwargs = {k: v for k, v in config.items() if k != 'class'}
        
        # 处理日志级别
        if 'level' in kwargs:
            kwargs['level'] = self._parse_level(kwargs['level'])
        
        return filter_class(**kwargs)
    
    def _parse_handlers(self) -> None:
        """解析处理器配置"""
        handlers_config = self._config.get('handlers', {})
        
        for name, config in handlers_config.items():
            handler = self._create_handler(config)
            self._handlers[name] = handler
    
    def _create_handler(self, config: Dict[str, Any]) -> BaseHandler:
        """创建处理器实例
        
        Args:
            config: 处理器配置
            
        Returns:
            处理器实例
        """
        class_name = config.get('class', 'ConsoleHandler')
        
        handler_class = self.HANDLER_CLASSES.get(class_name)
        if handler_class is None:
            raise ValueError(f"Unknown handler class: {class_name}")
        
        # 提取参数
        kwargs = {k: v for k, v in config.items() if k not in ('class', 'formatter', 'filters')}
        
        # 处理日志级别
        if 'level' in kwargs:
            kwargs['level'] = self._parse_level(kwargs['level'])
        
        # 创建处理器
        handler = handler_class(**kwargs)
        
        # 设置格式化器
        formatter_name = config.get('formatter')
        if formatter_name and formatter_name in self._formatters:
            handler.formatter = self._formatters[formatter_name]
        
        # 添加过滤器
        filter_names = config.get('filters', [])
        for filter_name in filter_names:
            if filter_name in self._filters:
                handler.add_filter(self._filters[filter_name])
        
        return handler
    
    def _parse_loggers(self) -> None:
        """解析 Logger 配置"""
        loggers_config = self._config.get('loggers', {})
        
        for name, config in loggers_config.items():
            self._configure_logger(name, config)
    
    def _configure_logger(self, name: str, config: Dict[str, Any]) -> None:
        """配置 Logger
        
        Args:
            name: Logger 名称
            config: Logger 配置
        """
        logger = get_logger(name)
        
        # 设置级别
        if 'level' in config:
            logger.level = self._parse_level(config['level'])
        
        # 添加处理器
        handler_names = config.get('handlers', [])
        for handler_name in handler_names:
            if handler_name in self._handlers:
                logger.add_handler(self._handlers[handler_name])
        
        # 设置是否传播
        if 'propagate' in config:
            logger.propagate = config['propagate']
    
    def _parse_level(self, level: Union[str, int]) -> int:
        """解析日志级别
        
        Args:
            level: 级别字符串或整数
            
        Returns:
            级别整数值
        """
        if isinstance(level, int):
            return level
        
        log_level = LogLevel.get_level(level)
        if log_level is not None:
            return log_level.value
        
        return LogLevel.DEBUG.value
    
    def get_formatter(self, name: str) -> Optional[BaseFormatter]:
        """获取已创建的格式化器
        
        Args:
            name: 格式化器名称
            
        Returns:
            格式化器实例或 None
        """
        return self._formatters.get(name)
    
    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """获取已创建的处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            处理器实例或 None
        """
        return self._handlers.get(name)
    
    def get_filter(self, name: str) -> Optional[BaseFilter]:
        """获取已创建的过滤器
        
        Args:
            name: 过滤器名称
            
        Returns:
            过滤器实例或 None
        """
        return self._filters.get(name)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'ConfigParser':
        """从文件创建配置解析器
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            ConfigParser 实例
        """
        loader = ConfigLoader()
        loader.load_from_file(filepath)
        parser = cls(loader)
        parser.parse()
        return parser
    
    @classmethod
    def register_formatter(cls, name: str, formatter_class: Type[BaseFormatter]) -> None:
        """注册自定义格式化器类
        
        Args:
            name: 类名
            formatter_class: 格式化器类
        """
        cls.FORMATTER_CLASSES[name] = formatter_class
    
    @classmethod
    def register_handler(cls, name: str, handler_class: Type[BaseHandler]) -> None:
        """注册自定义处理器类
        
        Args:
            name: 类名
            handler_class: 处理器类
        """
        cls.HANDLER_CLASSES[name] = handler_class
    
    @classmethod
    def register_filter(cls, name: str, filter_class: Type[BaseFilter]) -> None:
        """注册自定义过滤器类
        
        Args:
            name: 类名
            filter_class: 过滤器类
        """
        cls.FILTER_CLASSES[name] = filter_class
    
    def __repr__(self) -> str:
        return (
            f"<ConfigParser("
            f"formatters={len(self._formatters)}, "
            f"filters={len(self._filters)}, "
            f"handlers={len(self._handlers)})>"
        )
