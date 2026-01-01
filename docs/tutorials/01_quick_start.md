# Logify 教程 01：快速入门

> 难度：入门 | 预计阅读时间：10 分钟

## 目录

- [简介](#简介)
- [安装](#安装)
- [第一个日志程序](#第一个日志程序)
- [日志级别](#日志级别)
- [格式化消息](#格式化消息)
- [记录异常信息](#记录异常信息)
- [小结](#小结)

---

## 简介

Logify 是一个功能完善、易于扩展的 Python 日志处理模块。它提供了类似于 Python 标准库 `logging` 的 API，但更加简洁易用，同时提供了更丰富的功能特性。

### 主要特性

- 简洁的 API 设计
- 多种日志级别支持
- 灵活的格式化选项（文本、JSON、彩色输出）
- 多种输出目标（控制台、文件、网络）
- 日志文件自动轮转
- 异步日志处理
- 强大的过滤机制
- 配置文件支持

---

## 安装

将 Logify 添加到你的项目中：

```python
# 假设 logify 已在你的项目路径中
from logify import get_logger
```

---

## 第一个日志程序

让我们从最简单的例子开始：

```python
from logify import get_logger

# 获取一个 logger 实例
logger = get_logger("myapp")

# 记录一条信息日志
logger.info("Hello, Logify!")
```

运行这段代码，你将在控制台看到类似这样的输出：

```
2026-01-02 10:30:45 - myapp - INFO - Hello, Logify!
```

### 代码解析

1. `get_logger("myapp")` - 获取或创建一个名为 "myapp" 的 logger
2. `logger.info(...)` - 使用 INFO 级别记录日志

---

## 日志级别

Logify 提供了 5 个标准日志级别，从低到高分别是：

| 级别 | 数值 | 用途 |
|------|------|------|
| `DEBUG` | 10 | 调试信息，用于开发阶段 |
| `INFO` | 20 | 一般信息，记录程序正常运行状态 |
| `WARNING` | 30 | 警告信息，表示潜在问题 |
| `ERROR` | 40 | 错误信息，表示程序遇到问题 |
| `CRITICAL` | 50 | 严重错误，可能导致程序无法继续运行 |

### 使用不同级别

```python
from logify import get_logger

logger = get_logger("myapp")

logger.debug("这是调试信息")
logger.info("这是一般信息")
logger.warning("这是警告信息")
logger.error("这是错误信息")
logger.critical("这是严重错误")
```

### 设置最低日志级别

默认情况下，logger 会记录所有级别的日志。你可以设置最低级别来过滤：

```python
from logify import get_logger, LogLevel, INFO

logger = get_logger("myapp")

# 方法 1：使用 LogLevel 枚举
logger.level = LogLevel.WARNING

# 方法 2：使用预定义常量
logger.level = INFO

# 方法 3：使用整数值
logger.level = 30  # 等同于 WARNING

# 设置后，只有 WARNING 及以上级别的日志才会被记录
logger.debug("不会显示")
logger.info("不会显示")
logger.warning("会显示")
logger.error("会显示")
```

---

## 格式化消息

Logify 支持使用 `%` 风格的字符串格式化：

```python
from logify import get_logger

logger = get_logger("myapp")

# 使用 % 格式化
name = "Alice"
age = 25
logger.info("用户 %s 已登录，年龄：%d", name, age)

# 支持多种格式化占位符
logger.info("价格：%.2f 元", 99.5)
logger.info("十六进制：%x", 255)
```

### 添加额外数据

你可以使用 `extra` 参数添加额外的上下文数据：

```python
logger.info("用户登录", extra={"user_id": 12345, "ip": "192.168.1.1"})
```

---

## 记录异常信息

在处理异常时，可以使用 `exc_info=True` 参数记录完整的异常堆栈：

```python
from logify import get_logger

logger = get_logger("myapp")

try:
    result = 10 / 0
except ZeroDivisionError:
    logger.error("计算出错", exc_info=True)
```

或者使用更简便的 `exception()` 方法：

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    logger.exception("计算出错")  # 自动包含异常信息
```

输出示例：

```
2026-01-02 10:30:45 - myapp - ERROR - 计算出错
Traceback (most recent call last):
  File "example.py", line 5, in <module>
    result = 10 / 0
ZeroDivisionError: division by zero
```

---

## 使用便捷函数

Logify 还提供了模块级的便捷函数，无需手动获取 logger：

```python
import logify

# 直接使用模块级函数
logify.debug("调试信息")
logify.info("一般信息")
logify.warning("警告信息")
logify.error("错误信息")
logify.critical("严重错误")

# 这些函数使用名为 "root" 的 logger
```

### 使用 basic_config 快速配置

```python
import logify
from logify import INFO

# 快速配置根 logger
logify.basic_config(
    level=INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

# 开始记录日志
logify.info("应用程序启动")
```

---

## 小结

在本教程中，你学会了：

1. ✅ 如何获取 logger 实例
2. ✅ 使用不同的日志级别
3. ✅ 格式化日志消息
4. ✅ 记录异常信息
5. ✅ 使用便捷函数

### 下一步

- 📖 [教程 02：日志格式化器](02_formatters.md) - 学习如何自定义日志输出格式
- 📖 [教程 03：处理器详解](03_handlers.md) - 了解如何将日志输出到不同目标

---

## 完整示例

```python
"""
Logify 快速入门示例
"""
from logify import get_logger, LogLevel, basic_config, INFO

# 配置根 logger
basic_config(level=INFO)

# 获取应用 logger
logger = get_logger("myapp")

def main():
    logger.info("应用程序启动")
    
    # 模拟一些操作
    for i in range(3):
        logger.debug("处理第 %d 项", i)  # 不会显示，因为级别是 INFO
    
    logger.info("处理完成")
    
    # 模拟错误处理
    try:
        process_data(None)
    except ValueError:
        logger.exception("数据处理失败")
    
    logger.info("应用程序结束")

def process_data(data):
    if data is None:
        raise ValueError("数据不能为空")
    return data

if __name__ == "__main__":
    main()
```

---

[返回目录](README.md) | [下一篇：日志格式化器 →](02_formatters.md)
