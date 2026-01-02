# Logify 教程 05：配置管理

> 难度：中级 | 预计阅读时间：15 分钟

## 目录

- [配置概述](#配置概述)
- [从字典配置](#从字典配置)
- [从文件配置](#从文件配置)
- [ConfigLoader 配置加载器](#configloader-配置加载器)
- [ConfigParser 配置解析器](#configparser-配置解析器)
- [环境变量配置](#环境变量配置)
- [注册自定义组件](#注册自定义组件)
- [配置最佳实践](#配置最佳实践)
- [小结](#小结)

---

## 配置概述

Logify 提供了多种配置方式：

| 方式 | 适用场景 |
|------|----------|
| 字典配置 | 程序化配置 |
| 文件配置 | 生产环境，支持 JSON/YAML/TOML |
| 环境变量 | 容器化部署 |

---

## 从字典配置

使用字典进行更灵活的配置，适合程序化生成配置。

### 配置格式

```python
from logify import configure_from_dict

config = {
    "version": 1,
    "formatters": {
        "simple": {
            "class": "TextFormatter",
            "format": "%(asctime)s - %(levelname)s - %(message)s"
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
            "formatter": "simple"
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        },
        "myapp": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }
}

# 应用配置
parser = configure_from_dict(config)
```

### 使用配置后的 Logger

```python
from logify import get_logger

# 配置完成后，获取 logger 使用
logger = get_logger("myapp")
logger.info("应用启动")

root = get_logger("root")
root.debug("根日志")
```

---

## 从文件配置

支持从 JSON、YAML、TOML 文件加载配置。

### JSON 配置文件

`config/logging.json`:

```json
{
    "version": 1,
    "formatters": {
        "standard": {
            "class": "TextFormatter",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "class": "JsonFormatter",
            "indent": null
        }
    },
    "handlers": {
        "console": {
            "class": "ConsoleHandler",
            "level": "DEBUG",
            "formatter": "standard"
        },
        "file": {
            "class": "RotatingFileHandler",
            "filename": "logs/app.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "level": "INFO",
            "formatter": "standard"
        },
        "json_file": {
            "class": "RotatingFileHandler",
            "filename": "logs/app.json",
            "max_bytes": 52428800,
            "backup_count": 10,
            "level": "DEBUG",
            "formatter": "json"
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file", "json_file"]
        }
    }
}
```

加载配置：

```python
from logify import configure_from_file, get_logger

# 从 JSON 文件加载
configure_from_file("config/logging.json")

# 使用
logger = get_logger("myapp")
logger.info("配置加载完成")
```

### YAML 配置文件

`config/logging.yaml`:

```yaml
version: 1

formatters:
  standard:
    class: TextFormatter
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  
  json:
    class: JsonFormatter
    indent: null
    extra_fields:
      app: myapp
      env: production

handlers:
  console:
    class: ConsoleHandler
    level: DEBUG
    formatter: standard
  
  file:
    class: RotatingFileHandler
    filename: logs/app.log
    max_bytes: 10485760  # 10MB
    backup_count: 5
    level: INFO
    formatter: standard
  
  error_file:
    class: FileHandler
    filename: logs/error.log
    level: ERROR
    formatter: standard

loggers:
  root:
    level: DEBUG
    handlers:
      - console
      - file
      - error_file
  
  myapp.db:
    level: WARNING
    handlers:
      - file
    propagate: false
```

> 注意：使用 YAML 需要安装 PyYAML: `pip install pyyaml`

```python
from logify import configure_from_file

configure_from_file("config/logging.yaml")
```

### TOML 配置文件

`config/logging.toml`:

```toml
version = 1

[formatters.standard]
class = "TextFormatter"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

[formatters.json]
class = "JsonFormatter"

[handlers.console]
class = "ConsoleHandler"
level = "DEBUG"
formatter = "standard"

[handlers.file]
class = "RotatingFileHandler"
filename = "logs/app.log"
max_bytes = 10485760
backup_count = 5
level = "INFO"
formatter = "standard"

[loggers.root]
level = "DEBUG"
handlers = ["console", "file"]
```

> 注意：Python 3.11+ 内置 tomllib，低版本需安装: `pip install toml`

```python
from logify import configure_from_file

configure_from_file("config/logging.toml")
```

---

## ConfigLoader 配置加载器

`ConfigLoader` 提供了灵活的配置加载方式。

### 基本使用

```python
from logify import ConfigLoader

loader = ConfigLoader()

# 从文件加载
loader.load_from_file("config/base.json")

# 从字典加载（合并）
loader.load_from_dict({
    "loggers": {
        "myapp": {"level": "DEBUG"}
    }
})

# 获取配置
config = loader.config
print(config)
```

### 链式加载

```python
from logify import ConfigLoader

# 链式调用
loader = (
    ConfigLoader()
    .load_from_file("config/base.json")      # 基础配置
    .load_from_file("config/production.json") # 生产环境覆盖
    .load_from_dict({"loggers": {"root": {"level": "WARNING"}}})
)

config = loader.config
```

### 获取嵌套配置

```python
from logify import ConfigLoader

loader = ConfigLoader()
loader.load_from_file("config/logging.json")

# 使用点号获取嵌套值
level = loader.get("loggers.root.level", default="INFO")
filename = loader.get("handlers.file.filename")
```

### 合并配置

```python
from logify import ConfigLoader

# 基础配置
base = ConfigLoader()
base.load_from_file("config/base.json")

# 环境配置
env_config = ConfigLoader()
env_config.load_from_file("config/production.json")

# 合并（env_config 覆盖 base）
base.merge(env_config)

final_config = base.config
```

---

## ConfigParser 配置解析器

`ConfigParser` 解析配置并创建日志组件。

### 基本使用

```python
from logify import ConfigParser

config = {
    "formatters": {...},
    "handlers": {...},
    "loggers": {...}
}

parser = ConfigParser(config)
parser.parse()

# 获取已创建的组件
formatter = parser.get_formatter("standard")
handler = parser.get_handler("console")
```

### 从文件创建

```python
from logify import ConfigParser

# 一步完成加载和解析
parser = ConfigParser.from_file("config/logging.json")

# 组件已创建，可以获取
console_handler = parser.get_handler("console")
```

### 可用的组件类

**格式化器：**
- `TextFormatter`
- `JsonFormatter`
- `ColorFormatter`

**处理器：**
- `ConsoleHandler`
- `FileHandler`
- `RotatingFileHandler`
- `TimedRotatingFileHandler`

**过滤器：**
- `LevelFilter`
- `RegexFilter`
- `ContextFilter`

---

## 环境变量配置

支持从环境变量加载配置，适合容器化部署。

### 基本使用

```python
import os
from logify import ConfigLoader

# 设置环境变量
os.environ["LOGIFY_LEVEL"] = "DEBUG"
os.environ["LOGIFY_HANDLERS_FILE_FILENAME"] = "/var/log/app.log"

# 从环境变量加载
loader = ConfigLoader()
loader.load_from_env(prefix="LOGIFY_")

# 获取值
level = loader.get("level")  # "DEBUG"
filename = loader.get("handlers.file.filename")  # "/var/log/app.log"
```

### 自定义映射

```python
from logify import ConfigLoader

# 使用自定义映射
loader = ConfigLoader()
loader.load_from_env(
    mapping={
        "LOG_LEVEL": "loggers.root.level",
        "LOG_FILE": "handlers.file.filename",
        "LOG_FORMAT": "formatters.standard.format"
    }
)
```

### 结合文件和环境变量

```python
from logify import ConfigLoader, ConfigParser

loader = ConfigLoader()

# 1. 加载基础配置文件
loader.load_from_file("config/logging.json")

# 2. 用环境变量覆盖
loader.load_from_env(prefix="LOGIFY_")

# 3. 解析配置
parser = ConfigParser(loader)
parser.parse()
```

### 值自动解析

环境变量的值会自动解析：

```python
os.environ["LOGIFY_DEBUG"] = "true"      # -> True (bool)
os.environ["LOGIFY_PORT"] = "9000"       # -> 9000 (int)
os.environ["LOGIFY_RATE"] = "0.5"        # -> 0.5 (float)
os.environ["LOGIFY_HOSTS"] = '["a","b"]' # -> ["a", "b"] (list)
```

---

## 注册自定义组件

可以注册自定义的格式化器、处理器、过滤器，使其可在配置文件中使用。

### 注册自定义格式化器

```python
from logify import ConfigParser, BaseFormatter

class MyFormatter(BaseFormatter):
    def format(self, record):
        return f"[{record.level_name}] {record.message}"

# 注册
ConfigParser.register_formatter("MyFormatter", MyFormatter)

# 现在可以在配置中使用
config = {
    "formatters": {
        "my": {
            "class": "MyFormatter"
        }
    }
}
```

### 注册自定义处理器

```python
from logify import ConfigParser, BaseHandler

class SlackHandler(BaseHandler):
    def __init__(self, webhook_url, **kwargs):
        super().__init__(**kwargs)
        self.webhook_url = webhook_url
    
    def emit(self, record):
        # 发送到 Slack
        pass

# 注册
ConfigParser.register_handler("SlackHandler", SlackHandler)

# 在配置中使用
config = {
    "handlers": {
        "slack": {
            "class": "SlackHandler",
            "webhook_url": "https://hooks.slack.com/...",
            "level": "CRITICAL"
        }
    }
}
```

### 注册自定义过滤器

```python
from logify import ConfigParser, BaseFilter

class SamplingFilter(BaseFilter):
    def __init__(self, rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.rate = rate
    
    def filter(self, record):
        import random
        return random.random() < self.rate

# 注册
ConfigParser.register_filter("SamplingFilter", SamplingFilter)

# 在配置中使用
config = {
    "filters": {
        "sampling": {
            "class": "SamplingFilter",
            "rate": 0.1
        }
    }
}
```

---

## 配置最佳实践

### 1. 分环境配置

```
config/
├── base.json         # 基础配置
├── development.json  # 开发环境
├── staging.json      # 预发布环境
└── production.json   # 生产环境
```

```python
import os
from logify import ConfigLoader, ConfigParser

env = os.getenv("ENV", "development")

loader = ConfigLoader()
loader.load_from_file("config/base.json")
loader.load_from_file(f"config/{env}.json")

parser = ConfigParser(loader)
parser.parse()
```

### 2. 使用环境变量覆盖敏感配置

```python
from logify import ConfigLoader, ConfigParser
import os

loader = ConfigLoader()
loader.load_from_file("config/logging.json")

# 用环境变量覆盖生产配置
if os.getenv("ENV") == "production":
    loader.load_from_env(
        mapping={
            "LOG_LEVEL": "loggers.root.level",
            "LOG_DIR": "handlers.file.filename"
        }
    )

parser = ConfigParser(loader)
parser.parse()
```

### 3. 配置验证

```python
from logify import ConfigLoader

def validate_config(config: dict) -> bool:
    """验证配置有效性"""
    required_keys = ["loggers"]
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key: {key}")
    
    if "root" not in config.get("loggers", {}):
        raise ValueError("Missing root logger configuration")
    
    return True

loader = ConfigLoader()
loader.load_from_file("config/logging.json")

validate_config(loader.config)
```

### 4. 完整示例

```python
"""
日志配置模块

使用方法：
    from logging_config import setup_logging
    setup_logging()
"""

import os
from pathlib import Path
from logify import ConfigLoader, ConfigParser, get_logger

def setup_logging(config_dir: str = "config"):
    """设置日志系统"""
    
    env = os.getenv("ENV", "development")
    config_path = Path(config_dir)
    
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 加载配置
    loader = ConfigLoader()
    
    # 基础配置
    base_config = config_path / "logging.json"
    if base_config.exists():
        loader.load_from_file(base_config)
    
    # 环境配置
    env_config = config_path / f"logging.{env}.json"
    if env_config.exists():
        loader.load_from_file(env_config)
    
    # 环境变量覆盖
    loader.load_from_env(prefix="LOGIFY_")
    
    # 解析并应用配置
    parser = ConfigParser(loader)
    parser.parse()
    
    # 返回根 logger
    return get_logger("root")


# 使用
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("日志系统初始化完成")
```

---

## 小结

在本教程中，你学会了：

1. ✅ 从字典配置日志系统
3. ✅ 从 JSON/YAML/TOML 文件加载配置
4. ✅ 使用 `ConfigLoader` 加载和合并配置
5. ✅ 使用 `ConfigParser` 解析配置
6. ✅ 从环境变量加载配置
7. ✅ 注册自定义组件
8. ✅ 配置管理最佳实践

### 下一步

- 📖 [教程 06：高级用法与最佳实践](06_advanced.md) - 进阶技巧和性能优化

---

[← 上一篇：过滤器与上下文](04_filters_context.md) | [返回目录](README.md) | [下一篇：高级用法与最佳实践 →](06_advanced.md)
