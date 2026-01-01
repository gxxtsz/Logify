"""
Logify Core Layer

核心层：管理日志记录的核心数据结构和生命周期
"""

from .levels import LogLevel
from .record import LogRecord
from .manager import LoggerManager

__all__ = ['LogLevel', 'LogRecord', 'LoggerManager']
