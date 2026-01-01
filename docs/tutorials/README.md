# Logify 教程系列

欢迎来到 Logify 教程系列！本教程将带你从入门到精通，全面掌握 Logify 日志库的使用。

## 关于 Logify

Logify 是一个功能完善、易于扩展的 Python 日志处理模块。它提供了：

- 简洁直观的 API
- 多种日志级别支持
- 灵活的格式化选项（文本、JSON、彩色输出）
- 多种输出目标（控制台、文件、网络）
- 日志文件自动轮转
- 异步日志处理
- 强大的过滤机制
- 配置文件支持（JSON/YAML/TOML）

---

## 教程目录

### 入门篇 (Beginner)

适合刚开始使用 Logify 的用户。

| 教程 | 主题 | 预计时间 |
|------|------|----------|
| [01. 快速入门](01_quick_start.md) | 基本概念、日志级别、第一个日志程序 | 10 分钟 |
| [02. 日志格式化器](02_formatters.md) | TextFormatter、JsonFormatter、ColorFormatter | 15 分钟 |

### 中级篇 (Intermediate)

适合已经了解基础，想深入学习的用户。

| 教程 | 主题 | 预计时间 |
|------|------|----------|
| [03. 处理器详解](03_handlers.md) | 控制台、文件、轮转、异步、网络处理器 | 20 分钟 |
| [04. 过滤器与上下文](04_filters_context.md) | 级别过滤、正则过滤、上下文管理 | 15 分钟 |
| [05. 配置管理](05_configuration.md) | 文件配置、环境变量、ConfigLoader | 15 分钟 |

### 高级篇 (Advanced)

适合需要在生产环境使用或进行高级定制的用户。

| 教程 | 主题 | 预计时间 |
|------|------|----------|
| [06. 高级用法与最佳实践](06_advanced.md) | 性能优化、结构化日志、生产部署 | 25 分钟 |

---

## 快速开始

如果你是第一次使用 Logify，只需几行代码即可开始：

```python
from logify import get_logger

# 获取 logger
logger = get_logger("myapp")

# 记录日志
logger.info("Hello, Logify!")
logger.debug("Debug message")
logger.error("Error occurred")
```

更多详情请查看 [快速入门教程](01_quick_start.md)。

---

## 学习路径

### 路径 1：快速上手（30 分钟）

如果你只是想快速使用 Logify：

1. 阅读 [01. 快速入门](01_quick_start.md)
2. 阅读 [02. 日志格式化器](02_formatters.md)（浏览常用格式）

### 路径 2：完整学习（2 小时）

如果你想全面掌握 Logify：

1. 按顺序阅读所有教程
2. 完成每个教程末尾的示例代码
3. 尝试修改示例，加深理解

### 路径 3：生产部署（1 小时）

如果你需要在生产环境使用：

1. 阅读 [03. 处理器详解](03_handlers.md)（重点关注轮转处理器）
2. 阅读 [05. 配置管理](05_configuration.md)
3. 阅读 [06. 高级用法与最佳实践](06_advanced.md)

---

## 常用示例代码

### 基础使用

```python
from logify import get_logger

logger = get_logger("myapp")
logger.info("应用启动")
```

### 输出到文件

```python
from logify import get_logger, FileHandler

logger = get_logger("myapp")
logger.add_handler(FileHandler("app.log"))
logger.info("写入文件")
```

### JSON 格式日志

```python
from logify import get_logger, FileHandler, JsonFormatter

logger = get_logger("myapp")
handler = FileHandler("app.json")
handler.formatter = JsonFormatter()
logger.add_handler(handler)
```

### 日志轮转

```python
from logify import get_logger, RotatingFileHandler

logger = get_logger("myapp")
handler = RotatingFileHandler(
    "app.log",
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5
)
logger.add_handler(handler)
```

### 从配置文件加载

```python
from logify import configure_from_file, get_logger

configure_from_file("config/logging.json")
logger = get_logger("myapp")
```

---

## 其他资源

- [API 文档](../../logify/API.md) - 完整的 API 参考
- [架构设计](../../logify/ARCHITECTURE.md) - 了解 Logify 的内部设计

---

## 版本信息

本教程基于 Logify v0.1.0 编写。

---

## 反馈与贡献

如果你发现教程中的问题或有改进建议，欢迎提交 Issue 或 Pull Request。

---

**祝你学习愉快！** 🎉
