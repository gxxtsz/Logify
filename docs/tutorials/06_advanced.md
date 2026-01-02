# Logify 教程 06：高级用法与最佳实践

> 难度：高级 | 预计阅读时间：25 分钟

## 目录

- [Logger 层级结构](#logger-层级结构)
- [日志传播机制](#日志传播机制)
- [性能优化](#性能优化)
- [结构化日志](#结构化日志)
- [分布式追踪](#分布式追踪)
- [测试中的日志](#测试中的日志)
- [生产环境最佳实践](#生产环境最佳实践)
- [常见问题与解决方案](#常见问题与解决方案)
- [小结](#小结)

---

## Logger 层级结构

Logify 的 Logger 采用层级结构，通过名称中的点号（`.`）建立父子关系。

### 层级命名

```python
from logify import get_logger

# 层级结构
root = get_logger("root")          # 根 Logger
app = get_logger("myapp")          # myapp 的父级是 root
db = get_logger("myapp.db")        # 父级是 myapp
api = get_logger("myapp.api")      # 父级是 myapp
users = get_logger("myapp.api.users")  # 父级是 myapp.api
```

### 使用 get_child

```python
from logify import get_logger

# 获取子 Logger
app = get_logger("myapp")
db = app.get_child("db")        # 等同于 get_logger("myapp.db")
api = app.get_child("api")      # 等同于 get_logger("myapp.api")

# 嵌套
users = api.get_child("users")  # 等同于 get_logger("myapp.api.users")
```

### 推荐的命名约定

```python
# 使用模块名作为 Logger 名称
import logging
logger = get_logger(__name__)  # 自动使用模块完整路径

# 例如在 myapp/services/user.py 中
# logger 名称为 "myapp.services.user"
```

### 按模块组织

```python
# myapp/__init__.py
from logify import get_logger
logger = get_logger("myapp")

# myapp/db/__init__.py
from logify import get_logger
logger = get_logger("myapp.db")

# myapp/api/routes.py
from logify import get_logger
logger = get_logger("myapp.api.routes")
```

---

## 日志传播机制

子 Logger 的日志会向上传播到父 Logger 的处理器。

### 传播流程

```
myapp.api.users 记录日志
    ↓
myapp.api.users 的处理器处理
    ↓ (propagate=True)
myapp.api 的处理器处理
    ↓ (propagate=True)
myapp 的处理器处理
    ↓ (propagate=True)
root 的处理器处理
```

### 控制传播

```python
from logify import get_logger, ConsoleHandler

# 设置根 Logger
root = get_logger("root")
root.add_handler(ConsoleHandler())

# 子 Logger 默认会传播到 root
app = get_logger("myapp")
app.info("这条会显示在 root 的处理器中")

# 禁用传播
app.propagate = False
app.add_handler(ConsoleHandler())
app.info("这条只会显示在 myapp 的处理器中")
```

### 避免重复日志

```python
from logify import get_logger, ConsoleHandler

root = get_logger("root")
root.add_handler(ConsoleHandler())

app = get_logger("myapp")
app.add_handler(ConsoleHandler())

# 问题：日志会显示两次！
app.info("Hello")  # 一次在 app，一次传播到 root

# 解决方案 1：禁用传播
app.propagate = False

# 解决方案 2：只在 root 配置处理器
app.remove_handler(app.handlers[0])
```

### 利用传播实现集中日志

```python
from logify import get_logger, ConsoleHandler, FileHandler

# 只在 root 配置处理器
root = get_logger("root")
root.add_handler(ConsoleHandler())
root.add_handler(FileHandler("app.log"))

# 所有子 Logger 自动获得日志能力
db_logger = get_logger("myapp.db")
api_logger = get_logger("myapp.api")

# 不需要为每个子 Logger 配置处理器
db_logger.info("数据库操作")   # 会传播到 root 的处理器
api_logger.info("API 调用")   # 会传播到 root 的处理器
```

---

## 性能优化

### 1. 延迟格式化

```python
from logify import get_logger

logger = get_logger("myapp")

# 不好：总是执行格式化
logger.debug("User data: " + str(expensive_operation()))

# 好：只有在 DEBUG 级别启用时才格式化
logger.debug("User data: %s", expensive_operation())

# 更好：先检查级别
if logger.is_enabled_for(LogLevel.DEBUG):
    logger.debug("User data: %s", expensive_operation())
```

### 2. 使用异步处理器

```python
from logify import get_logger, AsyncHandler, FileHandler

logger = get_logger("myapp")

# 同步文件处理会阻塞
file_handler = FileHandler("app.log")

# 使用异步包装，避免阻塞
async_handler = AsyncHandler(file_handler, queue_size=10000)
logger.add_handler(async_handler)
```

### 3. 批量处理

```python
from logify import BaseHandler, LogRecord
from typing import List
import time

class BatchHandler(BaseHandler):
    """批量处理器，累积日志后批量发送"""
    
    def __init__(self, batch_size=100, flush_interval=5.0, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: List[LogRecord] = []
        self._last_flush = time.time()
    
    def emit(self, record: LogRecord) -> None:
        self._buffer.append(record)
        
        if (len(self._buffer) >= self.batch_size or 
            time.time() - self._last_flush > self.flush_interval):
            self._flush_buffer()
    
    def _flush_buffer(self) -> None:
        if self._buffer:
            # 批量发送
            self._send_batch(self._buffer)
            self._buffer.clear()
            self._last_flush = time.time()
    
    def _send_batch(self, records: List[LogRecord]) -> None:
        # 实现批量发送逻辑
        pass
    
    def flush(self) -> None:
        self._flush_buffer()
```

### 4. 采样高频日志

```python
import random
from logify import BaseFilter, LogRecord

class SamplingFilter(BaseFilter):
    """采样过滤器，减少高频日志"""
    
    def __init__(self, rate=0.1, name=""):
        super().__init__(name)
        self.rate = rate
    
    def filter(self, record: LogRecord) -> bool:
        # 只保留指定比例的日志
        return random.random() < self.rate

# 对 DEBUG 日志采样 10%
debug_handler = ConsoleHandler(level=LogLevel.DEBUG)
debug_handler.add_filter(SamplingFilter(rate=0.1))
```

### 5. 避免循环中大量日志

```python
from logify import get_logger

logger = get_logger("myapp")

# 不好：循环中大量日志
for i in range(10000):
    logger.debug("Processing item %d", i)

# 好：汇总日志
processed = 0
for i in range(10000):
    processed += 1
    if processed % 1000 == 0:
        logger.info("Processed %d items", processed)

logger.info("Total processed: %d items", processed)
```

---

## 结构化日志

结构化日志便于搜索、分析和监控。

### 使用 JsonFormatter

```python
from logify import get_logger, FileHandler, JsonFormatter

logger = get_logger("myapp")

handler = FileHandler("app.json")
handler.formatter = JsonFormatter(
    fields=["timestamp", "level", "logger", "message"],
    extra_fields={
        "service": "user-service",
        "version": "1.0.0"
    }
)
logger.add_handler(handler)

# 记录结构化数据
logger.info("用户登录", extra={
    "user_id": 12345,
    "ip": "192.168.1.100",
    "method": "oauth"
})
```

输出：

```json
{
    "timestamp": "2026-01-02T10:30:45",
    "level": "INFO",
    "logger": "myapp",
    "message": "用户登录",
    "service": "user-service",
    "version": "1.0.0",
    "user_id": 12345,
    "ip": "192.168.1.100",
    "method": "oauth"
}
```

### 统一上下文

```python
from logify import get_logger

logger = get_logger("myapp")

# 设置全局上下文
logger.set_extra(
    service="user-service",
    environment="production",
    host="server-01"
)

# 所有日志都包含这些字段
logger.info("应用启动")
logger.info("处理请求")
```

### 请求级上下文

```python
import uuid
from logify import get_logger

logger = get_logger("myapp")

def process_request(request):
    request_id = str(uuid.uuid4())
    user_id = request.user.id
    
    with logger.context(request_id=request_id, user_id=user_id):
        logger.info("开始处理请求")
        
        # 业务逻辑
        result = do_business_logic(request)
        
        logger.info("请求处理完成", extra={"result": result})
    
    return result
```

---

## 分布式追踪

在微服务架构中，追踪请求跨服务的流转。

### 传递追踪 ID

```python
import uuid
from logify import get_logger

logger = get_logger("myapp")

def handle_request(request):
    # 从请求头获取或生成追踪 ID
    trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    
    with logger.context(trace_id=trace_id, span_id=span_id):
        logger.info("收到请求")
        
        # 调用其他服务时传递追踪 ID
        response = call_service(
            "http://other-service/api",
            headers={"X-Trace-ID": trace_id}
        )
        
        logger.info("请求完成")
```

### 结合 OpenTelemetry

```python
from opentelemetry import trace
from logify import BaseFilter, LogRecord

class TraceContextFilter(BaseFilter):
    """从 OpenTelemetry 获取追踪上下文"""
    
    def filter(self, record: LogRecord) -> bool:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        
        if ctx.is_valid:
            record.extra['trace_id'] = format(ctx.trace_id, '032x')
            record.extra['span_id'] = format(ctx.span_id, '016x')
        
        return True
```

---

## 测试中的日志

### 使用 LoggerManager.reset()

```python
import pytest
from logify import LoggerManager, get_logger

@pytest.fixture(autouse=True)
def reset_loggers():
    """每个测试前重置 Logger 状态"""
    yield
    LoggerManager.reset()
```

### 捕获日志进行断言

```python
from logify import get_logger, BaseHandler, LogRecord
from typing import List

class CaptureHandler(BaseHandler):
    """捕获日志用于测试"""
    
    def __init__(self):
        super().__init__()
        self.records: List[LogRecord] = []
    
    def emit(self, record: LogRecord) -> None:
        self.records.append(record)
    
    def clear(self) -> None:
        self.records.clear()


def test_user_login():
    logger = get_logger("myapp")
    capture = CaptureHandler()
    logger.add_handler(capture)
    
    # 执行操作
    login_user("alice")
    
    # 断言日志
    assert len(capture.records) == 1
    assert capture.records[0].level_name == "INFO"
    assert "alice" in capture.records[0].message
```

### 禁用日志输出

```python
import pytest
from logify import get_logger

@pytest.fixture
def quiet_logger():
    """禁用日志输出"""
    logger = get_logger("myapp")
    logger.disabled = True
    yield logger
    logger.disabled = False


def test_something(quiet_logger):
    # 测试过程中不会有日志输出
    quiet_logger.info("这条不会显示")
```

---

## 生产环境最佳实践

### 1. 日志级别策略

```python
# 生产环境建议配置
{
    "loggers": {
        "root": {"level": "INFO"},
        "myapp": {"level": "INFO"},
        "myapp.debug": {"level": "WARNING"},
        "urllib3": {"level": "WARNING"},
        "requests": {"level": "WARNING"}
    }
}
```

### 2. 日志轮转

```python
from logify import get_logger, RotatingFileHandler, TimedRotatingFileHandler

logger = get_logger("myapp")

# 按大小轮转（推荐单文件 50-100MB）
size_handler = RotatingFileHandler(
    filename="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    compress=True
)

# 按时间轮转（每天午夜）
time_handler = TimedRotatingFileHandler(
    filename="/var/log/myapp/app.log",
    when="MIDNIGHT",
    backup_count=30,
    compress=True
)
```

### 3. 分离错误日志

```python
from logify import get_logger, FileHandler, RotatingFileHandler, LogLevel

logger = get_logger("myapp")

# 所有日志
all_handler = RotatingFileHandler(
    filename="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,
    backup_count=10
)
all_handler.level = LogLevel.DEBUG

# 仅错误日志
error_handler = RotatingFileHandler(
    filename="/var/log/myapp/error.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=30
)
error_handler.level = LogLevel.ERROR

logger.add_handler(all_handler)
logger.add_handler(error_handler)
```

### 4. 敏感信息过滤

```python
import re
from logify import BaseFilter, LogRecord

class SensitiveDataFilter(BaseFilter):
    """过滤敏感数据"""
    
    PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[\w]+', 'password=***'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+', 'api_key=***'),
        (r'\b\d{16}\b', '****-****-****-****'),  # 信用卡号
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***'),  # 邮箱
    ]
    
    def filter(self, record: LogRecord) -> bool:
        message = record.msg
        for pattern, replacement in self.PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        return True
```

### 5. 监控和告警

```python
from logify import BaseHandler, LogRecord, LogLevel
import requests

class AlertHandler(BaseHandler):
    """发送告警到监控系统"""
    
    def __init__(self, webhook_url, **kwargs):
        super().__init__(level=LogLevel.ERROR, **kwargs)
        self.webhook_url = webhook_url
    
    def emit(self, record: LogRecord) -> None:
        try:
            payload = {
                "level": record.level_name,
                "message": record.message,
                "logger": record.name,
                "timestamp": record.formatted_time,
                "extra": record.extra
            }
            
            if record.exception_info:
                payload["exception"] = self.format_exception(record)
            
            requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
        except Exception:
            self.handle_error(record)
```

### 6. 完整的生产配置

```json
{
    "version": 1,
    "formatters": {
        "standard": {
            "class": "TextFormatter",
            "format": "%(asctime)s [%(process)d] %(name)s %(levelname)s - %(message)s"
        },
        "json": {
            "class": "JsonFormatter",
            "extra_fields": {
                "service": "myapp",
                "env": "production"
            }
        }
    },
    "filters": {
        "sensitive": {
            "class": "SensitiveDataFilter"
        }
    },
    "handlers": {
        "console": {
            "class": "ConsoleHandler",
            "level": "INFO",
            "formatter": "standard"
        },
        "app_file": {
            "class": "RotatingFileHandler",
            "filename": "/var/log/myapp/app.log",
            "max_bytes": 52428800,
            "backup_count": 10,
            "level": "DEBUG",
            "formatter": "standard",
            "filters": ["sensitive"]
        },
        "error_file": {
            "class": "RotatingFileHandler",
            "filename": "/var/log/myapp/error.log",
            "max_bytes": 10485760,
            "backup_count": 30,
            "level": "ERROR",
            "formatter": "standard"
        },
        "json_file": {
            "class": "TimedRotatingFileHandler",
            "filename": "/var/log/myapp/app.json",
            "when": "MIDNIGHT",
            "backup_count": 7,
            "compress": true,
            "level": "INFO",
            "formatter": "json"
        }
    },
    "loggers": {
        "root": {
            "level": "INFO",
            "handlers": ["console", "app_file", "error_file", "json_file"]
        },
        "myapp": {
            "level": "DEBUG",
            "propagate": true
        },
        "urllib3": {
            "level": "WARNING"
        }
    }
}
```

---

## 常见问题与解决方案

### Q1: 日志不显示

```python
from logify import get_logger, ConsoleHandler

logger = get_logger("myapp")

# 检查 1: 是否添加了处理器？
if not logger.handlers:
    logger.add_handler(ConsoleHandler())

# 检查 2: 日志级别是否正确？
logger.level = LogLevel.DEBUG

# 检查 3: Logger 是否被禁用？
logger.disabled = False
```

### Q2: 日志重复显示

```python
# 原因：子 Logger 有处理器，同时传播到有处理器的父 Logger

# 解决方案 1：禁用传播
logger.propagate = False

# 解决方案 2：只在 root 配置处理器
for handler in logger.handlers[:]:
    logger.remove_handler(handler)
```

### Q3: 日志文件太大

```python
from logify import RotatingFileHandler

# 使用轮转处理器
handler = RotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    compress=True  # 压缩旧日志
)
```

### Q4: 日志写入慢

```python
from logify import AsyncHandler, FileHandler

# 使用异步处理器
file_handler = FileHandler("app.log")
async_handler = AsyncHandler(file_handler, queue_size=10000)
logger.add_handler(async_handler)

# 记得在程序结束时刷新
import atexit
atexit.register(async_handler.flush)
atexit.register(async_handler.close)
```

### Q5: 多进程日志问题

```python
# 方案 1：每个进程写不同文件
import os
handler = FileHandler(f"app.{os.getpid()}.log")

# 方案 2：使用 QueueHandler（需自行实现）
# 所有进程写入队列，单独进程处理

# 方案 3：使用外部日志服务
handler = HTTPHandler(url="http://log-service/api/logs")
```

---

## 小结

在本教程中，你学会了：

1. ✅ Logger 层级结构和命名约定
2. ✅ 日志传播机制的控制
3. ✅ 性能优化技巧
4. ✅ 结构化日志的实现
5. ✅ 分布式追踪集成
6. ✅ 测试中的日志处理
7. ✅ 生产环境配置最佳实践
8. ✅ 常见问题的解决方案

### 恭喜！

你已经完成了 Logify 的全部教程！现在你已经掌握了：

- 基础：快速入门、日志级别、基本使用
- 中级：格式化器、处理器、过滤器、配置管理
- 高级：性能优化、结构化日志、生产部署

---

## 附录：快速参考

### 常用导入

```python
from logify import (
    # 核心
    get_logger, LogLevel, LogRecord,
    DEBUG, INFO, WARNING, ERROR, CRITICAL,
    
    # 格式化器
    TextFormatter, JsonFormatter, ColorFormatter,
    
    # 处理器
    ConsoleHandler, FileHandler,
    RotatingFileHandler, TimedRotatingFileHandler,
    AsyncHandler,
    
    # 过滤器
    LevelFilter, RegexFilter, ContextFilter,
    
    # 配置
    basic_config, configure_from_file, configure_from_dict
)
```

### 快速配置模板

```python
import logify
from logify import INFO

# 开发环境
logify.basic_config(level=DEBUG)

# 生产环境
logify.basic_config(
    level=INFO,
    filename="/var/log/myapp/app.log",
    format="%(asctime)s [%(process)d] %(levelname)s - %(message)s"
)
```

---

[← 上一篇：配置管理](05_configuration.md) | [返回目录](README.md)
