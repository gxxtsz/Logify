"""
异步处理器模块

异步处理器包装器，实现非阻塞日志写入
"""

import atexit
import queue
import threading
from typing import TYPE_CHECKING, Optional, Union

from .base import BaseHandler
from ..core.levels import LogLevel
from ..formatters.base import BaseFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class AsyncHandler(BaseHandler):
    """异步处理器
    
    将日志记录放入队列，由后台线程异步处理
    用于包装其他处理器，实现非阻塞写入
    """
    
    def __init__(
        self,
        handler: BaseHandler,
        queue_size: int = 10000,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        name: str = ""
    ):
        """初始化异步处理器
        
        Args:
            handler: 被包装的处理器
            queue_size: 队列最大容量，0 表示无限制
            level: 最低日志级别
            name: 处理器名称
        """
        super().__init__(level=level, formatter=handler.formatter, name=name)
        
        self._handler = handler
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._shutdown = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # 启动后台线程
        self._start()
        
        # 注册退出时清理
        atexit.register(self.close)
    
    @property
    def handler(self) -> BaseHandler:
        """获取被包装的处理器"""
        return self._handler
    
    @property
    def queue_size(self) -> int:
        """获取当前队列大小"""
        return self._queue.qsize()
    
    def _start(self) -> None:
        """启动后台处理线程"""
        self._thread = threading.Thread(
            target=self._process_loop,
            name=f"AsyncHandler-{self.name}",
            daemon=True
        )
        self._thread.start()
    
    def _process_loop(self) -> None:
        """后台处理循环"""
        while not self._shutdown.is_set():
            try:
                # 等待获取日志记录
                record = self._queue.get(timeout=0.5)
                
                if record is None:  # 停止信号
                    break
                
                # 使用被包装的处理器处理
                try:
                    self._handler.handle(record)
                except Exception:
                    pass
                
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception:
                pass
        
        # 处理剩余的日志
        self._flush_queue()
    
    def _flush_queue(self) -> None:
        """清空队列中剩余的日志"""
        while True:
            try:
                record = self._queue.get_nowait()
                if record is not None:
                    self._handler.handle(record)
                self._queue.task_done()
            except queue.Empty:
                break
            except Exception:
                pass
    
    def emit(self, record: 'LogRecord') -> None:
        """将日志记录放入队列
        
        Args:
            record: 日志记录
        """
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            # 队列满时，丢弃最旧的记录
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def flush(self) -> None:
        """等待队列清空"""
        self._queue.join()
        self._handler.flush()
    
    def close(self) -> None:
        """关闭异步处理器"""
        if self._closed:
            return
        
        super().close()
        
        # 发送停止信号
        self._shutdown.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        
        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        # 关闭被包装的处理器
        self._handler.close()
    
    def __repr__(self) -> str:
        return f"<AsyncHandler(handler={self._handler!r}, queue_size={self._queue.qsize()})>"
