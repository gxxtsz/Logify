"""
级别过滤器模块

基于日志级别的过滤
"""

from typing import TYPE_CHECKING, Union

from .base import BaseFilter
from ..core.levels import LogLevel

if TYPE_CHECKING:
    from ..core.record import LogRecord


class LevelFilter(BaseFilter):
    """级别过滤器
    
    只允许指定级别或更高级别的日志通过
    """
    
    def __init__(self, level: Union[LogLevel, int, str] = LogLevel.DEBUG, name: str = ""):
        """初始化级别过滤器
        
        Args:
            level: 最低日志级别，可以是 LogLevel 枚举、整数或字符串
            name: 过滤器名称
        """
        super().__init__(name)
        self._level = self._normalize_level(level)
    
    def _normalize_level(self, level: Union[LogLevel, int, str]) -> int:
        """规范化日志级别为整数
        
        Args:
            level: 日志级别
            
        Returns:
            日志级别整数值
        """
        if isinstance(level, LogLevel):
            return level.value
        elif isinstance(level, str):
            log_level = LogLevel.get_level(level)
            return log_level.value if log_level else LogLevel.DEBUG.value
        return int(level)
    
    @property
    def level(self) -> int:
        """获取当前过滤级别"""
        return self._level
    
    @level.setter
    def level(self, value: Union[LogLevel, int, str]) -> None:
        """设置过滤级别"""
        self._level = self._normalize_level(value)
    
    def filter(self, record: 'LogRecord') -> bool:
        """过滤日志记录
        
        Args:
            record: 待过滤的日志记录
            
        Returns:
            日志级别 >= 过滤级别时返回 True
        """
        return record.level >= self._level
    
    def __repr__(self) -> str:
        level_name = LogLevel.get_name(self._level)
        return f"<LevelFilter(level={level_name})>"
