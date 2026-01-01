# Logify API Documentation

Logify 是一个功能完善、易于扩展的 Python 日志处理模块。

**版本**: 0.1.0

---

## 目录

- [快速开始](#快速开始)
- [核心组件 (Core)](#核心组件-core)
  - [LogLevel](#loglevel)
  - [LogRecord](#logrecord)
  - [LoggerManager](#loggermanager)
- [Logger API](#logger-api)
  - [Logger](#logger)
- [过滤器 (Filters)](#过滤器-filters)
  - [BaseFilter](#basefilter)
  - [FilterChain](#filterchain)
  - [LevelFilter](#levelfilter)
  - [RegexFilter](#regexfilter)
  - [ContextFilter](#contextfilter)
- [格式化器 (Formatters)](#格式化器-formatters)
  - [BaseFormatter](#baseformatter)
  - [TextFormatter](#textformatter)
  - [JsonFormatter](#jsonformatter)
  - [ColorFormatter](#colorformatter)
- [处理器 (Handlers)](#处理器-handlers)
  - [BaseHandler](#basehandler)
  - [HandlerChain](#handlerchain)
  - [ConsoleHandler](#consolehandler)
  - [FileHandler](#filehandler)
  - [RotatingFileHandler](#rotatingfilehandler)
  - [TimedRotatingFileHandler](#timedrotatingfilehandler)
  - [AsyncHandler](#asynchandler)
  - [NetworkHandler](#networkhandler)
  - [TCPHandler](#tcphandler)
  - [UDPHandler](#udphandler)
  - [HTTPHandler](#httphandler)
- [配置 (Config)](#配置-config)
  - [ConfigLoader](#configloader)
  - [ConfigParser](#configparser)
- [便捷函数](#便捷函数)
- [完整示例](#完整示例)

---

## 快速开始

### 基本用法

```python
from logify import get_logger, DEBUG, INFO

# 获取 logger
logger = get_logger("myapp")

# 记录日志
logger.info("Application started")
logger.debug("Debug message")
logger.error("Error occurred", exc_info=True)
```

### 高级用法

```python
from logify import (
    get_logger, 
    ConsoleHandler, 
    FileHandler, 
    JsonFormatter,
    LevelFilter,
    LogLevel
)

# 创建 logger
logger = get_logger("myapp")
logger.level = LogLevel.DEBUG

# 添加控制台处理器
console_handler = ConsoleHandler()
logger.add_handler(console_handler)

# 添加文件处理器
file_handler = FileHandler("app.log")
file_handler.formatter = JsonFormatter()
logger.add_handler(file_handler)

# 使用上下文
with logger.context(request_id="123"):
    logger.info("Processing request")

# 使用装饰器
@logger.trace
def my_function():
    pass
```

---

## 核心组件 (Core)

### LogLevel

日志级别枚举类，定义日志的严重程度。

```python
from logify import LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL
```

#### 级别值

| 级别 | 数值 | 说明 |
|------|------|------|
| `DEBUG` | 10 | 调试信息 |
| `INFO` | 20 | 一般信息 |
| `WARNING` | 30 | 警告信息 |
| `ERROR` | 40 | 错误信息 |
| `CRITICAL` | 50 | 严重错误 |

#### 类方法

##### `get_name(level: int) -> str`
根据级别值获取级别名称。

```python
LogLevel.get_name(20)  # 返回 "INFO"
```

##### `get_level(name: str) -> Optional[LogLevel]`
根据名称获取日志级别（不区分大小写）。

```python
LogLevel.get_level("info")  # 返回 LogLevel.INFO
```

##### `get_all_levels() -> Dict[str, int]`
获取所有日志级别映射字典。

```python
LogLevel.get_all_levels()  # {'DEBUG': 10, 'INFO': 20, ...}
```

---

### LogRecord

日志记录数据类，封装单条日志的所有信息。

```python
from logify import LogRecord
```

#### 构造函数

```python
LogRecord(
    name: str,                          # Logger 名称
    level: LogLevel,                    # 日志级别
    msg: str,                           # 原始日志消息
    args: tuple = (),                   # 消息格式化参数
    kwargs: Dict[str, Any] = {},        # 附加键值对数据
    timestamp: float = time.time(),     # 时间戳
    filename: str = "",                 # 源文件名
    lineno: int = 0,                    # 源代码行号
    func_name: str = "",                # 函数名
    thread_id: int = ...,               # 线程 ID
    thread_name: str = ...,             # 线程名称
    process_id: int = ...,              # 进程 ID
    exception_info: Optional[tuple] = None,  # 异常信息
    extra: Dict[str, Any] = {}          # 额外上下文数据
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `level_name` | `str` | 日志级别名称 |
| `datetime` | `datetime` | 日志时间的 datetime 对象 |
| `formatted_time` | `str` | 格式化的时间字符串 |
| `message` | `str` | 格式化后的消息（使用 `%` 格式化 args） |

#### 方法

##### `to_dict() -> Dict[str, Any]`
将日志记录转换为字典格式。

---

### LoggerManager

Logger 管理器，采用单例模式全局管理所有 Logger 实例。

```python
from logify import LoggerManager, get_logger
```

#### 方法

##### `get_logger(name: str = "root") -> Logger`
获取或创建 Logger 实例。

```python
manager = LoggerManager()
logger = manager.get_logger("myapp")
```

##### `get_all_loggers() -> Dict[str, Logger]`
获取所有已创建的 Logger。

##### `clear() -> None`
清除所有 Logger 缓存。

##### `reset() -> None` (类方法)
重置单例实例（主要用于测试）。

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `root` | `Logger` | 根 Logger |

---

## Logger API

### Logger

日志记录器，提供日志记录的主要接口。

```python
from logify import get_logger, Logger
```

#### 构造函数

```python
Logger(
    name: str = "root",                           # Logger 名称
    level: Union[LogLevel, int] = LogLevel.DEBUG, # 最低日志级别
    manager: Optional[LoggerManager] = None       # Logger 管理器
)
```

#### 属性

| 属性 | 类型 | 可写 | 说明 |
|------|------|------|------|
| `name` | `str` | 否 | Logger 名称 |
| `level` | `int` | 是 | 日志级别 |
| `parent` | `Optional[Logger]` | 是 | 父 Logger |
| `propagate` | `bool` | 是 | 是否向父 Logger 传播日志 |
| `disabled` | `bool` | 是 | 是否禁用 |
| `handlers` | `List[BaseHandler]` | 否 | 所有处理器列表 |

#### 日志记录方法

##### `debug(msg: str, *args, **kwargs) -> None`
记录 DEBUG 级别日志。

##### `info(msg: str, *args, **kwargs) -> None`
记录 INFO 级别日志。

##### `warning(msg: str, *args, **kwargs) -> None`
记录 WARNING 级别日志。

##### `warn(msg: str, *args, **kwargs) -> None`
`warning` 的别名。

##### `error(msg: str, *args, **kwargs) -> None`
记录 ERROR 级别日志。

##### `critical(msg: str, *args, **kwargs) -> None`
记录 CRITICAL 级别日志。

##### `fatal(msg: str, *args, **kwargs) -> None`
`critical` 的别名。

##### `exception(msg: str, *args, **kwargs) -> None`
记录带异常信息的 ERROR 级别日志（应在 except 块中调用）。

##### `log(level: Union[LogLevel, int], msg: str, *args, **kwargs) -> None`
记录指定级别的日志。

**特殊参数**：
- `exc_info: bool` - 是否包含异常信息
- `extra: Dict` - 额外的上下文数据

```python
logger.info("User %s logged in", username)
logger.error("Failed to connect", exc_info=True)
logger.info("Request processed", extra={"request_id": "123"})
```

#### 处理器管理

##### `add_handler(handler: BaseHandler) -> Logger`
添加处理器，支持链式调用。

##### `remove_handler(handler: BaseHandler) -> Logger`
移除处理器，支持链式调用。

#### 过滤器管理

##### `add_filter(filter_: BaseFilter) -> Logger`
添加过滤器，支持链式调用。

##### `remove_filter(filter_: BaseFilter) -> Logger`
移除过滤器，支持链式调用。

#### 上下文管理

##### `set_extra(**kwargs) -> Logger`
设置额外的上下文数据（添加到每条日志记录中）。

##### `clear_extra() -> Logger`
清除额外的上下文数据。

##### `context(**kwargs)` (上下文管理器)
临时添加额外数据。

```python
with logger.context(request_id="123", user="admin"):
    logger.info("Processing request")  # 日志包含 request_id 和 user
# 离开上下文后，额外数据自动移除
```

#### 装饰器

##### `trace(func=None, *, level=LogLevel.DEBUG)`
函数调用追踪装饰器，记录函数的进入和退出。

```python
@logger.trace
def my_function():
    pass

@logger.trace(level=LogLevel.INFO)
def another_function():
    pass
```

#### 其他方法

##### `is_enabled_for(level: Union[LogLevel, int]) -> bool`
检查是否启用指定级别。

##### `get_child(suffix: str) -> Logger`
获取子 Logger。

```python
child = logger.get_child("module")  # 创建 "myapp.module" logger
```

##### `flush() -> None`
刷新所有处理器。

##### `close() -> None`
关闭所有处理器。

---

## 过滤器 (Filters)

### BaseFilter

过滤器抽象基类。

```python
from logify import BaseFilter
```

#### 构造函数

```python
BaseFilter(name: str = "")
```

#### 抽象方法

##### `filter(record: LogRecord) -> bool`
过滤日志记录。返回 `True` 表示通过，`False` 表示拒绝。

#### 自定义过滤器示例

```python
class MyFilter(BaseFilter):
    def filter(self, record):
        return "secret" not in record.message.lower()
```

---

### FilterChain

过滤器责任链，按顺序执行多个过滤器。

```python
from logify import FilterChain
```

#### 方法

##### `add_filter(filter_: BaseFilter) -> FilterChain`
添加过滤器到链中。

##### `remove_filter(filter_: BaseFilter) -> FilterChain`
从链中移除过滤器。

##### `filter(record: LogRecord) -> bool`
执行过滤器链，所有过滤器都通过才返回 `True`。

##### `clear() -> None`
清空过滤器链。

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `filters` | `List[BaseFilter]` | 所有过滤器列表 |

---

### LevelFilter

级别过滤器，只允许指定级别或更高级别的日志通过。

```python
from logify import LevelFilter
```

#### 构造函数

```python
LevelFilter(
    level: Union[LogLevel, int, str] = LogLevel.DEBUG,  # 最低日志级别
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 可写 | 说明 |
|------|------|------|------|
| `level` | `int` | 是 | 当前过滤级别 |

#### 示例

```python
filter = LevelFilter(level="WARNING")  # 只允许 WARNING 及以上
handler.add_filter(filter)
```

---

### RegexFilter

正则表达式过滤器，根据正则表达式匹配日志消息。

```python
from logify import RegexFilter
```

#### 构造函数

```python
RegexFilter(
    pattern: Union[str, Pattern],  # 正则表达式模式
    match_pass: bool = True,       # True=匹配时通过，False=匹配时拒绝
    flags: int = 0,                # 正则表达式标志（如 re.IGNORECASE）
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `pattern` | `Pattern` | 正则表达式模式 |
| `match_pass` | `bool` | 匹配行为 |

#### 示例

```python
import re

# 只允许包含 "important" 的消息
filter1 = RegexFilter(r"important", match_pass=True, flags=re.IGNORECASE)

# 过滤掉包含密码的消息
filter2 = RegexFilter(r"password", match_pass=False)
```

---

### ContextFilter

上下文过滤器，根据日志记录的上下文属性进行过滤。

```python
from logify import ContextFilter
```

#### 构造函数

```python
ContextFilter(
    allowed_names: Optional[Set[str]] = None,      # 允许的 Logger 名称集合
    denied_names: Optional[Set[str]] = None,       # 拒绝的 Logger 名称集合
    allowed_threads: Optional[Set[Union[int, str]]] = None,  # 允许的线程
    allowed_processes: Optional[Set[int]] = None,  # 允许的进程 ID
    custom_check: Optional[Callable[[LogRecord], bool]] = None,  # 自定义检查函数
    name: str = ""
)
```

#### 方法

##### `allow_name(name: str) -> ContextFilter`
添加允许的 Logger 名称。

##### `deny_name(name: str) -> ContextFilter`
添加拒绝的 Logger 名称。

#### 示例

```python
# 只允许特定模块的日志
filter = ContextFilter(allowed_names={"myapp.api", "myapp.db"})

# 使用自定义检查函数
def check_extra(record):
    return record.extra.get("user_id") is not None

filter = ContextFilter(custom_check=check_extra)
```

---

## 格式化器 (Formatters)

### BaseFormatter

格式化器抽象基类。

```python
from logify import BaseFormatter
```

#### 抽象方法

##### `format(record: LogRecord) -> str`
格式化日志记录，返回格式化后的字符串。

#### 方法

##### `format_exception(record: LogRecord) -> str`
格式化异常信息。

---

### TextFormatter

文本格式化器，支持类似 Python logging 的格式化字符串语法。

```python
from logify import TextFormatter
```

#### 构造函数

```python
TextFormatter(
    fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    name: str = ""
)
```

#### 可用占位符

| 占位符 | 说明 |
|--------|------|
| `%(asctime)s` | 时间戳 |
| `%(name)s` | Logger 名称 |
| `%(levelname)s` | 日志级别名称 |
| `%(levelno)d` | 日志级别数值 |
| `%(message)s` | 日志消息 |
| `%(filename)s` | 源文件名 |
| `%(lineno)d` | 行号 |
| `%(funcName)s` | 函数名 |
| `%(thread)d` | 线程 ID |
| `%(threadName)s` | 线程名称 |
| `%(process)d` | 进程 ID |

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `format_string` | `str` | 格式化模板 |
| `date_format` | `str` | 日期格式 |

#### 示例

```python
formatter = TextFormatter(
    fmt="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
```

---

### JsonFormatter

JSON 格式化器，将日志输出为 JSON 格式。

```python
from logify import JsonFormatter
```

#### 构造函数

```python
JsonFormatter(
    fields: Optional[List[str]] = None,      # 要包含的字段列表
    indent: Optional[int] = None,            # JSON 缩进空格数
    ensure_ascii: bool = False,              # 是否确保 ASCII 编码
    timestamp_format: str = "iso",           # 时间戳格式 ("iso" 或 "epoch")
    extra_fields: Optional[Dict[str, Any]] = None,  # 额外固定字段
    json_encoder: Optional[Callable] = None, # 自定义 JSON 编码器
    name: str = ""
)
```

#### 示例

```python
# 基本用法
formatter = JsonFormatter()

# 只输出特定字段
formatter = JsonFormatter(
    fields=["timestamp", "level", "message", "logger"],
    indent=2
)

# 添加固定字段
formatter = JsonFormatter(
    extra_fields={"app": "myapp", "env": "production"}
)
```

#### 输出示例

```json
{
  "timestamp": "2025-01-01T12:00:00",
  "level": "INFO",
  "logger": "myapp",
  "message": "Application started",
  "filename": "main.py",
  "lineno": 10
}
```

---

### ColorFormatter

颜色格式化器，为控制台输出添加 ANSI 颜色支持。

```python
from logify import ColorFormatter, Colors
```

#### 构造函数

```python
ColorFormatter(
    fmt: Optional[str] = None,                # 格式化模板
    datefmt: Optional[str] = None,            # 日期格式
    level_colors: Optional[Dict[int, str]] = None,  # 级别颜色映射
    colorize_message: bool = True,            # 是否为消息添加颜色
    colorize_level: bool = True,              # 是否为级别名称添加颜色
    force_colors: bool = False,               # 是否强制使用颜色
    name: str = ""
)
```

#### Colors 常量

| 常量 | 说明 |
|------|------|
| `Colors.BLACK` | 黑色 |
| `Colors.RED` | 红色 |
| `Colors.GREEN` | 绿色 |
| `Colors.YELLOW` | 黄色 |
| `Colors.BLUE` | 蓝色 |
| `Colors.MAGENTA` | 洋红 |
| `Colors.CYAN` | 青色 |
| `Colors.WHITE` | 白色 |
| `Colors.BRIGHT_*` | 亮色版本 |
| `Colors.BOLD` | 粗体 |
| `Colors.RESET` | 重置 |

#### 默认级别颜色

| 级别 | 颜色 |
|------|------|
| DEBUG | 青色 |
| INFO | 绿色 |
| WARNING | 黄色 |
| ERROR | 红色 |
| CRITICAL | 亮红色 + 粗体 |

#### 方法

##### `set_level_color(level: int, color: str) -> None`
设置日志级别的颜色。

```python
formatter = ColorFormatter()
formatter.set_level_color(LogLevel.DEBUG, Colors.BLUE)
```

---

## 处理器 (Handlers)

### BaseHandler

处理器抽象基类。

```python
from logify import BaseHandler
```

#### 构造函数

```python
BaseHandler(
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 可写 | 说明 |
|------|------|------|------|
| `level` | `int` | 是 | 处理器级别 |
| `formatter` | `BaseFormatter` | 是 | 格式化器 |
| `name` | `str` | 否 | 处理器名称 |

#### 方法

##### `add_filter(filter_: BaseFilter) -> BaseHandler`
添加过滤器。

##### `remove_filter(filter_: BaseFilter) -> BaseHandler`
移除过滤器。

##### `handle(record: LogRecord) -> bool`
处理日志记录（执行级别检查、过滤和输出）。

##### `emit(record: LogRecord) -> None` (抽象方法)
输出日志记录，子类必须实现。

##### `flush() -> None`
刷新缓冲区。

##### `close() -> None`
关闭处理器。

---

### HandlerChain

处理器责任链，将日志分发到多个处理器。

```python
from logify import HandlerChain
```

#### 方法

##### `add_handler(handler: BaseHandler) -> HandlerChain`
添加处理器。

##### `remove_handler(handler: BaseHandler) -> HandlerChain`
移除处理器。

##### `handle(record: LogRecord) -> int`
分发日志到所有处理器，返回成功处理的数量。

##### `flush() -> None`
刷新所有处理器。

##### `close() -> None`
关闭所有处理器。

##### `clear() -> None`
清空处理器链。

---

### ConsoleHandler

控制台处理器，输出日志到标准输出/错误流。

```python
from logify import ConsoleHandler
```

#### 构造函数

```python
ConsoleHandler(
    stream: Optional[TextIO] = None,         # 输出流，默认 sys.stdout
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,  # 默认 ColorFormatter
    use_stderr_for_errors: bool = True,      # ERROR 及以上输出到 stderr
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 可写 | 说明 |
|------|------|------|------|
| `stream` | `TextIO` | 是 | 输出流 |

---

### FileHandler

文件处理器，输出日志到文件。

```python
from logify import FileHandler
```

#### 构造函数

```python
FileHandler(
    filename: Union[str, Path],              # 日志文件路径
    mode: str = 'a',                         # 'a' 追加，'w' 覆盖
    encoding: str = 'utf-8',
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    delay: bool = False,                     # 是否延迟打开文件
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `filename` | `Path` | 文件路径 |
| `base_filename` | `str` | 基础文件名 |

---

### RotatingFileHandler

按大小轮转的文件处理器。

```python
from logify import RotatingFileHandler
```

#### 构造函数

```python
RotatingFileHandler(
    filename: Union[str, Path],
    max_bytes: int = 10 * 1024 * 1024,       # 单文件最大字节数 (10MB)
    backup_count: int = 5,                   # 保留的备份文件数量
    encoding: str = 'utf-8',
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    compress: bool = False,                  # 是否压缩备份文件
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `max_bytes` | `int` | 最大字节数 |
| `backup_count` | `int` | 备份数量 |

#### 方法

##### `should_rollover(record: LogRecord) -> bool`
检查是否需要轮转。

##### `do_rollover() -> None`
执行轮转。

#### 示例

```python
handler = RotatingFileHandler(
    filename="app.log",
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=3,
    compress=True
)
# 生成文件: app.log, app.log.1.gz, app.log.2.gz, app.log.3.gz
```

---

### TimedRotatingFileHandler

按时间轮转的文件处理器。

```python
from logify import TimedRotatingFileHandler
```

#### 构造函数

```python
TimedRotatingFileHandler(
    filename: Union[str, Path],
    when: str = 'D',                         # 时间间隔类型
    interval: int = 1,                       # 时间间隔数量
    backup_count: int = 7,                   # 保留的备份数量
    encoding: str = 'utf-8',
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    compress: bool = False,
    name: str = ""
)
```

#### when 参数值

| 值 | 说明 |
|----|------|
| `'S'` | 秒 |
| `'M'` | 分钟 |
| `'H'` | 小时 |
| `'D'` | 天 |
| `'MIDNIGHT'` | 午夜 |

#### 示例

```python
# 每天午夜轮转，保留 30 天
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="MIDNIGHT",
    backup_count=30
)

# 每小时轮转
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="H",
    interval=1
)
```

---

### AsyncHandler

异步处理器包装器，实现非阻塞日志写入。

```python
from logify import AsyncHandler
```

#### 构造函数

```python
AsyncHandler(
    handler: BaseHandler,                    # 被包装的处理器
    queue_size: int = 10000,                 # 队列最大容量
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `handler` | `BaseHandler` | 被包装的处理器 |
| `queue_size` | `int` | 当前队列大小 |

#### 示例

```python
file_handler = FileHandler("app.log")
async_handler = AsyncHandler(file_handler, queue_size=5000)
logger.add_handler(async_handler)
```

---

### NetworkHandler

网络处理器基类。

```python
from logify import NetworkHandler
```

#### 构造函数

```python
NetworkHandler(
    host: str,                               # 目标主机
    port: int,                               # 目标端口
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,  # 默认 JsonFormatter
    timeout: float = 5.0,                    # 连接超时
    name: str = ""
)
```

---

### TCPHandler

TCP 网络处理器。

```python
from logify import TCPHandler
```

#### 构造函数

```python
TCPHandler(
    host: str,
    port: int,
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    timeout: float = 5.0,
    name: str = ""
)
```

---

### UDPHandler

UDP 网络处理器。

```python
from logify import UDPHandler
```

#### 构造函数

```python
UDPHandler(
    host: str,
    port: int,
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    name: str = ""
)
```

---

### HTTPHandler

HTTP 网络处理器，通过 HTTP POST 发送日志。

```python
from logify import HTTPHandler
```

#### 构造函数

```python
HTTPHandler(
    url: str,                                # 目标 URL
    method: str = 'POST',                    # HTTP 方法
    headers: Optional[Dict[str, str]] = None,
    level: Union[LogLevel, int] = LogLevel.DEBUG,
    formatter: Optional[BaseFormatter] = None,
    timeout: float = 5.0,
    batch_size: int = 1,                     # 批量发送大小
    auth: Optional[tuple] = None,            # 认证信息 (username, password)
    name: str = ""
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 目标 URL |

#### 示例

```python
handler = HTTPHandler(
    url="https://logs.example.com/api/logs",
    headers={"X-API-Key": "your-api-key"},
    auth=("user", "password")
)
```

---

## 配置 (Config)

### ConfigLoader

配置加载器，支持从多种来源加载配置。

```python
from logify import ConfigLoader
```

#### 方法

##### `load_from_dict(config: Dict[str, Any]) -> ConfigLoader`
从字典加载配置。

##### `load_from_file(filepath: Union[str, Path]) -> ConfigLoader`
从文件加载配置（支持 JSON、YAML、TOML）。

##### `load_from_env(prefix: str = "LOGIFY_", mapping: Optional[Dict] = None) -> ConfigLoader`
从环境变量加载配置。

##### `get(key: str, default: Any = None) -> Any`
获取配置值（支持点号分隔的嵌套键）。

##### `clear() -> ConfigLoader`
清除所有配置。

##### `merge(other: ConfigLoader) -> ConfigLoader`
合并另一个配置加载器的配置。

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | `Dict[str, Any]` | 当前配置字典 |

#### 示例

```python
loader = ConfigLoader()
loader.load_from_file("config.yaml")
loader.load_from_env("MYAPP_LOG_")

level = loader.get("handlers.console.level", "INFO")
```

---

### ConfigParser

配置解析器，解析配置并初始化日志组件。

```python
from logify import ConfigParser
```

#### 配置格式

```json
{
    "version": 1,
    "formatters": {
        "simple": {
            "class": "TextFormatter",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "JsonFormatter"
        }
    },
    "filters": {
        "level_filter": {
            "class": "LevelFilter",
            "level": "INFO"
        }
    },
    "handlers": {
        "console": {
            "class": "ConsoleHandler",
            "level": "DEBUG",
            "formatter": "simple"
        },
        "file": {
            "class": "FileHandler",
            "filename": "app.log",
            "level": "INFO",
            "formatter": "simple",
            "filters": ["level_filter"]
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        },
        "app": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": false
        }
    }
}
```

#### 方法

##### `parse() -> None`
解析配置并创建所有组件。

##### `from_file(filepath: str) -> ConfigParser` (类方法)
从文件创建配置解析器。

##### `get_formatter(name: str) -> Optional[BaseFormatter]`
获取已创建的格式化器。

##### `get_handler(name: str) -> Optional[BaseHandler]`
获取已创建的处理器。

##### `get_filter(name: str) -> Optional[BaseFilter]`
获取已创建的过滤器。

##### `register_formatter(name: str, formatter_class: Type) -> None` (类方法)
注册自定义格式化器类。

##### `register_handler(name: str, handler_class: Type) -> None` (类方法)
注册自定义处理器类。

##### `register_filter(name: str, filter_class: Type) -> None` (类方法)
注册自定义过滤器类。

#### 示例

```python
# 从文件配置
parser = ConfigParser.from_file("logging.json")

# 从字典配置
config = {
    "formatters": {...},
    "handlers": {...},
    "loggers": {...}
}
parser = ConfigParser(config)
parser.parse()
```

---

## 便捷函数

Logify 提供了模块级的便捷函数，直接操作根 Logger：

```python
from logify import (
    basic_config,
    configure_from_file,
    configure_from_dict,
    get_logger,
    debug, info, warning, error, critical, exception
)
```

### basic_config

快速配置根日志记录器。

```python
basic_config(
    level: int = INFO,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    filename: str = None,
    handlers: list = None,
    force: bool = False
)
```

### configure_from_file

从配置文件配置日志系统。

```python
configure_from_file(filepath: str) -> ConfigParser
```

### configure_from_dict

从字典配置日志系统。

```python
configure_from_dict(config: dict) -> ConfigParser
```

### 模块级日志方法

```python
debug(msg, *args, **kwargs)
info(msg, *args, **kwargs)
warning(msg, *args, **kwargs)
error(msg, *args, **kwargs)
critical(msg, *args, **kwargs)
exception(msg, *args, **kwargs)
```

---

## 完整示例

### 基础示例

```python
from logify import get_logger, basic_config, WARNING

# 快速配置
basic_config(level=WARNING, filename="app.log")

# 记录日志
logger = get_logger("myapp")
logger.warning("This is a warning")
logger.error("This is an error")
```

### 多处理器配置

```python
from logify import (
    get_logger,
    ConsoleHandler, FileHandler, RotatingFileHandler,
    TextFormatter, JsonFormatter, ColorFormatter,
    LevelFilter, LogLevel
)

# 创建 logger
logger = get_logger("myapp")
logger.level = LogLevel.DEBUG

# 控制台处理器（带颜色）
console_handler = ConsoleHandler()
console_handler.formatter = ColorFormatter(
    fmt="[%(asctime)s] %(levelname)s - %(message)s"
)
console_handler.level = LogLevel.DEBUG
logger.add_handler(console_handler)

# 文件处理器（JSON 格式，只记录 WARNING 以上）
file_handler = RotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=5
)
file_handler.formatter = JsonFormatter()
file_handler.add_filter(LevelFilter(LogLevel.WARNING))
logger.add_handler(file_handler)

# 使用
logger.debug("Debug message")  # 只输出到控制台
logger.warning("Warning message")  # 输出到控制台和文件
```

### 使用上下文和装饰器

```python
from logify import get_logger

logger = get_logger("myapp")

# 上下文管理器
def process_request(request_id, user):
    with logger.context(request_id=request_id, user=user):
        logger.info("Processing request")
        do_something()
        logger.info("Request completed")

# 函数追踪装饰器
@logger.trace
def calculate(x, y):
    return x + y

# 带日志级别的追踪
@logger.trace(level=LogLevel.INFO)
def important_operation():
    pass
```

### 从配置文件加载

```yaml
# logging.yaml
version: 1
formatters:
  simple:
    class: TextFormatter
    format: "%(asctime)s - %(levelname)s - %(message)s"
  json:
    class: JsonFormatter
    indent: 2

handlers:
  console:
    class: ConsoleHandler
    formatter: simple
    level: DEBUG
  file:
    class: RotatingFileHandler
    filename: logs/app.log
    max_bytes: 10485760
    backup_count: 5
    formatter: json
    level: INFO

loggers:
  root:
    level: DEBUG
    handlers:
      - console
      - file
```

```python
from logify import configure_from_file, get_logger

# 加载配置
configure_from_file("logging.yaml")

# 使用
logger = get_logger("myapp")
logger.info("Application started")
```

### 异步日志

```python
from logify import get_logger, AsyncHandler, FileHandler

logger = get_logger("myapp")

# 创建异步文件处理器
file_handler = FileHandler("app.log")
async_handler = AsyncHandler(file_handler, queue_size=10000)
logger.add_handler(async_handler)

# 日志写入不会阻塞主线程
for i in range(10000):
    logger.info(f"Message {i}")

# 程序退出时会自动刷新队列
```

### 网络日志

```python
from logify import get_logger, HTTPHandler, JsonFormatter

logger = get_logger("myapp")

# 发送日志到远程服务器
http_handler = HTTPHandler(
    url="https://logs.example.com/api/logs",
    headers={"Authorization": "Bearer your-token"},
    timeout=3.0
)
http_handler.formatter = JsonFormatter(
    extra_fields={"app": "myapp", "env": "production"}
)
logger.add_handler(http_handler)

logger.error("Critical error occurred", exc_info=True)
```

---

## 导出列表

```python
from logify import (
    # Version
    __version__,
    
    # Core
    LogLevel, DEBUG, INFO, WARNING, ERROR, CRITICAL,
    LogRecord,
    LoggerManager, get_logger,
    
    # Filters
    BaseFilter, FilterChain,
    LevelFilter, RegexFilter, ContextFilter,
    
    # Formatters
    BaseFormatter,
    TextFormatter, JsonFormatter, ColorFormatter, Colors,
    
    # Handlers
    BaseHandler, HandlerChain,
    ConsoleHandler, FileHandler,
    RotatingFileHandler, TimedRotatingFileHandler,
    AsyncHandler,
    NetworkHandler, TCPHandler, UDPHandler, HTTPHandler,
    
    # Config
    ConfigLoader, ConfigParser,
    
    # API
    Logger,
    
    # Functions
    basic_config,
    configure_from_file,
    configure_from_dict,
    debug, info, warning, error, critical, exception,
)
```
