"""
Logger 类模块

提供日志记录的核心 API
"""

import sys
import functools
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING

from ..core.levels import LogLevel
from ..core.record import LogRecord
from ..filters.base import BaseFilter, FilterChain
from ..handlers.base import BaseHandler, HandlerChain

if TYPE_CHECKING:
    from ..core.manager import LoggerManager


class Logger:
    """日志记录器
    
    提供日志记录的主要接口
    
    使用示例：
    ```python
    from logify import get_logger
    
    logger = get_logger("myapp")
    logger.info("Application started")
    logger.error("Error occurred", exc_info=True)
    ```
    """
    
    def __init__(
        self,
        name: str = "root",
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        manager: Optional['LoggerManager'] = None
    ):
        """初始化 Logger
        
        Args:
            name: Logger 名称
            level: 最低日志级别
            manager: Logger 管理器
        """
        self._name = name
        self._level = level if isinstance(level, int) else level.value
        self._manager = manager
        self._parent: Optional['Logger'] = None
        self._propagate = True
        
        self._handler_chain = HandlerChain()
        self._filter_chain = FilterChain()
        
        self._disabled = False
        self._extra: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """获取 Logger 名称"""
        return self._name
    
    @property
    def level(self) -> int:
        """获取日志级别"""
        return self._level
    
    @level.setter
    def level(self, value: Union[LogLevel, int]) -> None:
        """设置日志级别"""
        self._level = value if isinstance(value, int) else value.value
    
    @property
    def parent(self) -> Optional['Logger']:
        """获取父 Logger"""
        return self._parent
    
    @parent.setter
    def parent(self, value: Optional['Logger']) -> None:
        """设置父 Logger"""
        self._parent = value
    
    @property
    def propagate(self) -> bool:
        """是否向父 Logger 传播日志"""
        return self._propagate
    
    @propagate.setter
    def propagate(self, value: bool) -> None:
        """设置是否传播"""
        self._propagate = value
    
    @property
    def disabled(self) -> bool:
        """是否禁用"""
        return self._disabled
    
    @disabled.setter
    def disabled(self, value: bool) -> None:
        """设置是否禁用"""
        self._disabled = value
    
    @property
    def handlers(self) -> List[BaseHandler]:
        """获取所有处理器"""
        return self._handler_chain.handlers
    
    def add_handler(self, handler: BaseHandler) -> 'Logger':
        """添加处理器
        
        Args:
            handler: 处理器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._handler_chain.add_handler(handler)
        return self
    
    def remove_handler(self, handler: BaseHandler) -> 'Logger':
        """移除处理器
        
        Args:
            handler: 处理器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._handler_chain.remove_handler(handler)
        return self
    
    def add_filter(self, filter_: BaseFilter) -> 'Logger':
        """添加过滤器
        
        Args:
            filter_: 过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._filter_chain.add_filter(filter_)
        return self
    
    def remove_filter(self, filter_: BaseFilter) -> 'Logger':
        """移除过滤器
        
        Args:
            filter_: 过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        self._filter_chain.remove_filter(filter_)
        return self
    
    def set_extra(self, **kwargs) -> 'Logger':
        """设置额外的上下文数据
        
        这些数据会添加到每条日志记录中
        
        Args:
            **kwargs: 键值对数据
            
        Returns:
            返回自身，支持链式调用
        """
        self._extra.update(kwargs)
        return self
    
    def clear_extra(self) -> 'Logger':
        """清除额外的上下文数据
        
        Returns:
            返回自身，支持链式调用
        """
        self._extra.clear()
        return self
    
    def is_enabled_for(self, level: Union[LogLevel, int]) -> bool:
        """检查是否启用指定级别
        
        Args:
            level: 日志级别
            
        Returns:
            True 表示启用
        """
        if self._disabled:
            return False
        
        level_value = level if isinstance(level, int) else level.value
        return level_value >= self._level
    
    def _make_record(
        self,
        level: LogLevel,
        msg: str,
        args: tuple,
        exc_info: Optional[tuple] = None,
        **kwargs
    ) -> LogRecord:
        """创建日志记录
        
        Args:
            level: 日志级别
            msg: 日志消息
            args: 格式化参数
            exc_info: 异常信息
            **kwargs: 附加数据
            
        Returns:
            LogRecord 实例
        """
        # 合并 extra 数据
        extra = {**self._extra}
        if 'extra' in kwargs:
            extra.update(kwargs.pop('extra'))
        
        return LogRecord(
            name=self._name,
            level=level,
            msg=msg,
            args=args,
            kwargs=kwargs,
            exception_info=exc_info,
            extra=extra
        )
    
    def _log(
        self,
        level: LogLevel,
        msg: str,
        *args,
        exc_info: bool = False,
        stack_info: bool = False,
        **kwargs
    ) -> None:
        """内部日志记录方法
        
        Args:
            level: 日志级别
            msg: 日志消息
            *args: 格式化参数
            exc_info: 是否包含异常信息
            stack_info: 是否包含堆栈信息（暂不支持）
            **kwargs: 附加数据
        """
        if not self.is_enabled_for(level):
            return
        
        # 获取异常信息
        exception_info = None
        if exc_info:
            if isinstance(exc_info, tuple):
                exception_info = exc_info
            else:
                exception_info = sys.exc_info()
        
        # 创建日志记录
        record = self._make_record(level, msg, args, exception_info, **kwargs)
        
        # 通过过滤器
        if not self._filter_chain.filter(record):
            return
        
        # 分发到处理器
        self._handle(record)
    
    def _handle(self, record: LogRecord) -> None:
        """处理日志记录
        
        Args:
            record: 日志记录
        """
        # 调用本地处理器
        self._handler_chain.handle(record)
        
        # 向父 Logger 传播
        if self._propagate and self._parent:
            self._parent._handle(record)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """记录 DEBUG 级别日志
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        self._log(LogLevel.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """记录 INFO 级别日志
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        self._log(LogLevel.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """记录 WARNING 级别日志
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        self._log(LogLevel.WARNING, msg, *args, **kwargs)
    
    def warn(self, msg: str, *args, **kwargs) -> None:
        """warning 的别名"""
        self.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """记录 ERROR 级别日志
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        self._log(LogLevel.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """记录 CRITICAL 级别日志
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        self._log(LogLevel.CRITICAL, msg, *args, **kwargs)
    
    def fatal(self, msg: str, *args, **kwargs) -> None:
        """critical 的别名"""
        self.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """记录带异常信息的 ERROR 级别日志
        
        应在 except 块中调用
        
        Args:
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        kwargs['exc_info'] = True
        self.error(msg, *args, **kwargs)
    
    def log(self, level: Union[LogLevel, int], msg: str, *args, **kwargs) -> None:
        """记录指定级别的日志
        
        Args:
            level: 日志级别
            msg: 日志消息
            *args: 格式化参数
            **kwargs: 附加数据
        """
        if isinstance(level, int):
            # 尝试转换为 LogLevel
            for log_level in LogLevel:
                if log_level.value == level:
                    level = log_level
                    break
            else:
                level = LogLevel.DEBUG
        
        self._log(level, msg, *args, **kwargs)
    
    @contextmanager
    def context(self, **kwargs):
        """上下文管理器，临时添加额外数据
        
        Usage:
            with logger.context(request_id="123"):
                logger.info("Processing request")
        
        Args:
            **kwargs: 临时上下文数据
        """
        old_extra = self._extra.copy()
        self._extra.update(kwargs)
        try:
            yield self
        finally:
            self._extra = old_extra
    
    def trace(self, func: Optional[Callable] = None, *, level: LogLevel = LogLevel.DEBUG):
        """函数调用追踪装饰器
        
        记录函数的进入和退出
        
        Usage:
            @logger.trace
            def my_function():
                pass
            
            @logger.trace(level=LogLevel.INFO)
            def another_function():
                pass
        
        Args:
            func: 被装饰的函数
            level: 日志级别
        """
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                func_name = fn.__name__
                self._log(level, f"Entering {func_name}")
                try:
                    result = fn(*args, **kwargs)
                    self._log(level, f"Exiting {func_name}")
                    return result
                except Exception as e:
                    self._log(LogLevel.ERROR, f"Exception in {func_name}: {e}", exc_info=True)
                    raise
            return wrapper
        
        if func is not None:
            return decorator(func)
        return decorator
    
    def flush(self) -> None:
        """刷新所有处理器"""
        self._handler_chain.flush()
    
    def close(self) -> None:
        """关闭所有处理器"""
        self._handler_chain.close()
    
    def get_child(self, suffix: str) -> 'Logger':
        """获取子 Logger
        
        Args:
            suffix: 子 Logger 名称后缀
            
        Returns:
            子 Logger 实例
        """
        if self._manager:
            child_name = f"{self._name}.{suffix}" if self._name != "root" else suffix
            return self._manager.get_logger(child_name)
        
        # 没有管理器时创建独立的子 Logger
        child = Logger(f"{self._name}.{suffix}", self._level)
        child.parent = self
        return child
    
    def __repr__(self) -> str:
        level_name = LogLevel.get_name(self._level)
        return f"<Logger(name={self._name!r}, level={level_name})>"
