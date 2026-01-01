"""
文件处理器模块

输出日志到文件
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .base import BaseHandler
from ..core.levels import LogLevel
from ..formatters.base import BaseFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class FileHandler(BaseHandler):
    """文件处理器
    
    将日志输出到指定文件
    """
    
    def __init__(
        self,
        filename: Union[str, Path],
        mode: str = 'a',
        encoding: str = 'utf-8',
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        delay: bool = False,
        name: str = ""
    ):
        """初始化文件处理器
        
        Args:
            filename: 日志文件路径
            mode: 文件打开模式，'a' 追加，'w' 覆盖
            encoding: 文件编码
            level: 最低日志级别
            formatter: 格式化器
            delay: 是否延迟打开文件（首次写入时打开）
            name: 处理器名称
        """
        super().__init__(level=level, formatter=formatter, name=name)
        
        self._filename = Path(filename)
        self._mode = mode
        self._encoding = encoding
        self._delay = delay
        self._file = None
        
        # 确保目录存在
        self._filename.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果不延迟，立即打开文件
        if not delay:
            self._open()
    
    @property
    def filename(self) -> Path:
        """获取文件路径"""
        return self._filename
    
    @property
    def base_filename(self) -> str:
        """获取基础文件名"""
        return str(self._filename)
    
    def _open(self) -> None:
        """打开文件"""
        if self._file is None:
            self._file = open(
                self._filename,
                mode=self._mode,
                encoding=self._encoding
            )
    
    def emit(self, record: 'LogRecord') -> None:
        """输出日志到文件
        
        Args:
            record: 日志记录
        """
        if self._file is None:
            self._open()
        
        try:
            msg = self.format(record)
            self._file.write(msg + '\n')
            self.flush()
        except Exception:
            self.handle_error(record)
    
    def flush(self) -> None:
        """刷新文件缓冲区"""
        if self._file:
            try:
                self._file.flush()
                os.fsync(self._file.fileno())
            except Exception:
                pass
    
    def close(self) -> None:
        """关闭文件"""
        super().close()
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
            finally:
                self._file = None
    
    def __repr__(self) -> str:
        return f"<FileHandler(filename={self._filename!r})>"
