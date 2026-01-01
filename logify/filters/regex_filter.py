"""
正则表达式过滤器模块

基于正则表达式匹配消息内容的过滤
"""

import re
from typing import TYPE_CHECKING, Pattern, Union

from .base import BaseFilter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class RegexFilter(BaseFilter):
    """正则表达式过滤器
    
    根据正则表达式匹配日志消息，可配置为匹配时通过或匹配时拒绝
    """
    
    def __init__(
        self,
        pattern: Union[str, Pattern],
        match_pass: bool = True,
        flags: int = 0,
        name: str = ""
    ):
        """初始化正则过滤器
        
        Args:
            pattern: 正则表达式模式（字符串或已编译的 Pattern）
            match_pass: True 表示匹配时通过，False 表示匹配时拒绝
            flags: 正则表达式标志（如 re.IGNORECASE）
            name: 过滤器名称
        """
        super().__init__(name)
        
        if isinstance(pattern, str):
            self._pattern = re.compile(pattern, flags)
        else:
            self._pattern = pattern
        
        self._match_pass = match_pass
    
    @property
    def pattern(self) -> Pattern:
        """获取正则表达式模式"""
        return self._pattern
    
    @property
    def match_pass(self) -> bool:
        """获取匹配行为"""
        return self._match_pass
    
    def filter(self, record: 'LogRecord') -> bool:
        """过滤日志记录
        
        Args:
            record: 待过滤的日志记录
            
        Returns:
            根据匹配结果和 match_pass 设置返回相应值
        """
        message = record.message
        matched = bool(self._pattern.search(message))
        
        # 匹配时通过：matched == True 返回 True
        # 匹配时拒绝：matched == True 返回 False
        return matched if self._match_pass else not matched
    
    def __repr__(self) -> str:
        return f"<RegexFilter(pattern={self._pattern.pattern!r}, match_pass={self._match_pass})>"
