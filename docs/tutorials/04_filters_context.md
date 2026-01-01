# Logify 教程 04：过滤器与上下文

> 难度：中级 | 预计阅读时间：15 分钟

## 目录

- [过滤器简介](#过滤器简介)
- [LevelFilter 级别过滤器](#levelfilter-级别过滤器)
- [RegexFilter 正则过滤器](#regexfilter-正则过滤器)
- [ContextFilter 上下文过滤器](#contextfilter-上下文过滤器)
- [FilterChain 过滤器链](#filterchain-过滤器链)
- [上下文管理](#上下文管理)
- [自定义过滤器](#自定义过滤器)
- [函数追踪装饰器](#函数追踪装饰器)
- [小结](#小结)

---

## 过滤器简介

过滤器（Filter）用于决定哪些日志记录应该被处理，哪些应该被丢弃。过滤器可以添加到 Logger 或 Handler 上。

### 过滤流程

```
日志记录 → Logger 级别检查 → Logger 过滤器 → Handler 级别检查 → Handler 过滤器 → 输出
```

每个过滤器返回 `True`（通过）或 `False`（拒绝）。

---

## LevelFilter 级别过滤器

根据日志级别进行过滤，只允许指定级别或更高级别的日志通过。

### 基本使用

```python
from logify import get_logger, ConsoleHandler, LevelFilter, LogLevel

logger = get_logger("myapp")
handler = ConsoleHandler()

# 创建级别过滤器，只允许 WARNING 及以上
level_filter = LevelFilter(level=LogLevel.WARNING)
handler.add_filter(level_filter)

logger.add_handler(handler)

logger.debug("不会显示")
logger.info("不会显示")
logger.warning("会显示")
logger.error("会显示")
```

### 使用字符串指定级别

```python
from logify import LevelFilter

# 可以使用字符串（不区分大小写）
filter1 = LevelFilter(level="WARNING")
filter2 = LevelFilter(level="info")
filter3 = LevelFilter(level="ERROR")
```

### 动态修改级别

```python
from logify import LevelFilter, LogLevel

level_filter = LevelFilter(level=LogLevel.INFO)

# 运行时修改
level_filter.level = LogLevel.DEBUG

# 或使用整数
level_filter.level = 30  # WARNING
```

---

## RegexFilter 正则过滤器

使用正则表达式匹配日志消息内容进行过滤。

### 基本使用

```python
from logify import get_logger, ConsoleHandler, RegexFilter

logger = get_logger("myapp")
handler = ConsoleHandler()

# 只允许包含 "important" 的消息
filter = RegexFilter(pattern=r"important", match_pass=True)
handler.add_filter(filter)

logger.add_handler(handler)

logger.info("普通消息")           # 不会显示
logger.info("这是 important 消息") # 会显示
```

### 过滤模式

```python
import re
from logify import RegexFilter

# match_pass=True: 匹配时通过
filter1 = RegexFilter(r"important", match_pass=True)
# 只显示包含 "important" 的消息

# match_pass=False: 匹配时拒绝
filter2 = RegexFilter(r"password", match_pass=False)
# 过滤掉包含 "password" 的消息

# 使用正则标志
filter3 = RegexFilter(
    pattern=r"error",
    match_pass=True,
    flags=re.IGNORECASE  # 不区分大小写
)
```

### 实际应用示例

```python
from logify import get_logger, ConsoleHandler, RegexFilter

logger = get_logger("myapp")

# 过滤敏感信息
handler = ConsoleHandler()

# 拒绝包含密码、密钥等敏感词的日志
sensitive_filter = RegexFilter(
    pattern=r"(password|secret|api_key|token)",
    match_pass=False,
    flags=re.IGNORECASE
)
handler.add_filter(sensitive_filter)

logger.add_handler(handler)

logger.info("用户登录成功")                    # 会显示
logger.info("密码验证: password=123456")       # 不会显示
logger.debug("API Token: abc123")             # 不会显示
```

---

## ContextFilter 上下文过滤器

根据日志记录的上下文属性（如 Logger 名称、线程、进程等）进行过滤。

### 按 Logger 名称过滤

```python
from logify import get_logger, ConsoleHandler, ContextFilter

# 创建多个 logger
app_logger = get_logger("myapp")
db_logger = get_logger("myapp.db")
api_logger = get_logger("myapp.api")
third_party = get_logger("urllib3")

handler = ConsoleHandler()

# 只允许 myapp 开头的 logger
filter = ContextFilter(allowed_names={"myapp", "myapp.db", "myapp.api"})
handler.add_filter(filter)

app_logger.add_handler(handler)
db_logger.add_handler(handler)
api_logger.add_handler(handler)
third_party.add_handler(handler)

app_logger.info("应用日志")      # 会显示
db_logger.info("数据库日志")     # 会显示
third_party.info("第三方日志")   # 不会显示
```

### 拒绝特定 Logger

```python
from logify import ContextFilter

# 拒绝某些嘈杂的 Logger
filter = ContextFilter(denied_names={"urllib3", "requests"})
```

### 链式配置

```python
from logify import ContextFilter

filter = ContextFilter()
filter.allow_name("myapp")
filter.allow_name("myapp.db")
filter.deny_name("myapp.debug")
```

### 按线程/进程过滤

```python
import threading
from logify import ContextFilter

# 只允许主线程的日志
main_thread_id = threading.main_thread().ident
filter = ContextFilter(allowed_threads={main_thread_id})

# 或按线程名称
filter = ContextFilter(allowed_threads={"MainThread", "WorkerThread"})

# 按进程 ID
import os
filter = ContextFilter(allowed_processes={os.getpid()})
```

### 自定义检查函数

```python
from logify import ContextFilter, LogRecord

def check_has_user_id(record: LogRecord) -> bool:
    """只允许包含 user_id 的日志"""
    return 'user_id' in record.extra

filter = ContextFilter(custom_check=check_has_user_id)

# 使用
logger.info("普通日志")                           # 不会显示
logger.info("用户操作", extra={"user_id": 123})  # 会显示
```

---

## FilterChain 过滤器链

将多个过滤器组合使用，只有所有过滤器都通过，日志才会被处理。

### 基本使用

```python
from logify import FilterChain, LevelFilter, RegexFilter, LogLevel

chain = FilterChain()

# 添加多个过滤器
chain.add_filter(LevelFilter(LogLevel.INFO))
chain.add_filter(RegexFilter(r"user", match_pass=True))

# 只有 INFO 及以上级别，且包含 "user" 的日志才会通过
```

### 在 Logger 上使用

```python
from logify import get_logger, LevelFilter, RegexFilter

logger = get_logger("myapp")

# 添加多个过滤器
logger.add_filter(LevelFilter(LogLevel.INFO))
logger.add_filter(RegexFilter(r"important", match_pass=True))

# 链式调用
logger.add_filter(LevelFilter(LogLevel.WARNING)).add_filter(
    RegexFilter(r"error", match_pass=True)
)
```

### 管理过滤器

```python
from logify import FilterChain, LevelFilter

chain = FilterChain()
level_filter = LevelFilter()

# 添加
chain.add_filter(level_filter)

# 检查
print(chain.filters)  # 获取所有过滤器

# 移除
chain.remove_filter(level_filter)

# 清空
chain.clear()
```

---

## 上下文管理

Logify 提供了强大的上下文管理功能，可以为日志添加额外的上下文信息。

### 设置永久上下文

```python
from logify import get_logger

logger = get_logger("myapp")

# 设置额外数据（会添加到每条日志）
logger.set_extra(
    app_version="1.0.0",
    environment="production"
)

logger.info("应用启动")
# 日志会包含 app_version 和 environment

# 清除额外数据
logger.clear_extra()
```

### 临时上下文（上下文管理器）

```python
from logify import get_logger

logger = get_logger("myapp")

def handle_request(request_id, user_id):
    # 临时添加请求相关上下文
    with logger.context(request_id=request_id, user_id=user_id):
        logger.info("开始处理请求")
        # 在这个块内的所有日志都会包含 request_id 和 user_id
        process_data()
        logger.info("请求处理完成")
    
    # 离开 with 块后，上下文自动移除
    logger.info("这条日志不包含 request_id")
```

### 嵌套上下文

```python
from logify import get_logger

logger = get_logger("myapp")

with logger.context(request_id="req-123"):
    logger.info("外层上下文")
    
    with logger.context(step="validation"):
        logger.info("嵌套上下文")
        # 包含 request_id 和 step
    
    logger.info("回到外层")
    # 只包含 request_id
```

### 使用 extra 参数

```python
from logify import get_logger

logger = get_logger("myapp")

# 在单条日志中添加额外数据
logger.info("用户登录", extra={
    "user_id": 12345,
    "ip_address": "192.168.1.100",
    "login_method": "oauth"
})
```

---

## 自定义过滤器

继承 `BaseFilter` 创建自定义过滤器：

### 基本结构

```python
from logify import BaseFilter, LogRecord

class MyFilter(BaseFilter):
    """自定义过滤器"""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        # 初始化
    
    def filter(self, record: LogRecord) -> bool:
        """过滤日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            True 表示通过，False 表示拒绝
        """
        # 你的过滤逻辑
        return True
```

### 示例：采样过滤器

```python
import random
from logify import BaseFilter, LogRecord

class SamplingFilter(BaseFilter):
    """采样过滤器，只保留一定比例的日志"""
    
    def __init__(self, rate: float = 0.1, name: str = ""):
        super().__init__(name)
        self.rate = rate  # 0.1 = 10%
    
    def filter(self, record: LogRecord) -> bool:
        return random.random() < self.rate

# 使用：只保留 10% 的 DEBUG 日志
sampling_filter = SamplingFilter(rate=0.1)
```

### 示例：速率限制过滤器

```python
import time
from collections import defaultdict
from logify import BaseFilter, LogRecord

class RateLimitFilter(BaseFilter):
    """速率限制过滤器，防止日志刷屏"""
    
    def __init__(
        self,
        max_records: int = 100,
        period: float = 60.0,
        name: str = ""
    ):
        super().__init__(name)
        self.max_records = max_records
        self.period = period
        self._counts = defaultdict(list)
    
    def filter(self, record: LogRecord) -> bool:
        now = time.time()
        key = f"{record.name}:{record.level}"
        
        # 清理过期记录
        self._counts[key] = [
            t for t in self._counts[key]
            if now - t < self.period
        ]
        
        # 检查是否超过限制
        if len(self._counts[key]) >= self.max_records:
            return False
        
        self._counts[key].append(now)
        return True

# 使用：每分钟最多 100 条同类型日志
rate_filter = RateLimitFilter(max_records=100, period=60)
```

### 示例：关键词高亮过滤器

```python
from logify import BaseFilter, LogRecord

class KeywordFilter(BaseFilter):
    """关键词过滤器，只保留包含指定关键词的日志"""
    
    def __init__(self, keywords: list, name: str = ""):
        super().__init__(name)
        self.keywords = [kw.lower() for kw in keywords]
    
    def filter(self, record: LogRecord) -> bool:
        message = record.message.lower()
        return any(kw in message for kw in self.keywords)

# 使用
keyword_filter = KeywordFilter(keywords=["error", "warning", "critical"])
```

---

## 函数追踪装饰器

Logify 提供了 `@logger.trace` 装饰器，自动记录函数的进入和退出。

### 基本使用

```python
from logify import get_logger

logger = get_logger("myapp")

@logger.trace
def process_data(data):
    """处理数据的函数"""
    result = data.upper()
    return result

process_data("hello")
```

输出：

```
2026-01-02 10:30:45 - myapp - DEBUG - Entering process_data
2026-01-02 10:30:45 - myapp - DEBUG - Exiting process_data
```

### 自定义日志级别

```python
from logify import get_logger, LogLevel

logger = get_logger("myapp")

@logger.trace(level=LogLevel.INFO)
def important_function():
    pass

# 日志级别为 INFO
```

### 异常处理

```python
from logify import get_logger

logger = get_logger("myapp")

@logger.trace
def risky_function():
    raise ValueError("Something went wrong")

try:
    risky_function()
except ValueError:
    pass
```

输出：

```
DEBUG - Entering risky_function
ERROR - Exception in risky_function: Something went wrong
Traceback (most recent call last):
  ...
```

---

## 在 Handler 和 Logger 上添加过滤器

### 在 Logger 上添加

Logger 过滤器会影响所有处理器：

```python
from logify import get_logger, LevelFilter

logger = get_logger("myapp")

# 添加到 Logger
logger.add_filter(LevelFilter(LogLevel.WARNING))

# 所有日志都会先经过这个过滤器
```

### 在 Handler 上添加

Handler 过滤器只影响该处理器：

```python
from logify import get_logger, ConsoleHandler, FileHandler, LevelFilter

logger = get_logger("myapp")

# 控制台显示所有级别
console = ConsoleHandler()
logger.add_handler(console)

# 文件只记录 ERROR 及以上
file_handler = FileHandler("error.log")
file_handler.add_filter(LevelFilter(LogLevel.ERROR))
logger.add_handler(file_handler)
```

---

## 小结

在本教程中，你学会了：

1. ✅ 使用 `LevelFilter` 按级别过滤
2. ✅ 使用 `RegexFilter` 按内容过滤
3. ✅ 使用 `ContextFilter` 按上下文过滤
4. ✅ 组合多个过滤器
5. ✅ 使用上下文管理器添加临时上下文
6. ✅ 创建自定义过滤器
7. ✅ 使用 `@trace` 装饰器追踪函数

### 下一步

- 📖 [教程 05：配置管理](05_configuration.md) - 从文件加载配置
- 📖 [教程 06：高级用法与最佳实践](06_advanced.md) - 进阶技巧

---

[← 上一篇：处理器详解](03_handlers.md) | [返回目录](README.md) | [下一篇：配置管理 →](05_configuration.md)
