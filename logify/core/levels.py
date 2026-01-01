"""
日志级别定义模块

定义和管理日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
"""

from enum import IntEnum
from typing import Dict, Optional


class LogLevel(IntEnum):
    """日志级别枚举类
    
    级别从低到高：DEBUG < INFO < WARNING < ERROR < CRITICAL
    数值越大，级别越高
    """
    
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def get_name(cls, level: int) -> str:
        """根据级别值获取级别名称
        
        Args:
            level: 日志级别数值
            
        Returns:
            级别名称字符串
        """
        for member in cls:
            if member.value == level:
                return member.name
        return f"LEVEL_{level}"
    
    @classmethod
    def get_level(cls, name: str) -> Optional['LogLevel']:
        """根据名称获取日志级别
        
        Args:
            name: 级别名称（不区分大小写）
            
        Returns:
            对应的 LogLevel 枚举值，不存在返回 None
        """
        name_upper = name.upper()
        for member in cls:
            if member.name == name_upper:
                return member
        return None
    
    @classmethod
    def get_all_levels(cls) -> Dict[str, int]:
        """获取所有日志级别
        
        Returns:
            日志级别名称到数值的映射字典
        """
        return {member.name: member.value for member in cls}


# 便捷常量导出
DEBUG = LogLevel.DEBUG
INFO = LogLevel.INFO
WARNING = LogLevel.WARNING
ERROR = LogLevel.ERROR
CRITICAL = LogLevel.CRITICAL
