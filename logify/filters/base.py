"""
过滤器基类模块

定义过滤器的抽象基类，所有自定义过滤器都应继承此类
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.record import LogRecord


class BaseFilter(ABC):
    """过滤器抽象基类
    
    所有过滤器必须实现 filter() 方法，返回 True 表示通过过滤，
    返回 False 表示拒绝该日志记录
    """
    
    def __init__(self, name: str = ""):
        """初始化过滤器
        
        Args:
            name: 过滤器名称，用于标识和调试
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def filter(self, record: 'LogRecord') -> bool:
        """过滤日志记录
        
        Args:
            record: 待过滤的日志记录
            
        Returns:
            True 表示通过过滤，False 表示拒绝
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"


class FilterChain:
    """过滤器责任链
    
    按顺序执行多个过滤器，所有过滤器都通过才算通过
    """
    
    def __init__(self):
        """初始化过滤器链"""
        self._filters: list[BaseFilter] = []
    
    def add_filter(self, filter_: BaseFilter) -> 'FilterChain':
        """添加过滤器到链中
        
        Args:
            filter_: 过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        if filter_ not in self._filters:
            self._filters.append(filter_)
        return self
    
    def remove_filter(self, filter_: BaseFilter) -> 'FilterChain':
        """从链中移除过滤器
        
        Args:
            filter_: 要移除的过滤器实例
            
        Returns:
            返回自身，支持链式调用
        """
        if filter_ in self._filters:
            self._filters.remove(filter_)
        return self
    
    def filter(self, record: 'LogRecord') -> bool:
        """执行过滤器链
        
        Args:
            record: 待过滤的日志记录
            
        Returns:
            所有过滤器都通过返回 True，任一拒绝返回 False
        """
        for filter_ in self._filters:
            if not filter_.filter(record):
                return False
        return True
    
    def clear(self) -> None:
        """清空过滤器链"""
        self._filters.clear()
    
    @property
    def filters(self) -> list[BaseFilter]:
        """获取所有过滤器"""
        return self._filters.copy()
    
    def __len__(self) -> int:
        return len(self._filters)
    
    def __repr__(self) -> str:
        return f"<FilterChain(filters={len(self._filters)})>"
