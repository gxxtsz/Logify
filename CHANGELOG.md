# 更新日志

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [0.1.0] - 2025-01-02

### 新增功能

- Logify 首次发布
- 核心日志功能：`Logger` 和 `LoggerManager`
- 日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
- `LogRecord` 日志记录数据类

### 处理器

- `ConsoleHandler` - 控制台输出（stdout/stderr）
- `FileHandler` - 文件输出
- `RotatingFileHandler` - 按文件大小轮转
- `TimedRotatingFileHandler` - 按时间轮转
- `AsyncHandler` - 异步日志处理
- `NetworkHandler` - 网络日志（TCP/UDP/HTTP）

### 格式化器

- `TextFormatter` - 自定义文本格式
- `JsonFormatter` - 结构化 JSON 输出
- `ColorFormatter` - 终端彩色输出

### 过滤器

- `LevelFilter` - 按日志级别过滤
- `RegexFilter` - 按正则表达式过滤
- `ContextFilter` - 按上下文属性过滤

### 配置管理

- `ConfigLoader` - 从 JSON/YAML/TOML 文件加载配置
- `ConfigParser` - 解析并应用配置
- `basic_config()` - 快速配置函数
- `configure_from_file()` - 从文件配置
- `configure_from_dict()` - 从字典配置

### 特性

- 上下文管理器：临时添加上下文数据
- `@logger.trace` 装饰器：函数调用追踪
- 层级式 Logger 名称与日志传播
- 模块级便捷函数（debug、info、warning、error、critical）
