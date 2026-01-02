"""
Logger 管理器模块

管理 Logger 实例的创建、缓存和层级关系
"""

import threading
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.logger import Logger


class LoggerManager:
    """Logger 管理器
    
    采用单例模式，全局管理所有 Logger 实例
    
    功能：
    - 创建和缓存 Logger 实例
    - 管理 Logger 的层级关系（通过名称中的点号分隔）
    - 提供全局配置入口
    """
    
    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'LoggerManager':
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化管理器"""
        if self._initialized:
            return
            
        self._loggers: Dict[str, 'Logger'] = {}
        self._logger_lock = threading.RLock()  # RLock allows recursive acquisition
        self._root_logger: Optional['Logger'] = None
        self._initialized = True
    
    def get_logger(self, name: str = "root") -> 'Logger':
        """获取或创建 Logger 实例
        
        Args:
            name: Logger 名称，支持层级命名（如 "app.module.component"）
            
        Returns:
            Logger 实例
        """
        # 延迟导入避免循环依赖
        from ..api.logger import Logger
        from ..handlers.console import ConsoleHandler
        
        if name in self._loggers:
            return self._loggers[name]
        
        with self._logger_lock:
            # 双重检查
            if name in self._loggers:
                return self._loggers[name]
            
            # 创建新的 Logger
            logger = Logger(name, manager=self)
            
            # 设置父 Logger
            if name != "root":
                parent_name = self._get_parent_name(name)
                logger.parent = self.get_logger(parent_name)
            
            self._loggers[name] = logger
            
            # 保存 root logger 引用，并添加默认控制台处理器
            if name == "root":
                self._root_logger = logger
                # 为 root logger 添加默认的控制台处理器
                logger.add_handler(ConsoleHandler())
            
            return logger
    
    def _get_parent_name(self, name: str) -> str:
        """获取父 Logger 名称
        
        Args:
            name: 当前 Logger 名称
            
        Returns:
            父 Logger 名称
        """
        if '.' in name:
            return name.rsplit('.', 1)[0]
        return "root"
    
    @property
    def root(self) -> 'Logger':
        """获取根 Logger"""
        return self.get_logger("root")
    
    def get_all_loggers(self) -> Dict[str, 'Logger']:
        """获取所有已创建的 Logger
        
        Returns:
            Logger 名称到实例的映射字典
        """
        return self._loggers.copy()
    
    def clear(self) -> None:
        """清除所有 Logger 缓存（主要用于测试）"""
        with self._logger_lock:
            self._loggers.clear()
            self._root_logger = None
    
    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._loggers.clear()
                cls._instance._root_logger = None
                cls._instance._initialized = False
            cls._instance = None


# 全局管理器实例
_manager = LoggerManager()


def get_logger(name: str = "root") -> 'Logger':
    """便捷函数：获取 Logger 实例
    
    Args:
        name: Logger 名称
        
    Returns:
        Logger 实例
    """
    return _manager.get_logger(name)
