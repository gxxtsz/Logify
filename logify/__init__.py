"""
Logify - A Python Logging Library

一个功能完善、易于扩展的 Python 日志处理模块

基本用法：
```python
from logify import get_logger, DEBUG, INFO

# 获取 logger
logger = get_logger("myapp")

# 记录日志
logger.info("Application started")
logger.debug("Debug message")
logger.error("Error occurred", exc_info=True)
```

高级用法：
```python
from logify import (
    get_logger, 
    ConsoleHandler, 
    FileHandler, 
    JsonFormatter,
    LevelFilter,
    LogLevel
)

# 创建 logger
logger = get_logger("myapp")
logger.level = LogLevel.DEBUG

# 添加控制台处理器
console_handler = ConsoleHandler()
logger.add_handler(console_handler)

# 添加文件处理器
file_handler = FileHandler("app.log")
file_handler.formatter = JsonFormatter()
logger.add_handler(file_handler)

# 使用上下文
with logger.context(request_id="123"):
    logger.info("Processing request")

# 使用装饰器
@logger.trace
def my_function():
    pass
```
"""

__version__ = "0.1.0"
__author__ = "Logify Team"

# Core - 核心组件
from .core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL
from .core.record import LogRecord
from .core.manager import LoggerManager, get_logger

# Filters - 过滤器
from .filters.base import BaseFilter, FilterChain
from .filters.level_filter import LevelFilter
from .filters.regex_filter import RegexFilter
from .filters.context_filter import ContextFilter

# Formatters - 格式化器
from .formatters.base import BaseFormatter
from .formatters.text import TextFormatter
from .formatters.json_formatter import JsonFormatter
from .formatters.color import ColorFormatter, Colors

# Handlers - 处理器
from .handlers.base import BaseHandler, HandlerChain
from .handlers.console import ConsoleHandler
from .handlers.file import FileHandler
from .handlers.rotating import RotatingFileHandler, TimedRotatingFileHandler
from .handlers.async_handler import AsyncHandler
from .handlers.network import NetworkHandler, TCPHandler, UDPHandler, HTTPHandler

# Config - 配置
from .config.loader import ConfigLoader
from .config.parser import ConfigParser

# API - 日志记录器
from .api.logger import Logger


def basic_config(
    level: int = INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    filename: str = None,
    handlers: list = None,
    force: bool = False
) -> None:
    """快速配置根日志记录器
    
    类似于 logging.basicConfig() 的便捷函数
    
    Args:
        level: 日志级别
        format: 日志格式
        datefmt: 日期格式
        filename: 日志文件名（可选）
        handlers: 处理器列表（可选）
        force: 是否强制重新配置
    """
    root = get_logger("root")
    
    # 如果已有处理器且不强制，跳过
    if root.handlers and not force:
        return
    
    # 清除现有处理器
    if force:
        for handler in root.handlers[:]:
            root.remove_handler(handler)
    
    # 设置级别
    root.level = level
    
    # 创建格式化器
    formatter = TextFormatter(fmt=format, datefmt=datefmt)
    
    if handlers:
        # 使用提供的处理器
        for handler in handlers:
            handler.formatter = formatter
            root.add_handler(handler)
    elif filename:
        # 使用文件处理器
        file_handler = FileHandler(filename)
        file_handler.formatter = formatter
        root.add_handler(file_handler)
    else:
        # 默认使用控制台处理器
        console_handler = ConsoleHandler()
        console_handler.formatter = ColorFormatter(fmt=format, datefmt=datefmt)
        root.add_handler(console_handler)


def configure_from_file(filepath: str) -> ConfigParser:
    """从配置文件配置日志系统
    
    Args:
        filepath: 配置文件路径（支持 JSON、YAML、TOML）
        
    Returns:
        ConfigParser 实例
    """
    return ConfigParser.from_file(filepath)


def configure_from_dict(config: dict) -> ConfigParser:
    """从字典配置日志系统
    
    Args:
        config: 配置字典
        
    Returns:
        ConfigParser 实例
    """
    parser = ConfigParser(config)
    parser.parse()
    return parser


# 便捷的模块级日志方法
def debug(msg: str, *args, **kwargs) -> None:
    """记录 DEBUG 级别日志到根 Logger"""
    get_logger("root").debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """记录 INFO 级别日志到根 Logger"""
    get_logger("root").info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """记录 WARNING 级别日志到根 Logger"""
    get_logger("root").warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """记录 ERROR 级别日志到根 Logger"""
    get_logger("root").error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """记录 CRITICAL 级别日志到根 Logger"""
    get_logger("root").critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    """记录带异常信息的 ERROR 级别日志到根 Logger"""
    get_logger("root").exception(msg, *args, **kwargs)


__all__ = [
    # Version
    '__version__',
    
    # Core
    'LogLevel',
    'DEBUG',
    'INFO', 
    'WARNING',
    'ERROR',
    'CRITICAL',
    'LogRecord',
    'LoggerManager',
    'get_logger',
    
    # Filters
    'BaseFilter',
    'FilterChain',
    'LevelFilter',
    'RegexFilter',
    'ContextFilter',
    
    # Formatters
    'BaseFormatter',
    'TextFormatter',
    'JsonFormatter',
    'ColorFormatter',
    'Colors',
    
    # Handlers
    'BaseHandler',
    'HandlerChain',
    'ConsoleHandler',
    'FileHandler',
    'RotatingFileHandler',
    'TimedRotatingFileHandler',
    'AsyncHandler',
    'NetworkHandler',
    'TCPHandler',
    'UDPHandler',
    'HTTPHandler',
    
    # Config
    'ConfigLoader',
    'ConfigParser',
    
    # API
    'Logger',
    
    # Functions
    'basic_config',
    'configure_from_file',
    'configure_from_dict',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'exception',
]
