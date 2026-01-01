# Logify 教程 02：日志格式化器

> 难度：入门 | 预计阅读时间：15 分钟

## 目录

- [格式化器简介](#格式化器简介)
- [TextFormatter 文本格式化器](#textformatter-文本格式化器)
- [JsonFormatter JSON 格式化器](#jsonformatter-json-格式化器)
- [ColorFormatter 彩色格式化器](#colorformatter-彩色格式化器)
- [自定义格式化器](#自定义格式化器)
- [小结](#小结)

---

## 格式化器简介

格式化器（Formatter）负责将日志记录转换为最终输出的字符串。Logify 提供了三种内置格式化器：

| 格式化器 | 用途 |
|----------|------|
| `TextFormatter` | 传统文本格式，支持自定义模板 |
| `JsonFormatter` | JSON 格式，适合日志分析系统 |
| `ColorFormatter` | 彩色输出，适合控制台显示 |

---

## TextFormatter 文本格式化器

`TextFormatter` 是最常用的格式化器，使用类似 Python logging 的格式化字符串语法。

### 基本使用

```python
from logify import get_logger, ConsoleHandler, TextFormatter

logger = get_logger("myapp")

# 创建格式化器
formatter = TextFormatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 创建处理器并设置格式化器
handler = ConsoleHandler()
handler.formatter = formatter
logger.add_handler(handler)

logger.info("Hello, World!")
```

输出：

```
2026-01-02 10:30:45 - myapp - INFO - Hello, World!
```

### 可用的占位符

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `%(asctime)s` | 时间戳 | `2026-01-02 10:30:45` |
| `%(name)s` | Logger 名称 | `myapp` |
| `%(levelname)s` | 日志级别名称 | `INFO` |
| `%(levelno)d` | 日志级别数值 | `20` |
| `%(message)s` | 日志消息 | `Hello, World!` |
| `%(filename)s` | 源文件名 | `main.py` |
| `%(lineno)d` | 源代码行号 | `42` |
| `%(funcName)s` | 函数名 | `process_data` |
| `%(thread)d` | 线程 ID | `12345` |
| `%(threadName)s` | 线程名称 | `MainThread` |
| `%(process)d` | 进程 ID | `1234` |

### 常用格式模板

```python
# 简洁格式
fmt1 = "%(levelname)s: %(message)s"
# 输出: INFO: Hello, World!

# 开发调试格式
fmt2 = "[%(asctime)s] %(levelname)s %(filename)s:%(lineno)d - %(message)s"
# 输出: [2026-01-02 10:30:45] INFO main.py:42 - Hello, World!

# 生产环境格式
fmt3 = "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s"
# 输出: 2026-01-02 10:30:45 | myapp | INFO     | Hello, World!

# 详细格式（包含线程信息）
fmt4 = "%(asctime)s [%(thread)d] %(name)s %(levelname)s - %(message)s"
# 输出: 2026-01-02 10:30:45 [12345] myapp INFO - Hello, World!
```

### 自定义日期格式

```python
# ISO 格式
formatter = TextFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
# 输出: 2026-01-02T10:30:45

# 仅时间
formatter = TextFormatter(datefmt="%H:%M:%S")
# 输出: 10:30:45

# 包含毫秒
formatter = TextFormatter(datefmt="%Y-%m-%d %H:%M:%S.%f")
# 输出: 2026-01-02 10:30:45.123456
```

---

## JsonFormatter JSON 格式化器

`JsonFormatter` 将日志输出为 JSON 格式，非常适合与日志分析系统（如 ELK、Splunk）配合使用。

### 基本使用

```python
from logify import get_logger, ConsoleHandler, JsonFormatter

logger = get_logger("myapp")

formatter = JsonFormatter()
handler = ConsoleHandler()
handler.formatter = formatter
logger.add_handler(handler)

logger.info("用户登录", extra={"user_id": 12345})
```

输出：

```json
{"timestamp": "2026-01-02T10:30:45", "level": "INFO", "logger": "myapp", "message": "用户登录", "user_id": 12345, "filename": "main.py", "lineno": 10}
```

### 配置选项

```python
from logify import JsonFormatter

# 自定义字段列表
formatter = JsonFormatter(
    fields=["timestamp", "level", "message", "logger"]
)
# 只输出指定的字段

# 格式化输出（带缩进）
formatter = JsonFormatter(indent=2)
# 输出带缩进的 JSON

# 添加固定字段
formatter = JsonFormatter(
    extra_fields={
        "app": "myapp",
        "env": "production",
        "version": "1.0.0"
    }
)
# 每条日志都包含这些固定字段

# 使用 epoch 时间戳
formatter = JsonFormatter(timestamp_format="epoch")
# 时间戳输出为 Unix 时间戳
```

### 完整配置示例

```python
from logify import get_logger, FileHandler, JsonFormatter

logger = get_logger("myapp")

# 创建适合日志分析的 JSON 格式化器
formatter = JsonFormatter(
    fields=["timestamp", "level", "logger", "message", "filename", "lineno"],
    extra_fields={
        "service": "user-service",
        "env": "production"
    },
    indent=None,  # 不格式化，每行一条记录
    ensure_ascii=False  # 支持中文
)

handler = FileHandler("app.json.log")
handler.formatter = formatter
logger.add_handler(handler)

logger.info("服务启动")
```

---

## ColorFormatter 彩色格式化器

`ColorFormatter` 为控制台输出添加 ANSI 颜色，使日志更易于阅读。

### 基本使用

```python
from logify import get_logger, ConsoleHandler, ColorFormatter

logger = get_logger("myapp")

formatter = ColorFormatter()
handler = ConsoleHandler()
handler.formatter = formatter
logger.add_handler(handler)

logger.debug("调试信息")    # 青色
logger.info("一般信息")     # 绿色
logger.warning("警告信息")  # 黄色
logger.error("错误信息")    # 红色
logger.critical("严重错误") # 亮红色+粗体
```

### 默认颜色方案

| 级别 | 颜色 |
|------|------|
| DEBUG | 青色 (Cyan) |
| INFO | 绿色 (Green) |
| WARNING | 黄色 (Yellow) |
| ERROR | 红色 (Red) |
| CRITICAL | 亮红色 + 粗体 |

### 自定义颜色

```python
from logify import ColorFormatter, Colors, LogLevel

formatter = ColorFormatter()

# 使用预定义颜色常量
formatter.set_level_color(LogLevel.DEBUG, Colors.BLUE)
formatter.set_level_color(LogLevel.INFO, Colors.WHITE)
formatter.set_level_color(LogLevel.WARNING, Colors.MAGENTA)

# 可用的颜色常量
# Colors.BLACK, Colors.RED, Colors.GREEN, Colors.YELLOW
# Colors.BLUE, Colors.MAGENTA, Colors.CYAN, Colors.WHITE
# Colors.BRIGHT_RED, Colors.BRIGHT_GREEN, ...
# Colors.BOLD, Colors.RESET
```

### 配置选项

```python
from logify import ColorFormatter

# 自定义格式模板
formatter = ColorFormatter(
    fmt="[%(asctime)s] %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)

# 只给级别名称着色，消息不着色
formatter = ColorFormatter(
    colorize_message=False,
    colorize_level=True
)

# 强制使用颜色（即使输出不是终端）
formatter = ColorFormatter(force_colors=True)
```

---

## 自定义格式化器

你可以通过继承 `BaseFormatter` 来创建自定义格式化器。

### 基本结构

```python
from logify import BaseFormatter, LogRecord

class MyFormatter(BaseFormatter):
    """自定义格式化器"""
    
    def format(self, record: LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            格式化后的字符串
        """
        # 实现你的格式化逻辑
        output = f"[{record.level_name}] {record.message}"
        
        # 如果有异常信息，添加异常堆栈
        if record.exception_info:
            output += "\n" + self.format_exception(record)
        
        return output
```

### 示例：XML 格式化器

```python
from logify import BaseFormatter, LogRecord

class XMLFormatter(BaseFormatter):
    """XML 格式化器"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: LogRecord) -> str:
        lines = ['<log>']
        lines.append(f'  <timestamp>{record.formatted_time}</timestamp>')
        lines.append(f'  <level>{record.level_name}</level>')
        lines.append(f'  <logger>{record.name}</logger>')
        lines.append(f'  <message>{self._escape_xml(record.message)}</message>')
        
        if self.include_extra and record.extra:
            lines.append('  <extra>')
            for key, value in record.extra.items():
                lines.append(f'    <{key}>{self._escape_xml(str(value))}</{key}>')
            lines.append('  </extra>')
        
        if record.exception_info:
            lines.append(f'  <exception>{self._escape_xml(self.format_exception(record))}</exception>')
        
        lines.append('</log>')
        return '\n'.join(lines)
    
    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )
```

### 示例：表格格式化器

```python
from logify import BaseFormatter, LogRecord

class TableFormatter(BaseFormatter):
    """表格格式化器"""
    
    def __init__(self, columns=None):
        super().__init__()
        self.columns = columns or ['time', 'level', 'logger', 'message']
        self.col_width = {
            'time': 19,
            'level': 8,
            'logger': 15,
            'message': 50
        }
    
    def format(self, record: LogRecord) -> str:
        data = {
            'time': record.formatted_time,
            'level': record.level_name,
            'logger': record.name,
            'message': record.message
        }
        
        parts = []
        for col in self.columns:
            value = str(data.get(col, ''))
            width = self.col_width.get(col, 20)
            parts.append(value[:width].ljust(width))
        
        return ' | '.join(parts)
```

---

## 为处理器设置格式化器

每个处理器可以有自己的格式化器：

```python
from logify import (
    get_logger,
    ConsoleHandler, FileHandler,
    ColorFormatter, JsonFormatter, TextFormatter
)

logger = get_logger("myapp")

# 控制台使用彩色格式
console = ConsoleHandler()
console.formatter = ColorFormatter(
    fmt="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger.add_handler(console)

# 文件使用 JSON 格式（方便分析）
file_handler = FileHandler("app.json.log")
file_handler.formatter = JsonFormatter()
logger.add_handler(file_handler)

# 另一个文件使用详细文本格式
detail_handler = FileHandler("app.detail.log")
detail_handler.formatter = TextFormatter(
    fmt="%(asctime)s [%(thread)d] %(name)s %(levelname)s %(filename)s:%(lineno)d - %(message)s"
)
logger.add_handler(detail_handler)

# 同一条日志会以不同格式输出到不同目标
logger.info("应用启动")
```

---

## 小结

在本教程中，你学会了：

1. ✅ 使用 `TextFormatter` 自定义文本格式
2. ✅ 使用 `JsonFormatter` 输出结构化日志
3. ✅ 使用 `ColorFormatter` 美化控制台输出
4. ✅ 创建自定义格式化器
5. ✅ 为不同处理器设置不同格式化器

### 下一步

- 📖 [教程 03：处理器详解](03_handlers.md) - 学习日志输出到不同目标
- 📖 [教程 04：过滤器与上下文](04_filters_context.md) - 了解如何过滤和添加上下文

---

[← 上一篇：快速入门](01_quick_start.md) | [返回目录](README.md) | [下一篇：处理器详解 →](03_handlers.md)
