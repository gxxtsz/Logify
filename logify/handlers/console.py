"""
控制台处理器模块

输出日志到控制台（stdout/stderr）
"""

import sys
from typing import TYPE_CHECKING, Optional, TextIO, Union

from .base import BaseHandler
from ..core.levels import LogLevel
from ..formatters.base import BaseFormatter
from ..formatters.color import ColorFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class ConsoleHandler(BaseHandler):
    """控制台处理器
    
    将日志输出到标准输出或标准错误流
    默认使用 ColorFormatter 提供彩色输出
    """
    
    def __init__(
        self,
        stream: Optional[TextIO] = None,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        use_stderr_for_errors: bool = False,
        name: str = ""
    ):
        """初始化控制台处理器
        
        Args:
            stream: 输出流，默认为 sys.stdout
            level: 最低日志级别
            formatter: 格式化器，默认为 ColorFormatter
            use_stderr_for_errors: 是否将 ERROR 及以上级别输出到 stderr，默认 False 以保证输出顺序
            name: 处理器名称
        """
        # 默认使用颜色格式化器
        if formatter is None:
            formatter = ColorFormatter()
        
        super().__init__(level=level, formatter=formatter, name=name)
        
        self._stream = stream or sys.stdout
        self._use_stderr_for_errors = use_stderr_for_errors
    
    @property
    def stream(self) -> TextIO:
        """获取输出流"""
        return self._stream
    
    @stream.setter
    def stream(self, value: TextIO) -> None:
        """设置输出流"""
        self._stream = value
    
    def _get_stream(self, record: 'LogRecord') -> TextIO:
        """根据日志级别获取输出流
        
        Args:
            record: 日志记录
            
        Returns:
            输出流
        """
        if self._use_stderr_for_errors and record.level >= LogLevel.ERROR:
            return sys.stderr
        return self._stream
    
    def emit(self, record: 'LogRecord') -> None:
        """输出日志到控制台
        
        Args:
            record: 日志记录
        """
        try:
            stream = self._get_stream(record)
            msg = self.format(record)
            stream.write(msg + '\n')
            stream.flush()
        except Exception:
            self.handle_error(record)
    
    def flush(self) -> None:
        """刷新输出流"""
        try:
            self._stream.flush()
            if self._use_stderr_for_errors:
                sys.stderr.flush()
        except Exception:
            pass
    
    def __repr__(self) -> str:
        stream_name = getattr(self._stream, 'name', str(self._stream))
        return f"<ConsoleHandler(stream={stream_name})>"
