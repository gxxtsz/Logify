"""
颜色格式化器模块

为控制台输出添加颜色支持
"""

import sys
from typing import TYPE_CHECKING, Dict, Optional

from .text import TextFormatter
from ..core.levels import LogLevel

if TYPE_CHECKING:
    from ..core.record import LogRecord


# ANSI 颜色代码
class Colors:
    """ANSI 颜色代码常量"""
    RESET = "\033[0m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # 样式
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"


# 默认级别颜色映射
DEFAULT_LEVEL_COLORS: Dict[int, str] = {
    LogLevel.DEBUG: Colors.CYAN,
    LogLevel.INFO: Colors.GREEN,
    LogLevel.WARNING: Colors.YELLOW,
    LogLevel.ERROR: Colors.RED,
    LogLevel.CRITICAL: Colors.BRIGHT_RED + Colors.BOLD,
}


class ColorFormatter(TextFormatter):
    """颜色格式化器
    
    继承自 TextFormatter，添加 ANSI 颜色代码支持
    仅在支持颜色的终端中有效
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        level_colors: Optional[Dict[int, str]] = None,
        colorize_message: bool = True,
        colorize_level: bool = True,
        force_colors: bool = False,
        name: str = ""
    ):
        """初始化颜色格式化器
        
        Args:
            fmt: 格式化模板字符串
            datefmt: 日期时间格式字符串
            level_colors: 日志级别到颜色的映射
            colorize_message: 是否为消息添加颜色
            colorize_level: 是否为级别名称添加颜色
            force_colors: 是否强制使用颜色（忽略终端检测）
            name: 格式化器名称
        """
        from .text import DEFAULT_FORMAT, DEFAULT_DATE_FORMAT
        
        super().__init__(
            fmt=fmt or DEFAULT_FORMAT,
            datefmt=datefmt or DEFAULT_DATE_FORMAT,
            name=name
        )
        
        self._level_colors = level_colors or DEFAULT_LEVEL_COLORS.copy()
        self._colorize_message = colorize_message
        self._colorize_level = colorize_level
        self._force_colors = force_colors
    
    def _supports_color(self) -> bool:
        """检测终端是否支持颜色
        
        Returns:
            True 表示支持颜色
        """
        if self._force_colors:
            return True
        
        import os
        
        # 检测 PyCharm / IntelliJ IDEA 环境
        if os.environ.get('PYCHARM_HOSTED') == '1' or 'IDEA' in os.environ.get('TERMINAL_EMULATOR', ''):
            return True
        
        # 检测 VS Code 环境
        if os.environ.get('TERM_PROGRAM') == 'vscode':
            return True
        
        # 检查是否是 TTY
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return True
        
        # Windows 特殊处理
        if sys.platform == 'win32':
            try:
                return bool(
                    os.environ.get('TERM') or 
                    os.environ.get('ANSICON') or 
                    os.environ.get('WT_SESSION') or  # Windows Terminal
                    os.environ.get('COLORTERM')
                )
            except Exception:
                pass
        
        return False
    
    def _get_level_color(self, level: int) -> str:
        """获取日志级别对应的颜色
        
        Args:
            level: 日志级别
            
        Returns:
            ANSI 颜色代码
        """
        return self._level_colors.get(level, "")
    
    def _colorize(self, text: str, color: str) -> str:
        """为文本添加颜色
        
        Args:
            text: 原始文本
            color: ANSI 颜色代码
            
        Returns:
            带颜色的文本
        """
        if not color:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    def format(self, record: 'LogRecord') -> str:
        """格式化日志记录（带颜色）
        
        Args:
            record: 待格式化的日志记录
            
        Returns:
            带颜色的格式化字符串
        """
        # 不支持颜色时使用父类格式化
        if not self._supports_color():
            return super().format(record)
        
        color = self._get_level_color(record.level)
        
        # 获取格式化字典
        format_dict = self._get_format_dict(record)
        
        # 为级别名称添加颜色
        if self._colorize_level:
            format_dict['levelname'] = self._colorize(format_dict['levelname'], color)
        
        # 为消息添加颜色
        if self._colorize_message:
            format_dict['message'] = self._colorize(format_dict['message'], color)
        
        try:
            result = self._fmt % format_dict
        except (KeyError, ValueError, TypeError):
            result = f"{format_dict['asctime']} - {format_dict['name']} - {format_dict['levelname']} - {format_dict['message']}"
        
        # 添加异常信息（红色）
        exc_text = self.format_exception(record)
        if exc_text:
            result = f"{result}\n{self._colorize(exc_text, Colors.RED)}"
        
        return result
    
    def set_level_color(self, level: int, color: str) -> None:
        """设置日志级别的颜色
        
        Args:
            level: 日志级别
            color: ANSI 颜色代码
        """
        self._level_colors[level] = color
    
    def __repr__(self) -> str:
        return f"<ColorFormatter(colorize_message={self._colorize_message})>"
