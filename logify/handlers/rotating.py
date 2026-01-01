"""
轮转文件处理器模块

支持按大小或时间轮转的文件处理器
"""

import os
import re
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .file import FileHandler
from ..core.levels import LogLevel
from ..formatters.base import BaseFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class RotatingFileHandler(FileHandler):
    """按大小轮转的文件处理器
    
    当日志文件达到指定大小时，自动轮转到备份文件
    """
    
    def __init__(
        self,
        filename: Union[str, Path],
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        encoding: str = 'utf-8',
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        compress: bool = False,
        name: str = ""
    ):
        """初始化轮转文件处理器
        
        Args:
            filename: 日志文件路径
            max_bytes: 单个文件最大字节数
            backup_count: 保留的备份文件数量
            encoding: 文件编码
            level: 最低日志级别
            formatter: 格式化器
            compress: 是否压缩备份文件
            name: 处理器名称
        """
        super().__init__(
            filename=filename,
            mode='a',
            encoding=encoding,
            level=level,
            formatter=formatter,
            delay=True,
            name=name
        )
        
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._compress = compress
    
    @property
    def max_bytes(self) -> int:
        """获取最大字节数"""
        return self._max_bytes
    
    @property
    def backup_count(self) -> int:
        """获取备份数量"""
        return self._backup_count
    
    def should_rollover(self, record: 'LogRecord') -> bool:
        """检查是否需要轮转
        
        Args:
            record: 日志记录
            
        Returns:
            True 表示需要轮转
        """
        if self._max_bytes <= 0:
            return False
        
        if self._file is None:
            self._open()
        
        # 检查当前文件大小
        self._file.seek(0, 2)  # 移到文件末尾
        current_size = self._file.tell()
        
        # 估算新记录大小
        msg = self.format(record)
        new_size = len(msg.encode(self._encoding)) + 1  # +1 for newline
        
        return current_size + new_size > self._max_bytes
    
    def do_rollover(self) -> None:
        """执行轮转"""
        if self._file:
            self._file.close()
            self._file = None
        
        # 轮转备份文件
        for i in range(self._backup_count - 1, 0, -1):
            src = self._get_backup_filename(i)
            dst = self._get_backup_filename(i + 1)
            
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        
        # 将当前文件重命名为 .1
        dst = self._get_backup_filename(1)
        if self._filename.exists():
            if dst.exists():
                dst.unlink()
            self._filename.rename(dst)
            
            # 压缩备份
            if self._compress:
                self._compress_file(dst)
        
        # 删除超出数量的备份
        self._cleanup_old_backups()
        
        # 重新打开文件
        self._open()
    
    def _get_backup_filename(self, index: int) -> Path:
        """获取备份文件名
        
        Args:
            index: 备份索引
            
        Returns:
            备份文件路径
        """
        suffix = f".{index}"
        if self._compress and index > 0:
            suffix += ".gz"
        return Path(str(self._filename) + suffix)
    
    def _compress_file(self, filepath: Path) -> None:
        """压缩文件
        
        Args:
            filepath: 要压缩的文件路径
        """
        gz_path = Path(str(filepath) + ".gz")
        try:
            with open(filepath, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            filepath.unlink()
        except Exception:
            pass
    
    def _cleanup_old_backups(self) -> None:
        """清理过期的备份文件"""
        pattern = re.compile(
            rf"^{re.escape(self._filename.name)}\.(\d+)(\.gz)?$"
        )
        
        for file in self._filename.parent.iterdir():
            match = pattern.match(file.name)
            if match:
                index = int(match.group(1))
                if index > self._backup_count:
                    file.unlink()
    
    def emit(self, record: 'LogRecord') -> None:
        """输出日志（带轮转检查）
        
        Args:
            record: 日志记录
        """
        try:
            if self.should_rollover(record):
                self.do_rollover()
            super().emit(record)
        except Exception:
            self.handle_error(record)


class TimedRotatingFileHandler(FileHandler):
    """按时间轮转的文件处理器
    
    按照指定的时间间隔轮转日志文件
    """
    
    # 时间间隔类型
    WHEN_MAPPING = {
        'S': 1,           # 秒
        'M': 60,          # 分钟
        'H': 3600,        # 小时
        'D': 86400,       # 天
        'MIDNIGHT': -1,   # 午夜
    }
    
    def __init__(
        self,
        filename: Union[str, Path],
        when: str = 'D',
        interval: int = 1,
        backup_count: int = 7,
        encoding: str = 'utf-8',
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        compress: bool = False,
        name: str = ""
    ):
        """初始化按时间轮转的文件处理器
        
        Args:
            filename: 日志文件路径
            when: 时间间隔类型 ('S', 'M', 'H', 'D', 'MIDNIGHT')
            interval: 时间间隔数量
            backup_count: 保留的备份文件数量
            encoding: 文件编码
            level: 最低日志级别
            formatter: 格式化器
            compress: 是否压缩备份文件
            name: 处理器名称
        """
        super().__init__(
            filename=filename,
            mode='a',
            encoding=encoding,
            level=level,
            formatter=formatter,
            delay=True,
            name=name
        )
        
        self._when = when.upper()
        self._interval = interval
        self._backup_count = backup_count
        self._compress = compress
        
        # 计算轮转间隔（秒）
        self._interval_seconds = self._compute_interval()
        
        # 计算下一次轮转时间
        self._rollover_at = self._compute_rollover_time()
    
    def _compute_interval(self) -> int:
        """计算轮转间隔秒数"""
        if self._when not in self.WHEN_MAPPING:
            raise ValueError(f"Invalid when value: {self._when}")
        
        base = self.WHEN_MAPPING[self._when]
        if base == -1:  # MIDNIGHT
            return 86400  # 每天
        
        return base * self._interval
    
    def _compute_rollover_time(self) -> float:
        """计算下一次轮转时间"""
        now = datetime.now()
        
        if self._when == 'MIDNIGHT':
            # 计算到明天午夜的时间
            tomorrow = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            from datetime import timedelta
            tomorrow += timedelta(days=1)
            return tomorrow.timestamp()
        
        # 从文件修改时间或当前时间计算
        if self._filename.exists():
            file_time = self._filename.stat().st_mtime
        else:
            file_time = now.timestamp()
        
        return file_time + self._interval_seconds
    
    def should_rollover(self, record: 'LogRecord') -> bool:
        """检查是否需要轮转
        
        Args:
            record: 日志记录
            
        Returns:
            True 表示需要轮转
        """
        return record.timestamp >= self._rollover_at
    
    def do_rollover(self) -> None:
        """执行轮转"""
        if self._file:
            self._file.close()
            self._file = None
        
        # 生成备份文件名（使用时间戳）
        current_time = datetime.now()
        time_suffix = current_time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self._filename}.{time_suffix}"
        
        if self._filename.exists():
            backup_path = Path(backup_name)
            self._filename.rename(backup_path)
            
            if self._compress:
                self._compress_file(backup_path)
        
        # 清理过期备份
        self._cleanup_old_backups()
        
        # 更新下一次轮转时间
        self._rollover_at = self._compute_rollover_time()
        
        # 重新打开文件
        self._open()
    
    def _compress_file(self, filepath: Path) -> None:
        """压缩文件"""
        gz_path = Path(str(filepath) + ".gz")
        try:
            with open(filepath, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            filepath.unlink()
        except Exception:
            pass
    
    def _cleanup_old_backups(self) -> None:
        """清理过期的备份文件"""
        pattern = re.compile(
            rf"^{re.escape(self._filename.name)}\.\d{{8}}_\d{{6}}(\.gz)?$"
        )
        
        backups = []
        for file in self._filename.parent.iterdir():
            if pattern.match(file.name):
                backups.append(file)
        
        # 按修改时间排序，删除旧的
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for old_backup in backups[self._backup_count:]:
            old_backup.unlink()
    
    def emit(self, record: 'LogRecord') -> None:
        """输出日志（带轮转检查）
        
        Args:
            record: 日志记录
        """
        try:
            if self.should_rollover(record):
                self.do_rollover()
            super().emit(record)
        except Exception:
            self.handle_error(record)
