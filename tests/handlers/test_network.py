"""
Tests for logify.handlers.network module

Tests for NetworkHandler, TCPHandler, UDPHandler, and HTTPHandler classes
"""

import socket
import threading
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from logify.handlers.network import NetworkHandler, TCPHandler, UDPHandler, HTTPHandler
from logify.core.levels import LogLevel, DEBUG, INFO, WARNING, ERROR
from logify.core.record import LogRecord
from logify.formatters.text import TextFormatter
from logify.formatters.json_formatter import JsonFormatter


# ============================================
# NetworkHandler Tests
# ============================================

class TestNetworkHandlerInit:
    """Test NetworkHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = NetworkHandler(host="localhost", port=9999)
        assert handler.host == "localhost"
        assert handler.port == 9999
        assert handler.level == DEBUG
        assert handler._timeout == 5.0
        assert isinstance(handler.formatter, JsonFormatter)
    
    def test_custom_level(self):
        """Test initialization with custom level"""
        handler = NetworkHandler(host="localhost", port=9999, level=LogLevel.WARNING)
        assert handler.level == WARNING
    
    def test_custom_formatter(self):
        """Test initialization with custom formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = NetworkHandler(host="localhost", port=9999, formatter=formatter)
        assert handler.formatter is formatter
    
    def test_custom_timeout(self):
        """Test initialization with custom timeout"""
        handler = NetworkHandler(host="localhost", port=9999, timeout=10.0)
        assert handler._timeout == 10.0
    
    def test_custom_name(self):
        """Test initialization with custom name"""
        handler = NetworkHandler(host="localhost", port=9999, name="MyNetworkHandler")
        assert handler.name == "MyNetworkHandler"


class TestNetworkHandlerProperties:
    """Test NetworkHandler properties"""
    
    def test_host_property(self):
        """Test host property"""
        handler = NetworkHandler(host="192.168.1.1", port=9999)
        assert handler.host == "192.168.1.1"
    
    def test_port_property(self):
        """Test port property"""
        handler = NetworkHandler(host="localhost", port=8080)
        assert handler.port == 8080


class TestNetworkHandlerEmit:
    """Test NetworkHandler emit method"""
    
    def test_emit_raises_not_implemented(self):
        """Test emit raises NotImplementedError"""
        handler = NetworkHandler(host="localhost", port=9999)
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        
        with pytest.raises(NotImplementedError):
            handler.emit(record)


# ============================================
# TCPHandler Tests
# ============================================

class TestTCPHandlerInit:
    """Test TCPHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            assert handler.host == "localhost"
            assert handler.port == 9999
            assert handler._socket is None
        finally:
            handler.close()
    
    def test_custom_timeout(self):
        """Test initialization with custom timeout"""
        handler = TCPHandler(host="localhost", port=9999, timeout=15.0)
        try:
            assert handler._timeout == 15.0
        finally:
            handler.close()


class TestTCPHandlerConnect:
    """Test TCPHandler _connect method"""
    
    def test_connect_creates_socket(self):
        """Test _connect creates TCP socket"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            with patch.object(socket.socket, 'connect'):
                sock = handler._connect()
                assert sock.type == socket.SOCK_STREAM
                sock.close()
        finally:
            handler.close()


class TestTCPHandlerGetSocket:
    """Test TCPHandler _get_socket method"""
    
    def test_get_socket_creates_if_none(self):
        """Test _get_socket creates socket if none exists"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            with patch.object(handler, '_connect') as mock_connect:
                mock_socket = Mock()
                mock_connect.return_value = mock_socket
                
                result = handler._get_socket()
                
                mock_connect.assert_called_once()
                assert result is mock_socket
        finally:
            handler.close()
    
    def test_get_socket_reuses_existing(self):
        """Test _get_socket reuses existing socket"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            mock_socket = Mock()
            handler._socket = mock_socket
            
            result = handler._get_socket()
            
            assert result is mock_socket
        finally:
            handler.close()


class TestTCPHandlerCloseSocket:
    """Test TCPHandler _close_socket method"""
    
    def test_close_socket_closes_and_clears(self):
        """Test _close_socket closes socket and sets to None"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            mock_socket = Mock()
            handler._socket = mock_socket
            
            handler._close_socket()
            
            mock_socket.close.assert_called_once()
            assert handler._socket is None
        finally:
            handler.close()
    
    def test_close_socket_when_none(self):
        """Test _close_socket when socket is None"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            handler._close_socket()  # Should not raise
        finally:
            handler.close()


class TestTCPHandlerEmit:
    """Test TCPHandler emit method"""
    
    def test_emit_sends_formatted_message(self):
        """Test emit sends formatted message"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            mock_socket = Mock()
            handler._socket = mock_socket
            
            record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
            handler.emit(record)
            
            mock_socket.sendall.assert_called_once()
            sent_data = mock_socket.sendall.call_args[0][0]
            assert b'\n' in sent_data  # Message ends with newline
        finally:
            handler.close()
    
    def test_emit_handles_socket_error(self):
        """Test emit handles socket error"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            mock_socket = Mock()
            mock_socket.sendall.side_effect = socket.error("Connection failed")
            handler._socket = mock_socket
            
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)  # Should not raise
            
            assert handler._socket is None  # Socket should be closed
        finally:
            handler.close()


class TestTCPHandlerClose:
    """Test TCPHandler close method"""
    
    def test_close_closes_socket(self):
        """Test close closes socket"""
        handler = TCPHandler(host="localhost", port=9999)
        mock_socket = Mock()
        handler._socket = mock_socket
        
        handler.close()
        
        mock_socket.close.assert_called_once()


class TestTCPHandlerRepr:
    """Test TCPHandler __repr__ method"""
    
    def test_repr_format(self):
        """Test __repr__ format"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            repr_str = repr(handler)
            assert "TCPHandler" in repr_str
            assert "localhost" in repr_str
            assert "9999" in repr_str
        finally:
            handler.close()


# ============================================
# UDPHandler Tests
# ============================================

class TestUDPHandlerInit:
    """Test UDPHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = UDPHandler(host="localhost", port=9999)
        try:
            assert handler.host == "localhost"
            assert handler.port == 9999
            assert handler._socket is not None
            assert handler._socket.type == socket.SOCK_DGRAM
        finally:
            handler.close()
    
    def test_timeout_is_zero(self):
        """Test UDP handler has zero timeout"""
        handler = UDPHandler(host="localhost", port=9999)
        try:
            assert handler._timeout == 0
        finally:
            handler.close()


class TestUDPHandlerEmit:
    """Test UDPHandler emit method"""
    
    @patch('socket.socket')
    def test_emit_sends_to_destination(self, mock_socket_class):
        """Test emit sends to destination"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        handler = UDPHandler(host="localhost", port=9999)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
            handler.emit(record)
            
            mock_socket.sendto.assert_called_once()
            call_args = mock_socket.sendto.call_args[0]
            assert call_args[1] == ("localhost", 9999)
        finally:
            handler.close()
    
    @patch('socket.socket')
    def test_emit_handles_socket_error(self, mock_socket_class):
        """Test emit handles socket error"""
        mock_socket = Mock()
        mock_socket.sendto.side_effect = socket.error("Send failed")
        mock_socket_class.return_value = mock_socket
        
        handler = UDPHandler(host="localhost", port=9999)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)  # Should not raise
        finally:
            handler.close()


class TestUDPHandlerClose:
    """Test UDPHandler close method"""
    
    @patch('socket.socket')
    def test_close_closes_socket(self, mock_socket_class):
        """Test close closes socket"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        handler = UDPHandler(host="localhost", port=9999)
        handler.close()
        
        mock_socket.close.assert_called_once()


class TestUDPHandlerRepr:
    """Test UDPHandler __repr__ method"""
    
    def test_repr_format(self):
        """Test __repr__ format"""
        handler = UDPHandler(host="192.168.1.1", port=8080)
        try:
            repr_str = repr(handler)
            assert "UDPHandler" in repr_str
            assert "192.168.1.1" in repr_str
            assert "8080" in repr_str
        finally:
            handler.close()


# ============================================
# HTTPHandler Tests
# ============================================

class TestHTTPHandlerInit:
    """Test HTTPHandler initialization"""
    
    def test_default_initialization(self):
        """Test default initialization"""
        handler = HTTPHandler(url="http://localhost:8080/log")
        assert handler.url == "http://localhost:8080/log"
        assert handler._method == "POST"
        assert handler._timeout == 5.0
        assert handler._batch_size == 1
        assert handler._auth is None
        assert isinstance(handler.formatter, JsonFormatter)
        assert handler._headers["Content-Type"] == "application/json"
    
    def test_custom_method(self):
        """Test initialization with custom method"""
        handler = HTTPHandler(url="http://localhost:8080/log", method="PUT")
        assert handler._method == "PUT"
    
    def test_method_uppercase(self):
        """Test method is converted to uppercase"""
        handler = HTTPHandler(url="http://localhost:8080/log", method="post")
        assert handler._method == "POST"
    
    def test_custom_headers(self):
        """Test initialization with custom headers"""
        headers = {"X-Custom-Header": "value"}
        handler = HTTPHandler(url="http://localhost:8080/log", headers=headers)
        assert handler._headers["X-Custom-Header"] == "value"
        assert handler._headers["Content-Type"] == "application/json"
    
    def test_custom_content_type(self):
        """Test custom Content-Type header"""
        headers = {"Content-Type": "text/plain"}
        handler = HTTPHandler(url="http://localhost:8080/log", headers=headers)
        assert handler._headers["Content-Type"] == "text/plain"
    
    def test_custom_timeout(self):
        """Test initialization with custom timeout"""
        handler = HTTPHandler(url="http://localhost:8080/log", timeout=30.0)
        assert handler._timeout == 30.0
    
    def test_custom_level(self):
        """Test initialization with custom level"""
        handler = HTTPHandler(url="http://localhost:8080/log", level=LogLevel.ERROR)
        assert handler.level == ERROR
    
    def test_custom_formatter(self):
        """Test initialization with custom formatter"""
        formatter = TextFormatter(fmt="%(message)s")
        handler = HTTPHandler(url="http://localhost:8080/log", formatter=formatter)
        assert handler.formatter is formatter
    
    def test_auth_credentials(self):
        """Test initialization with auth credentials"""
        handler = HTTPHandler(url="http://localhost:8080/log", auth=("user", "pass"))
        assert handler._auth == ("user", "pass")
    
    def test_custom_name(self):
        """Test initialization with custom name"""
        handler = HTTPHandler(url="http://localhost:8080/log", name="MyHTTPHandler")
        assert handler.name == "MyHTTPHandler"


class TestHTTPHandlerUrl:
    """Test HTTPHandler url property"""
    
    def test_url_property(self):
        """Test url property"""
        handler = HTTPHandler(url="https://api.example.com/logs")
        assert handler.url == "https://api.example.com/logs"


class TestHTTPHandlerEmit:
    """Test HTTPHandler emit method"""
    
    @patch('logify.handlers.network.urlopen')
    def test_emit_sends_post_request(self, mock_urlopen):
        """Test emit sends POST request"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        handler = HTTPHandler(url="http://localhost:8080/log")
        record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
        handler.emit(record)
        
        mock_urlopen.assert_called_once()
    
    @patch('logify.handlers.network.urlopen')
    def test_emit_with_auth(self, mock_urlopen):
        """Test emit with authentication"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        handler = HTTPHandler(url="http://localhost:8080/log", auth=("user", "pass"))
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        handler.emit(record)
        
        # Check that request was made
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args[0][0]
        assert "Authorization" in request.headers
    
    @patch('logify.handlers.network.urlopen')
    def test_emit_handles_url_error(self, mock_urlopen):
        """Test emit handles URL error"""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection failed")
        
        handler = HTTPHandler(url="http://localhost:8080/log")
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        handler.emit(record)  # Should not raise
    
    @patch('logify.handlers.network.urlopen')
    def test_emit_handles_http_error(self, mock_urlopen):
        """Test emit handles HTTP error status"""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        handler = HTTPHandler(url="http://localhost:8080/log")
        record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
        handler.emit(record)  # Should not raise


class TestHTTPHandlerRepr:
    """Test HTTPHandler __repr__ method"""
    
    def test_repr_format(self):
        """Test __repr__ format"""
        handler = HTTPHandler(url="http://localhost:8080/log")
        repr_str = repr(handler)
        assert "HTTPHandler" in repr_str
        assert "http://localhost:8080/log" in repr_str


# ============================================
# Integration-style Tests (with mocked server)
# ============================================

class TestNetworkHandlerIntegration:
    """Integration tests with mocked network"""
    
    def test_tcp_handler_full_flow(self):
        """Test TCPHandler full flow with mocked socket"""
        handler = TCPHandler(host="localhost", port=9999)
        try:
            with patch.object(handler, '_connect') as mock_connect:
                mock_socket = Mock()
                mock_connect.return_value = mock_socket
                
                # Emit a record
                record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
                handler.emit(record)
                
                # Verify socket was used
                mock_socket.sendall.assert_called_once()
        finally:
            handler.close()
    
    @patch('socket.socket')
    def test_udp_handler_full_flow(self, mock_socket_class):
        """Test UDPHandler full flow"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        handler = UDPHandler(host="localhost", port=9999)
        try:
            record = LogRecord(name="test", level=INFO, msg="Test", filename="test.py", lineno=1)
            handler.emit(record)
            
            mock_socket.sendto.assert_called_once()
        finally:
            handler.close()
    
    @patch('logify.handlers.network.urlopen')
    def test_http_handler_full_flow(self, mock_urlopen):
        """Test HTTPHandler full flow"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        handler = HTTPHandler(url="http://localhost:8080/log")
        
        record = LogRecord(name="test", level=INFO, msg="Test message", filename="test.py", lineno=1)
        handler.emit(record)
        
        # Verify request was made
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args[0][0]
        assert request.method == "POST"


class TestNetworkHandlerLevelFiltering:
    """Test network handlers level filtering"""
    
    def test_tcp_handler_filters_by_level(self):
        """Test TCPHandler filters by level"""
        handler = TCPHandler(host="localhost", port=9999, level=WARNING)
        try:
            mock_socket = Mock()
            handler._socket = mock_socket
            
            record_info = LogRecord(name="test", level=INFO, msg="Info", filename="test.py", lineno=1)
            record_warning = LogRecord(name="test", level=WARNING, msg="Warning", filename="test.py", lineno=1)
            
            handler.handle(record_info)
            handler.handle(record_warning)
            
            # Only warning should be sent
            assert mock_socket.sendall.call_count == 1
        finally:
            handler.close()
    
    @patch('socket.socket')
    def test_udp_handler_filters_by_level(self, mock_socket_class):
        """Test UDPHandler filters by level"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        handler = UDPHandler(host="localhost", port=9999, level=ERROR)
        try:
            record_warning = LogRecord(name="test", level=WARNING, msg="Warning", filename="test.py", lineno=1)
            record_error = LogRecord(name="test", level=ERROR, msg="Error", filename="test.py", lineno=1)
            
            handler.handle(record_warning)
            handler.handle(record_error)
            
            # Only error should be sent
            assert mock_socket.sendto.call_count == 1
        finally:
            handler.close()
