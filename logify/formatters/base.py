"""
格式化器基类模块

定义格式化器的抽象基类，所有自定义格式化器都应继承此类
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.record import LogRecord


class BaseFormatter(ABC):
    """格式化器抽象基类
    
    所有格式化器必须实现 format() 方法，将 LogRecord 转换为字符串
    """
    
    def __init__(self, name: str = ""):
        """初始化格式化器
        
        Args:
            name: 格式化器名称，用于标识和调试
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def format(self, record: 'LogRecord') -> str:
        """格式化日志记录
        
        Args:
            record: 待格式化的日志记录
            
        Returns:
            格式化后的字符串
        """
        pass
    
    def format_exception(self, record: 'LogRecord') -> str:
        """格式化异常信息
        
        Args:
            record: 包含异常信息的日志记录
            
        Returns:
            格式化后的异常堆栈字符串
        """
        if record.exception_info is None:
            return ""
        
        import traceback
        exc_type, exc_value, exc_tb = record.exception_info
        
        if exc_type is None:
            return ""
        
        lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        return ''.join(lines)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
