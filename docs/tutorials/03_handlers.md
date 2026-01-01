# Logify 教程 03：处理器详解

> 难度：中级 | 预计阅读时间：20 分钟

## 目录

- [处理器简介](#处理器简介)
- [ConsoleHandler 控制台处理器](#consolehandler-控制台处理器)
- [FileHandler 文件处理器](#filehandler-文件处理器)
- [RotatingFileHandler 按大小轮转](#rotatingfilehandler-按大小轮转)
- [TimedRotatingFileHandler 按时间轮转](#timedrotatingfilehandler-按时间轮转)
- [AsyncHandler 异步处理器](#asynchandler-异步处理器)
- [NetworkHandler 网络处理器](#networkhandler-网络处理器)
- [多处理器配合使用](#多处理器配合使用)
- [自定义处理器](#自定义处理器)
- [小结](#小结)

---

## 处理器简介

处理器（Handler）负责将格式化后的日志发送到目标位置。Logify 提供了多种内置处理器：

| 处理器 | 用途 |
|--------|------|
| `ConsoleHandler` | 输出到控制台 |
| `FileHandler` | 输出到文件 |
| `RotatingFileHandler` | 按文件大小轮转 |
| `TimedRotatingFileHandler` | 按时间周期轮转 |
| `AsyncHandler` | 异步处理（非阻塞） |
| `NetworkHandler` | 网络传输（TCP/UDP/HTTP） |

---

## ConsoleHandler 控制台处理器

最常用的处理器，将日志输出到标准输出或标准错误流。

### 基本使用

```python
from logify import get_logger, ConsoleHandler

logger = get_logger("myapp")

# 创建控制台处理器
console = ConsoleHandler()
logger.add_handler(console)

logger.info("输出到控制台")
```

### 配置选项

```python
import sys
from logify import ConsoleHandler, ColorFormatter, LogLevel

# 指定输出流
console = ConsoleHandler(stream=sys.stdout)

# 设置最低日志级别
console = ConsoleHandler(level=LogLevel.INFO)

# 设置格式化器
console = ConsoleHandler(formatter=ColorFormatter())

# ERROR 及以上级别输出到 stderr
console = ConsoleHandler(use_stderr_for_errors=True)

# 完整配置
console = ConsoleHandler(
    stream=sys.stdout,
    level=LogLevel.DEBUG,
    formatter=ColorFormatter(fmt="[%(levelname)s] %(message)s"),
    use_stderr_for_errors=True
)
```

---

## FileHandler 文件处理器

将日志写入文件，是生产环境最常用的处理器之一。

### 基本使用

```python
from logify import get_logger, FileHandler

logger = get_logger("myapp")

# 创建文件处理器
file_handler = FileHandler("app.log")
logger.add_handler(file_handler)

logger.info("写入文件")
```

### 配置选项

```python
from logify import FileHandler, LogLevel, TextFormatter
from pathlib import Path

# 使用追加模式（默认）
handler = FileHandler("app.log", mode='a')

# 使用覆盖模式
handler = FileHandler("app.log", mode='w')

# 指定编码
handler = FileHandler("app.log", encoding='utf-8')

# 延迟打开文件（首次写入时才打开）
handler = FileHandler("app.log", delay=True)

# 使用 Path 对象
handler = FileHandler(Path("logs") / "app.log")

# 完整配置
handler = FileHandler(
    filename="logs/app.log",
    mode='a',
    encoding='utf-8',
    level=LogLevel.INFO,
    formatter=TextFormatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s"
    ),
    delay=False
)
logger.add_handler(handler)
```

### 确保日志目录存在

```python
from pathlib import Path
from logify import get_logger, FileHandler

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger = get_logger("myapp")
handler = FileHandler(log_dir / "app.log")
logger.add_handler(handler)
```

---

## RotatingFileHandler 按大小轮转

当日志文件达到指定大小时，自动轮转到备份文件。适合需要控制日志文件大小的场景。

### 基本使用

```python
from logify import get_logger, RotatingFileHandler

logger = get_logger("myapp")

handler = RotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)
logger.add_handler(handler)
```

### 轮转机制

当 `app.log` 达到 10MB 时：
1. `app.log.5` 被删除
2. `app.log.4` → `app.log.5`
3. `app.log.3` → `app.log.4`
4. `app.log.2` → `app.log.3`
5. `app.log.1` → `app.log.2`
6. `app.log` → `app.log.1`
7. 创建新的 `app.log`

### 配置选项

```python
from logify import RotatingFileHandler

handler = RotatingFileHandler(
    filename="app.log",
    max_bytes=5 * 1024 * 1024,   # 5MB
    backup_count=10,              # 保留 10 个备份
    encoding='utf-8',
    compress=True                 # 压缩备份文件
)

# 启用压缩后，备份文件为：
# app.log.1.gz, app.log.2.gz, ...
```

### 实际应用示例

```python
from logify import get_logger, RotatingFileHandler, JsonFormatter

# 生产环境日志配置
logger = get_logger("production")

# JSON 格式，每个文件 50MB，保留 30 个备份
handler = RotatingFileHandler(
    filename="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=30,
    compress=True
)
handler.formatter = JsonFormatter()

logger.add_handler(handler)
```

---

## TimedRotatingFileHandler 按时间轮转

按照时间周期轮转日志文件，适合按天、按小时归档日志。

### 基本使用

```python
from logify import get_logger, TimedRotatingFileHandler

logger = get_logger("myapp")

# 每天午夜轮转，保留 30 天
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="MIDNIGHT",
    backup_count=30
)
logger.add_handler(handler)
```

### when 参数选项

| 值 | 说明 | 示例间隔 |
|----|------|----------|
| `'S'` | 秒 | 每秒轮转 |
| `'M'` | 分钟 | 每分钟轮转 |
| `'H'` | 小时 | 每小时轮转 |
| `'D'` | 天 | 每天轮转 |
| `'MIDNIGHT'` | 午夜 | 每天午夜轮转 |

### 配置示例

```python
from logify import TimedRotatingFileHandler

# 每小时轮转
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="H",
    interval=1,
    backup_count=24  # 保留 24 小时
)

# 每 6 小时轮转
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="H",
    interval=6,
    backup_count=28  # 保留 7 天 (4 * 7)
)

# 每天午夜轮转，压缩旧日志
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="MIDNIGHT",
    backup_count=90,  # 保留 90 天
    compress=True
)
```

### 备份文件命名

轮转后的文件使用时间戳命名：

```
app.log                      # 当前日志
app.log.20260102_000000      # 1月2日的备份
app.log.20260101_000000.gz   # 1月1日的压缩备份
```

---

## AsyncHandler 异步处理器

将日志写入操作放到后台线程执行，避免阻塞主程序。适合高性能场景。

### 基本使用

```python
from logify import get_logger, AsyncHandler, FileHandler

logger = get_logger("myapp")

# 创建底层处理器
file_handler = FileHandler("app.log")

# 用 AsyncHandler 包装
async_handler = AsyncHandler(file_handler, queue_size=10000)
logger.add_handler(async_handler)

# 日志会异步写入文件
logger.info("异步写入")

# 程序结束前刷新缓冲区
async_handler.flush()
async_handler.close()
```

### 配置选项

```python
from logify import AsyncHandler, ConsoleHandler, LogLevel

# 包装任意处理器
console = ConsoleHandler()
async_console = AsyncHandler(
    handler=console,
    queue_size=10000,  # 队列最大容量
    level=LogLevel.DEBUG
)

# 检查队列状态
current_size = async_handler.queue_size
```

### 注意事项

```python
import atexit
from logify import get_logger, AsyncHandler, FileHandler

logger = get_logger("myapp")

async_handler = AsyncHandler(FileHandler("app.log"))
logger.add_handler(async_handler)

# 确保程序退出时刷新日志
def cleanup():
    async_handler.flush()
    async_handler.close()

atexit.register(cleanup)
```

---

## NetworkHandler 网络处理器

将日志发送到远程服务器，支持 TCP、UDP 和 HTTP 协议。

### TCPHandler

```python
from logify import get_logger, TCPHandler, JsonFormatter

logger = get_logger("myapp")

# 发送到日志服务器
handler = TCPHandler(
    host="logserver.example.com",
    port=9000
)
handler.formatter = JsonFormatter()
logger.add_handler(handler)
```

### UDPHandler

```python
from logify import get_logger, UDPHandler

logger = get_logger("myapp")

# UDP 协议（无连接，更快但可能丢失）
handler = UDPHandler(
    host="logserver.example.com",
    port=9001
)
logger.add_handler(handler)
```

### HTTPHandler

```python
from logify import get_logger, HTTPHandler, JsonFormatter

logger = get_logger("myapp")

# 发送到 HTTP 端点
handler = HTTPHandler(
    url="https://logs.example.com/api/logs",
    method="POST"
)
handler.formatter = JsonFormatter()
logger.add_handler(handler)
```

---

## 多处理器配合使用

实际应用中，通常需要将日志同时发送到多个目标：

```python
from logify import (
    get_logger,
    ConsoleHandler, FileHandler, RotatingFileHandler,
    ColorFormatter, TextFormatter, JsonFormatter,
    LogLevel
)

logger = get_logger("myapp")
logger.level = LogLevel.DEBUG

# 1. 控制台处理器 - 开发时查看
console = ConsoleHandler(level=LogLevel.DEBUG)
console.formatter = ColorFormatter(
    fmt="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
logger.add_handler(console)

# 2. 应用日志文件 - 记录所有日志
app_log = RotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=5
)
app_log.formatter = TextFormatter(
    fmt="%(asctime)s [%(thread)d] %(name)s %(levelname)s - %(message)s"
)
app_log.level = LogLevel.DEBUG
logger.add_handler(app_log)

# 3. 错误日志文件 - 只记录错误
error_log = FileHandler("logs/error.log")
error_log.formatter = TextFormatter(
    fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s"
)
error_log.level = LogLevel.ERROR
logger.add_handler(error_log)

# 4. JSON 日志 - 用于日志分析系统
json_log = RotatingFileHandler(
    filename="logs/app.json",
    max_bytes=50 * 1024 * 1024,
    backup_count=10
)
json_log.formatter = JsonFormatter(
    extra_fields={"service": "myapp", "env": "production"}
)
logger.add_handler(json_log)

# 使用 logger
logger.debug("这只会出现在控制台和 app.log")
logger.info("应用启动")
logger.error("发生错误")  # 这会出现在所有日志文件
```

---

## 自定义处理器

继承 `BaseHandler` 创建自定义处理器：

### 基本结构

```python
from logify import BaseHandler, LogRecord, LogLevel

class MyHandler(BaseHandler):
    """自定义处理器"""
    
    def __init__(self, level=LogLevel.DEBUG, formatter=None):
        super().__init__(level=level, formatter=formatter)
        # 初始化你的资源
    
    def emit(self, record: LogRecord) -> None:
        """输出日志记录
        
        Args:
            record: 日志记录
        """
        try:
            # 格式化消息
            msg = self.format(record)
            
            # 你的输出逻辑
            self._do_output(msg)
            
        except Exception:
            self.handle_error(record)
    
    def _do_output(self, msg: str) -> None:
        """实际的输出操作"""
        pass
    
    def flush(self) -> None:
        """刷新缓冲区"""
        pass
    
    def close(self) -> None:
        """关闭并清理资源"""
        super().close()
```

### 示例：数据库处理器

```python
import sqlite3
from logify import BaseHandler, LogRecord, LogLevel

class SQLiteHandler(BaseHandler):
    """SQLite 数据库日志处理器"""
    
    def __init__(
        self,
        database: str,
        table: str = "logs",
        level=LogLevel.DEBUG
    ):
        super().__init__(level=level)
        self.database = database
        self.table = table
        self._conn = None
        self._setup_database()
    
    def _setup_database(self):
        """创建数据库表"""
        self._conn = sqlite3.connect(self.database)
        self._conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                level TEXT,
                logger TEXT,
                message TEXT,
                filename TEXT,
                lineno INTEGER
            )
        ''')
        self._conn.commit()
    
    def emit(self, record: LogRecord) -> None:
        try:
            self._conn.execute(
                f'''INSERT INTO {self.table}
                    (timestamp, level, logger, message, filename, lineno)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    record.timestamp,
                    record.level_name,
                    record.name,
                    record.message,
                    record.filename,
                    record.lineno
                )
            )
            self._conn.commit()
        except Exception:
            self.handle_error(record)
    
    def close(self):
        if self._conn:
            self._conn.close()
        super().close()
```

### 示例：邮件告警处理器

```python
import smtplib
from email.mime.text import MIMEText
from logify import BaseHandler, LogRecord, LogLevel

class EmailHandler(BaseHandler):
    """邮件告警处理器（仅处理严重错误）"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_addr: str,
        to_addrs: list,
        subject: str = "Application Error Alert",
        username: str = None,
        password: str = None
    ):
        super().__init__(level=LogLevel.CRITICAL)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.subject = subject
        self.username = username
        self.password = password
    
    def emit(self, record: LogRecord) -> None:
        try:
            msg = MIMEText(self.format(record))
            msg['Subject'] = f"{self.subject}: {record.message[:50]}"
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.username:
                    server.login(self.username, self.password)
                server.sendmail(
                    self.from_addr,
                    self.to_addrs,
                    msg.as_string()
                )
        except Exception:
            self.handle_error(record)
```

---

## 处理器的生命周期

```python
from logify import get_logger, FileHandler

logger = get_logger("myapp")
handler = FileHandler("app.log")
logger.add_handler(handler)

# 使用日志
for i in range(1000):
    logger.info(f"处理项目 {i}")

# 刷新缓冲区（确保所有日志写入）
handler.flush()

# 或者刷新 logger 的所有处理器
logger.flush()

# 关闭处理器（释放资源）
handler.close()

# 或者关闭 logger 的所有处理器
logger.close()
```

---

## 小结

在本教程中，你学会了：

1. ✅ 使用 `ConsoleHandler` 输出到控制台
2. ✅ 使用 `FileHandler` 写入日志文件
3. ✅ 使用 `RotatingFileHandler` 按大小轮转
4. ✅ 使用 `TimedRotatingFileHandler` 按时间轮转
5. ✅ 使用 `AsyncHandler` 异步处理日志
6. ✅ 使用网络处理器发送日志
7. ✅ 配置多个处理器协同工作
8. ✅ 创建自定义处理器

### 下一步

- 📖 [教程 04：过滤器与上下文](04_filters_context.md) - 学习过滤和上下文管理
- 📖 [教程 05：配置管理](05_configuration.md) - 从文件加载配置

---

[← 上一篇：日志格式化器](02_formatters.md) | [返回目录](README.md) | [下一篇：过滤器与上下文 →](04_filters_context.md)
