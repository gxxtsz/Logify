"""
Logify Configuration Layer

配置层：加载和解析配置，动态配置日志系统
"""

from .loader import ConfigLoader
from .parser import ConfigParser

__all__ = ['ConfigLoader', 'ConfigParser']
