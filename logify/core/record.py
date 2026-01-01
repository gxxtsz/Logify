"""
日志记录数据结构模块

LogRecord 是日志记录的数据载体，封装时间戳、级别、消息、调用栈等信息
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime

from .levels import LogLevel


@dataclass
class LogRecord:
    """日志记录类
    
    封装单条日志的所有信息，作为日志系统内部传递的数据载体
    
    Attributes:
        name: Logger 名称
        level: 日志级别
        msg: 原始日志消息
        args: 消息格式化参数
        kwargs: 附加的键值对数据（用于结构化日志）
        timestamp: 日志创建时间戳
        filename: 调用日志的源文件名
        lineno: 调用日志的源代码行号
        func_name: 调用日志的函数名
        thread_id: 线程 ID
        thread_name: 线程名称
        process_id: 进程 ID
        exception_info: 异常信息元组
        extra: 额外的上下文数据
    """
    
    name: str
    level: LogLevel
    msg: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    filename: str = ""
    lineno: int = 0
    func_name: str = ""
    thread_id: int = field(default_factory=lambda: threading.current_thread().ident or 0)
    thread_name: str = field(default_factory=lambda: threading.current_thread().name)
    process_id: int = field(default_factory=os.getpid)
    exception_info: Optional[tuple] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果没有提供调用位置信息，尝试自动获取
        if not self.filename and not self.lineno:
            self._find_caller()
    
    def _find_caller(self, stack_level: int = 6) -> None:
        """查找调用者的文件名、行号和函数名
        
        Args:
            stack_level: 向上追溯的栈帧层数
        """
        try:
            frame = sys._getframe(stack_level)
            while frame:
                code = frame.f_code
                filename = os.path.basename(code.co_filename)
                # 跳过 logify 内部文件
                if 'logify' not in code.co_filename or 'test' in code.co_filename:
                    self.filename = filename
                    self.lineno = frame.f_lineno
                    self.func_name = code.co_name
                    break
                frame = frame.f_back
        except (ValueError, AttributeError):
            pass
    
    @property
    def level_name(self) -> str:
        """获取日志级别名称"""
        return LogLevel.get_name(self.level)
    
    @property
    def datetime(self) -> datetime:
        """获取日志时间的 datetime 对象"""
        return datetime.fromtimestamp(self.timestamp)
    
    @property
    def formatted_time(self) -> str:
        """获取格式化的时间字符串"""
        return self.datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def message(self) -> str:
        """获取格式化后的消息
        
        如果 msg 包含格式化占位符，使用 args 进行格式化
        """
        if self.args:
            try:
                return self.msg % self.args
            except (TypeError, ValueError):
                return self.msg
        return self.msg
    
    def to_dict(self) -> Dict[str, Any]:
        """将日志记录转换为字典格式
        
        Returns:
            包含所有日志信息的字典
        """
        return {
            'name': self.name,
            'level': self.level,
            'level_name': self.level_name,
            'message': self.message,
            'timestamp': self.timestamp,
            'formatted_time': self.formatted_time,
            'filename': self.filename,
            'lineno': self.lineno,
            'func_name': self.func_name,
            'thread_id': self.thread_id,
            'thread_name': self.thread_name,
            'process_id': self.process_id,
            'extra': self.extra,
            **self.kwargs
        }
