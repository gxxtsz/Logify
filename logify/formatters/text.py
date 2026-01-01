"""
文本格式化器模块

基于模板的文本格式化，支持自定义占位符
"""

from datetime import datetime
from string import Template
from typing import TYPE_CHECKING, Dict, Any

from .base import BaseFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


# 默认格式模板
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class TextFormatter(BaseFormatter):
    """文本格式化器
    
    支持类似 Python logging 的格式化字符串语法
    
    可用的格式化占位符：
    - %(asctime)s: 时间戳
    - %(name)s: Logger 名称
    - %(levelname)s: 日志级别名称
    - %(levelno)d: 日志级别数值
    - %(message)s: 日志消息
    - %(filename)s: 源文件名
    - %(lineno)d: 行号
    - %(funcName)s: 函数名
    - %(thread)d: 线程 ID
    - %(threadName)s: 线程名称
    - %(process)d: 进程 ID
    """
    
    def __init__(
        self,
        fmt: str = DEFAULT_FORMAT,
        datefmt: str = DEFAULT_DATE_FORMAT,
        name: str = ""
    ):
        """初始化文本格式化器
        
        Args:
            fmt: 格式化模板字符串
            datefmt: 日期时间格式字符串
            name: 格式化器名称
        """
        super().__init__(name)
        self._fmt = fmt
        self._datefmt = datefmt
    
    @property
    def format_string(self) -> str:
        """获取格式化模板"""
        return self._fmt
    
    @property
    def date_format(self) -> str:
        """获取日期格式"""
        return self._datefmt
    
    def format_time(self, record: 'LogRecord') -> str:
        """格式化时间戳
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的时间字符串
        """
        dt = datetime.fromtimestamp(record.timestamp)
        return dt.strftime(self._datefmt)
    
    def _get_format_dict(self, record: 'LogRecord') -> Dict[str, Any]:
        """获取格式化所需的字典
        
        Args:
            record: 日志记录
            
        Returns:
            包含所有格式化占位符值的字典
        """
        return {
            'asctime': self.format_time(record),
            'name': record.name,
            'levelname': record.level_name,
            'levelno': record.level,
            'message': record.message,
            'filename': record.filename,
            'lineno': record.lineno,
            'funcName': record.func_name,
            'thread': record.thread_id,
            'threadName': record.thread_name,
            'process': record.process_id,
            **record.extra,
            **record.kwargs
        }
    
    def format(self, record: 'LogRecord') -> str:
        """格式化日志记录
        
        Args:
            record: 待格式化的日志记录
            
        Returns:
            格式化后的字符串
        """
        format_dict = self._get_format_dict(record)
        
        try:
            # 使用 % 格式化
            result = self._fmt % format_dict
        except (KeyError, ValueError, TypeError):
            # 回退到基本格式
            result = f"{format_dict['asctime']} - {format_dict['name']} - {format_dict['levelname']} - {format_dict['message']}"
        
        # 添加异常信息
        exc_text = self.format_exception(record)
        if exc_text:
            result = f"{result}\n{exc_text}"
        
        return result
    
    def __repr__(self) -> str:
        return f"<TextFormatter(fmt={self._fmt!r})>"
