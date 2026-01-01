"""
网络处理器模块

通过网络发送日志（支持 HTTP、TCP、UDP 等协议）
"""

import json
import socket
import threading
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import URLError

from .base import BaseHandler
from ..core.levels import LogLevel
from ..formatters.base import BaseFormatter
from ..formatters.json_formatter import JsonFormatter

if TYPE_CHECKING:
    from ..core.record import LogRecord


class NetworkHandler(BaseHandler):
    """网络处理器基类
    
    通过网络发送日志记录
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        timeout: float = 5.0,
        name: str = ""
    ):
        """初始化网络处理器
        
        Args:
            host: 目标主机
            port: 目标端口
            level: 最低日志级别
            formatter: 格式化器，默认使用 JsonFormatter
            timeout: 连接超时时间（秒）
            name: 处理器名称
        """
        if formatter is None:
            formatter = JsonFormatter()
        
        super().__init__(level=level, formatter=formatter, name=name)
        
        self._host = host
        self._port = port
        self._timeout = timeout
    
    @property
    def host(self) -> str:
        """获取主机地址"""
        return self._host
    
    @property
    def port(self) -> int:
        """获取端口号"""
        return self._port
    
    def emit(self, record: 'LogRecord') -> None:
        """发送日志（子类需要实现）"""
        raise NotImplementedError


class TCPHandler(NetworkHandler):
    """TCP 网络处理器
    
    通过 TCP 连接发送日志
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        timeout: float = 5.0,
        name: str = ""
    ):
        super().__init__(
            host=host,
            port=port,
            level=level,
            formatter=formatter,
            timeout=timeout,
            name=name
        )
        
        self._socket: Optional[socket.socket] = None
        self._socket_lock = threading.Lock()
    
    def _connect(self) -> socket.socket:
        """建立 TCP 连接"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._timeout)
        sock.connect((self._host, self._port))
        return sock
    
    def _get_socket(self) -> socket.socket:
        """获取或创建 socket 连接"""
        with self._socket_lock:
            if self._socket is None:
                self._socket = self._connect()
            return self._socket
    
    def _close_socket(self) -> None:
        """关闭 socket 连接"""
        with self._socket_lock:
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None
    
    def emit(self, record: 'LogRecord') -> None:
        """通过 TCP 发送日志
        
        Args:
            record: 日志记录
        """
        try:
            msg = self.format(record)
            data = (msg + '\n').encode('utf-8')
            
            sock = self._get_socket()
            sock.sendall(data)
            
        except (socket.error, socket.timeout) as e:
            self._close_socket()
            self.handle_error(record)
    
    def close(self) -> None:
        """关闭处理器"""
        super().close()
        self._close_socket()
    
    def __repr__(self) -> str:
        return f"<TCPHandler(host={self._host}, port={self._port})>"


class UDPHandler(NetworkHandler):
    """UDP 网络处理器
    
    通过 UDP 发送日志（无连接）
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        name: str = ""
    ):
        super().__init__(
            host=host,
            port=port,
            level=level,
            formatter=formatter,
            timeout=0,  # UDP 不需要超时
            name=name
        )
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def emit(self, record: 'LogRecord') -> None:
        """通过 UDP 发送日志
        
        Args:
            record: 日志记录
        """
        try:
            msg = self.format(record)
            data = msg.encode('utf-8')
            self._socket.sendto(data, (self._host, self._port))
        except socket.error:
            self.handle_error(record)
    
    def close(self) -> None:
        """关闭处理器"""
        super().close()
        try:
            self._socket.close()
        except Exception:
            pass
    
    def __repr__(self) -> str:
        return f"<UDPHandler(host={self._host}, port={self._port})>"


class HTTPHandler(BaseHandler):
    """HTTP 网络处理器
    
    通过 HTTP POST 请求发送日志
    """
    
    def __init__(
        self,
        url: str,
        method: str = 'POST',
        headers: Optional[Dict[str, str]] = None,
        level: Union[LogLevel, int] = LogLevel.DEBUG,
        formatter: Optional[BaseFormatter] = None,
        timeout: float = 5.0,
        batch_size: int = 1,
        auth: Optional[tuple] = None,
        name: str = ""
    ):
        """初始化 HTTP 处理器
        
        Args:
            url: 目标 URL
            method: HTTP 方法
            headers: 自定义请求头
            level: 最低日志级别
            formatter: 格式化器
            timeout: 请求超时时间（秒）
            batch_size: 批量发送大小（暂不支持批量）
            auth: 认证信息 (username, password)
            name: 处理器名称
        """
        if formatter is None:
            formatter = JsonFormatter()
        
        super().__init__(level=level, formatter=formatter, name=name)
        
        self._url = url
        self._method = method.upper()
        self._headers = headers or {}
        self._timeout = timeout
        self._batch_size = batch_size
        self._auth = auth
        
        # 设置默认 Content-Type
        if 'Content-Type' not in self._headers:
            self._headers['Content-Type'] = 'application/json'
    
    @property
    def url(self) -> str:
        """获取目标 URL"""
        return self._url
    
    def emit(self, record: 'LogRecord') -> None:
        """通过 HTTP 发送日志
        
        Args:
            record: 日志记录
        """
        try:
            msg = self.format(record)
            data = msg.encode('utf-8')
            
            request = Request(
                self._url,
                data=data,
                headers=self._headers,
                method=self._method
            )
            
            # 添加基本认证
            if self._auth:
                import base64
                credentials = f"{self._auth[0]}:{self._auth[1]}"
                encoded = base64.b64encode(credentials.encode()).decode()
                request.add_header('Authorization', f'Basic {encoded}')
            
            with urlopen(request, timeout=self._timeout) as response:
                # 检查响应状态
                if response.status >= 400:
                    raise URLError(f"HTTP {response.status}")
                    
        except (URLError, Exception):
            self.handle_error(record)
    
    def __repr__(self) -> str:
        return f"<HTTPHandler(url={self._url})>"
