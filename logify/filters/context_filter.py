"""
上下文过滤器模块

基于上下文信息（如模块名、线程ID、进程ID）的过滤
"""

from typing import TYPE_CHECKING, Callable, Optional, Set, Union

from .base import BaseFilter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class ContextFilter(BaseFilter):
    """上下文过滤器
    
    根据日志记录的上下文属性进行过滤，支持多种过滤条件
    """
    
    def __init__(
        self,
        allowed_names: Optional[Set[str]] = None,
        denied_names: Optional[Set[str]] = None,
        allowed_threads: Optional[Set[Union[int, str]]] = None,
        allowed_processes: Optional[Set[int]] = None,
        custom_check: Optional[Callable[['LogRecord'], bool]] = None,
        name: str = ""
    ):
        """初始化上下文过滤器
        
        Args:
            allowed_names: 允许的 Logger 名称集合（为空表示不限制）
            denied_names: 拒绝的 Logger 名称集合
            allowed_threads: 允许的线程 ID 或线程名称集合
            allowed_processes: 允许的进程 ID 集合
            custom_check: 自定义检查函数，接收 LogRecord 返回 bool
            name: 过滤器名称
        """
        super().__init__(name)
        
        self._allowed_names = allowed_names
        self._denied_names = denied_names or set()
        self._allowed_threads = allowed_threads
        self._allowed_processes = allowed_processes
        self._custom_check = custom_check
    
    def filter(self, record: 'LogRecord') -> bool:
        """过滤日志记录
        
        Args:
            record: 待过滤的日志记录
            
        Returns:
            通过所有过滤条件返回 True
        """
        # 检查名称是否被拒绝
        if record.name in self._denied_names:
            return False
        
        # 检查名称是否在允许列表中
        if self._allowed_names and record.name not in self._allowed_names:
            # 检查是否匹配前缀
            name_allowed = any(
                record.name.startswith(allowed + '.')
                for allowed in self._allowed_names
            )
            if not name_allowed and record.name not in self._allowed_names:
                return False
        
        # 检查线程
        if self._allowed_threads:
            thread_match = (
                record.thread_id in self._allowed_threads or
                record.thread_name in self._allowed_threads
            )
            if not thread_match:
                return False
        
        # 检查进程
        if self._allowed_processes:
            if record.process_id not in self._allowed_processes:
                return False
        
        # 执行自定义检查
        if self._custom_check:
            if not self._custom_check(record):
                return False
        
        return True
    
    def allow_name(self, name: str) -> 'ContextFilter':
        """添加允许的 Logger 名称
        
        Args:
            name: Logger 名称
            
        Returns:
            返回自身，支持链式调用
        """
        if self._allowed_names is None:
            self._allowed_names = set()
        self._allowed_names.add(name)
        return self
    
    def deny_name(self, name: str) -> 'ContextFilter':
        """添加拒绝的 Logger 名称
        
        Args:
            name: Logger 名称
            
        Returns:
            返回自身，支持链式调用
        """
        self._denied_names.add(name)
        return self
    
    def __repr__(self) -> str:
        return f"<ContextFilter(allowed_names={self._allowed_names}, denied_names={self._denied_names})>"
