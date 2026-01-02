# Logify

一个功能完善、易于扩展的 Python 日志处理模块。

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 特性

- **简洁直观的 API** - 类似于 Python 标准库 logging 的使用方式，零学习成本
- **多种日志级别** - 支持 DEBUG、INFO、WARNING、ERROR、CRITICAL 五个级别
- **灵活的格式化选项** - 支持文本格式、JSON 格式、彩色终端输出
- **多种输出目标** - 控制台、文件、网络（TCP/UDP/HTTP）
- **日志文件轮转** - 支持按文件大小轮转和按时间轮转
- **异步日志处理** - 非阻塞写入，避免影响主程序性能
- **强大的过滤机制** - 支持级别过滤、正则过滤、上下文过滤
- **配置文件支持** - 支持 JSON、YAML、TOML 格式的配置文件
- **上下文管理** - 支持临时添加上下文信息，方便请求追踪
- **函数追踪装饰器** - 自动记录函数的进入和退出

## 安装

从源码安装：

```bash
git clone https://github.com/your-username/logify.git
cd logify
pip install -e .
```

## 快速开始

### 基本用法

```python
from logify import get_logger

# 获取 logger
logger = get_logger("myapp")

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 使用便捷函数

```python
from logify import info, error, debug

info("应用启动")
debug("调试信息")
error("发生错误")
```

### 快速配置

```python
from logify import basic_config, INFO

basic_config(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log"  # 可选，不指定则输出到控制台
)
```

## 使用示例

### 输出到文件

```python
from logify import get_logger, FileHandler

logger = get_logger("myapp")
handler = FileHandler("app.log")
logger.add_handler(handler)

logger.info("这条日志将写入文件")
```

### JSON 格式日志

```python
from logify import get_logger, FileHandler, JsonFormatter

logger = get_logger("myapp")
handler = FileHandler("app.json")
handler.formatter = JsonFormatter(indent=2)
logger.add_handler(handler)

logger.info("结构化日志", extra={"user_id": 123, "action": "login"})
```

输出示例：
```json
{
  "timestamp": "2025-01-02T10:30:00",
  "level": "INFO",
  "logger": "myapp",
  "message": "结构化日志",
  "user_id": 123,
  "action": "login"
}
```

### 彩色控制台输出

```python
from logify import get_logger, ConsoleHandler, ColorFormatter

logger = get_logger("myapp")
handler = ConsoleHandler()
handler.formatter = ColorFormatter()
logger.add_handler(handler)

logger.debug("青色")
logger.info("绿色")
logger.warning("黄色")
logger.error("红色")
```

### 日志文件轮转

按文件大小轮转：

```python
from logify import get_logger, RotatingFileHandler

logger = get_logger("myapp")
handler = RotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,              # 保留 5 个备份
    compress=True                # 压缩备份文件
)
logger.add_handler(handler)
```

按时间轮转：

```python
from logify import get_logger, TimedRotatingFileHandler

logger = get_logger("myapp")
handler = TimedRotatingFileHandler(
    filename="app.log",
    when="MIDNIGHT",    # 每天午夜轮转
    backup_count=30     # 保留 30 天
)
logger.add_handler(handler)
```

### 异步日志处理

```python
from logify import get_logger, AsyncHandler, FileHandler

logger = get_logger("myapp")
file_handler = FileHandler("app.log")
async_handler = AsyncHandler(file_handler, queue_size=10000)
logger.add_handler(async_handler)

# 日志将异步写入，不阻塞主程序
logger.info("异步写入")
```

### 使用上下文

```python
from logify import get_logger

logger = get_logger("myapp")

# 临时添加上下文信息
with logger.context(request_id="abc-123", user="admin"):
    logger.info("处理请求")  # 日志将包含 request_id 和 user
    logger.info("请求完成")

# 离开 with 块后，上下文自动清除
logger.info("新的请求")  # 不再包含之前的上下文
```

### 函数追踪装饰器

```python
from logify import get_logger

logger = get_logger("myapp")

@logger.trace
def process_data(data):
    return data.upper()

process_data("hello")
# 输出:
# DEBUG - Entering process_data(data='hello')
# DEBUG - Exiting process_data -> 'HELLO'
```

### 过滤器

级别过滤：

```python
from logify import get_logger, ConsoleHandler, LevelFilter, WARNING

logger = get_logger("myapp")
handler = ConsoleHandler()
handler.add_filter(LevelFilter(level=WARNING))  # 只记录 WARNING 及以上
logger.add_handler(handler)
```

正则过滤：

```python
from logify import get_logger, ConsoleHandler, RegexFilter

logger = get_logger("myapp")
handler = ConsoleHandler()
# 过滤掉包含敏感信息的日志
handler.add_filter(RegexFilter(r"password|secret", match_pass=False))
logger.add_handler(handler)
```

### 从配置文件加载

```python
from logify import configure_from_file, get_logger

# 支持 JSON、YAML、TOML 格式
configure_from_file("config/logging.json")

logger = get_logger("myapp")
logger.info("使用配置文件")
```

配置文件示例 (logging.json)：

```json
{
  "version": 1,
  "loggers": {
    "myapp": {
      "level": "DEBUG",
      "handlers": ["console", "file"]
    }
  },
  "handlers": {
    "console": {
      "class": "ConsoleHandler",
      "level": "INFO",
      "formatter": "colored"
    },
    "file": {
      "class": "RotatingFileHandler",
      "filename": "app.log",
      "max_bytes": 10485760,
      "backup_count": 5,
      "formatter": "json"
    }
  },
  "formatters": {
    "colored": {
      "class": "ColorFormatter"
    },
    "json": {
      "class": "JsonFormatter"
    }
  }
}
```

## 项目结构

```
logify/
├── __init__.py          # 包入口，导出所有公共 API
├── api/
│   └── logger.py        # Logger 日志记录器
├── core/
│   ├── levels.py        # 日志级别定义
│   ├── manager.py       # Logger 管理器
│   └── record.py        # 日志记录数据结构
├── handlers/
│   ├── base.py          # 处理器基类
│   ├── console.py       # 控制台处理器
│   ├── file.py          # 文件处理器
│   ├── rotating.py      # 日志轮转处理器
│   ├── async_handler.py # 异步处理器
│   └── network.py       # 网络处理器
├── formatters/
│   ├── base.py          # 格式化器基类
│   ├── text.py          # 文本格式化器
│   ├── json_formatter.py# JSON 格式化器
│   └── color.py         # 彩色格式化器
├── filters/
│   ├── base.py          # 过滤器基类
│   ├── level_filter.py  # 级别过滤器
│   ├── regex_filter.py  # 正则过滤器
│   └── context_filter.py# 上下文过滤器
└── config/
    ├── loader.py        # 配置加载器
    └── parser.py        # 配置解析器
```

## 扩展开发

Logify 提供了良好的扩展性，你可以轻松创建自定义组件：

### 自定义处理器

```python
from logify import BaseHandler, LogRecord

class MyHandler(BaseHandler):
    def emit(self, record: LogRecord) -> None:
        # 实现你的日志输出逻辑
        formatted = self.formatter.format(record)
        # ... 发送到你的目标
```

### 自定义格式化器

```python
from logify import BaseFormatter, LogRecord

class MyFormatter(BaseFormatter):
    def format(self, record: LogRecord) -> str:
        # 实现你的格式化逻辑
        return f"[{record.level_name}] {record.message}"
```

### 自定义过滤器

```python
from logify import BaseFilter, LogRecord

class MyFilter(BaseFilter):
    def filter(self, record: LogRecord) -> bool:
        # 返回 True 表示通过，False 表示过滤掉
        return "secret" not in record.message.lower()
```

## 文档

- [API 文档](logify/API.md) - 完整的 API 参考
- [架构设计](logify/ARCHITECTURE.md) - 了解 Logify 的内部设计
- [教程系列](docs/tutorials/README.md) - 从入门到精通的完整教程

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块的测试
pytest tests/handlers/

# 运行并生成覆盖率报告
pytest tests/ --cov=logify --cov-report=html
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

