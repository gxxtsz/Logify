"""
JSON 格式化器模块

将日志输出为 JSON 格式，便于日志聚合系统处理
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from .base import BaseFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class JsonFormatter(BaseFormatter):
    """JSON 格式化器
    
    将日志记录转换为 JSON 格式字符串
    """
    
    def __init__(
        self,
        fields: Optional[List[str]] = None,
        indent: Optional[int] = None,
        ensure_ascii: bool = False,
        timestamp_format: str = "iso",
        extra_fields: Optional[Dict[str, Any]] = None,
        json_encoder: Optional[Callable] = None,
        name: str = ""
    ):
        """初始化 JSON 格式化器
        
        Args:
            fields: 要包含的字段列表，为 None 时包含所有字段
            indent: JSON 缩进空格数，为 None 时不缩进
            ensure_ascii: 是否确保 ASCII 编码
            timestamp_format: 时间戳格式，"iso" 为 ISO 格式，"epoch" 为时间戳
            extra_fields: 额外添加到每条日志的固定字段
            json_encoder: 自定义 JSON 编码器
            name: 格式化器名称
        """
        super().__init__(name)
        self._fields = fields
        self._indent = indent
        self._ensure_ascii = ensure_ascii
        self._timestamp_format = timestamp_format
        self._extra_fields = extra_fields or {}
        self._json_encoder = json_encoder
    
    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳
        
        Args:
            timestamp: Unix 时间戳
            
        Returns:
            格式化后的时间字符串
        """
        if self._timestamp_format == "epoch":
            return str(timestamp)
        
        # 默认使用 ISO 格式
        dt = datetime.fromtimestamp(timestamp)
        return dt.isoformat()
    
    def _build_log_dict(self, record: 'LogRecord') -> Dict[str, Any]:
        """构建日志字典
        
        Args:
            record: 日志记录
            
        Returns:
            日志数据字典
        """
        # 基础字段
        all_fields = {
            'timestamp': self._format_timestamp(record.timestamp),
            'level': record.level_name,
            'level_no': record.level,
            'logger': record.name,
            'message': record.message,
            'filename': record.filename,
            'lineno': record.lineno,
            'func_name': record.func_name,
            'thread_id': record.thread_id,
            'thread_name': record.thread_name,
            'process_id': record.process_id,
        }
        
        # 添加 extra 字段
        all_fields.update(record.extra)
        all_fields.update(record.kwargs)
        
        # 添加固定的额外字段
        all_fields.update(self._extra_fields)
        
        # 添加异常信息
        if record.exception_info and record.exception_info[0] is not None:
            all_fields['exception'] = self.format_exception(record)
        
        # 如果指定了字段列表，只返回指定的字段
        if self._fields:
            return {k: all_fields[k] for k in self._fields if k in all_fields}
        
        return all_fields
    
    def format(self, record: 'LogRecord') -> str:
        """格式化日志记录为 JSON 字符串
        
        Args:
            record: 待格式化的日志记录
            
        Returns:
            JSON 格式的字符串
        """
        log_dict = self._build_log_dict(record)
        
        try:
            return json.dumps(
                log_dict,
                indent=self._indent,
                ensure_ascii=self._ensure_ascii,
                default=self._json_encoder or str
            )
        except (TypeError, ValueError) as e:
            # 编码失败时返回基本信息
            return json.dumps({
                'timestamp': self._format_timestamp(record.timestamp),
                'level': record.level_name,
                'message': str(record.message),
                'error': f'JSON encoding failed: {e}'
            })
    
    def __repr__(self) -> str:
        return f"<JsonFormatter(fields={self._fields})>"
