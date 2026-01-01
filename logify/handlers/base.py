"""
处理器基类模块

定义处理器的抽象基类，所有自定义处理器都应继承此类
"""

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Union

from ..filters.base import BaseFilter, FilterChain
from ..formatters.base import BaseFormatter
from ..formatters.text import TextFormatter
from ..core.levels import LogLevel

if TYPE_CHECKING:
    from ..core.record import LogRecord


class BaseHandler(ABC):
    """处理器抽象基类
    
    所有处理器必须实现 emit() 方法，将日志记录输出到目标位置
    """
    
    def __init__(
        self,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        name: str = ""
    ):
        """初始化处理器
        
        Args:
            level: 处理器的最低日志级别
            formatter: 格式化器实例
            name: 处理器名称
        """
        self.name = name or self.__class__.__name__
        self._level = level if isinstance(level, int) else level.value
        self._formatter = formatter or TextFormatter()
        self._filter_chain = FilterChain()
        self._lock = threading.RLock()
        self._closed = False
    
    @property
    def level(self) -> int:
        """获取处理器级别"""
        return self._level
    
    @level.setter
    def level(self, value: Union[LogLevel, int]) -> None:
        """设置处理器级别"""
        self._level = value if isinstance(value, int) else value.value
    
    @property
    def formatter(self) -> BaseFormatter:
        """获取格式化器"""
        return self._formatter
    
    @formatter.setter
    def formatter(self, value: BaseFormatter) -> None:
        """设置格式化器"""
        self._formatter = value
    
    def add_filter(self, filter_: BaseFilter) -> 'BaseHandler':
        """添加过滤器
        
        Args:
            filter_: 过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._filter_chain.add_filter(filter_)
        return self
    
    def remove_filter(self, filter_: BaseFilter) -> 'BaseHandler':
        """移除过滤器
        
        Args:
            filter_: 过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._filter_chain.remove_filter(filter_)
        return self
    
    def filter(self, record: 'LogRecord') -> bool:
        """执行过滤
        
        Args:
            record: 日志记录
            
        Returns:
            True 表示通过过滤
        """
        return self._filter_chain.filter(record)
    
    def format(self, record: 'LogRecord') -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的字符串
        """
        return self._formatter.format(record)
    
    def handle(self, record: 'LogRecord') -> bool:
        """处理日志记录
        
        执行级别检查、过滤和输出
        
        Args:
            record: 日志记录
            
        Returns:
            True 表示成功处理
        """
        if self._closed:
            return False
        
        # 级别检查
        if record.level < self._level:
            return False
        
        # 过滤检查
        if not self.filter(record):
            return False
        
        # 执行输出
        with self._lock:
            try:
                self.emit(record)
                return True
            except Exception:
                self.handle_error(record)
                return False
    
    @abstractmethod
    def emit(self, record: 'LogRecord') -> None:
        """输出日志记录
        
        Args:
            record: 日志记录
        """
        pass
    
    def handle_error(self, record: 'LogRecord') -> None:
        """处理输出过程中的错误
        
        Args:
            record: 日志记录
        """
        import sys
        import traceback
        
        try:
            print(f"Error in handler {self.name}:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        except Exception:
            pass
    
    def flush(self) -> None:
        """刷新缓冲区"""
        pass
    
    def close(self) -> None:
        """关闭处理器"""
        self._closed = True
        self.flush()
    
    def __repr__(self) -> str:
        level_name = LogLevel.get_name(self._level)
        return f"<{self.__class__.__name__}(level={level_name})>"


class HandlerChain:
    """处理器责任链
    
    将日志分发到多个处理器
    """
    
    def __init__(self):
        """初始化处理器链"""
        self._handlers: List[BaseHandler] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: BaseHandler) -> 'HandlerChain':
        """添加处理器
        
        Args:
            handler: 处理器实例
            
        Returns:
            返回自身，支持链式调用
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
        return self
    
    def remove_handler(self, handler: BaseHandler) -> 'HandlerChain':
        """移除处理器
        
        Args:
            handler: 处理器实例
            
        Returns:
            返回自身，支持链式调用
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
        return self
    
    def handle(self, record: 'LogRecord') -> int:
        """分发日志到所有处理器
        
        Args:
            record: 日志记录
            
        Returns:
            成功处理的处理器数量
        """
        count = 0
        for handler in self._handlers:
            if handler.handle(record):
                count += 1
        return count
    
    def flush(self) -> None:
        """刷新所有处理器"""
        for handler in self._handlers:
            handler.flush()
    
    def close(self) -> None:
        """关闭所有处理器"""
        for handler in self._handlers:
            handler.close()
    
    @property
    def handlers(self) -> List[BaseHandler]:
        """获取所有处理器"""
        return self._handlers.copy()
    
    def clear(self) -> None:
        """清空处理器链"""
        with self._lock:
            self._handlers.clear()
    
    def __len__(self) -> int:
        return len(self._handlers)
    
    def __repr__(self) -> str:
        return f"<HandlerChain(handlers={len(self._handlers)})>"
