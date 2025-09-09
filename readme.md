# FTP Transfer Tool

一个功能强大的FTP文件传输工具，用于在FTP服务器之间高效传输文件并提供完整的通知功能。支持配置文件驱动、文件过滤、自动归档和多平台兼容。

## 功能特点

- **多服务器文件传输**：从源FTP服务器扫描并上传文件到目标FTP服务器
- **灵活的文件过滤**：通过文件模式和排除模式精确控制需要传输的文件
- **安全的文件处理**：支持文件存在检查，可配置是否覆盖现有文件
- **完整的归档机制**：上传成功后将源文件自动移动到指定目录
- **详细的日志记录**：使用loguru库实现全面的日志记录，支持日志轮转和压缩
- **智能邮件通知**：根据执行情况（成功、部分成功、失败）发送不同的邮件通知
- **配置文件驱动**：基于YAML配置文件，易于管理和自动化部署
- **跨平台兼容**：同时支持Windows、Linux、macOS等操作系统

## 安装方法

### 从PyPI安装
```bash
pip install ftp_transfer
```

### 从源码安装
```bash
# 克隆仓库
# git clone https://github.com/yourusername/ftp_transfer.git
cd ftp_transfer

# 安装
pip install .
```

### 开发模式安装
```bash
pip install -e .
```

## 快速开始

### 1. 创建配置文件

您可以使用以下命令创建新的配置文件：

```bash
ftp_transfer create-config [配置文件路径]
```

如果不指定路径，将在默认位置创建配置文件。

### 2. 查看配置示例

如果需要查看完整的配置示例，可以使用：

```bash
ftp_transfer config-example
```

### 3. 更新配置

您可以使用命令行参数更新配置：

```bash
ftp_transfer update-config [配置文件路径] source.port=2121 email.enable=false
```

也可以使用交互式向导修改配置：

```bash
ftp_transfer interactive-update-config [配置文件路径]
```

### 4. 执行文件传输

```bash
ftp_transfer --config [配置文件路径]
# 或者直接使用默认配置
ftp_transfer
```

## 命令行接口

FTP Transfer 工具提供了丰富的命令行接口：

```
ftp_transfer [命令] [参数]
```

### 全局参数
- `-c, --config`: 指定配置文件路径
- `--version, -v`: 显示版本信息

### 子命令
- `transfer`: 执行文件传输（默认命令）
- `update-config`: 更新配置文件，格式为 `key=value`
- `interactive-update-config`: 使用交互式向导更新配置
- `create-config`: 创建新的配置文件
- `config-example`: 显示配置文件示例
- `version`: 显示版本信息及更新内容

## 配置说明

配置文件使用YAML格式，主要包含以下部分：

### 源FTP服务器配置
```yaml
source:
  host: "source.example.com"  # 源FTP服务器地址
  port: 21                    # 源FTP服务器端口
  username: "username"        # 用户名
  password: "password"        # 密码
  use_passive: true           # 是否使用被动模式
  directory: "/path/to/source/directory"  # 源目录
  file_patterns: ["*.txt", "*.pdf"]  # 要传输的文件模式
  exclude_patterns: ["*.tmp", ".*~"]  # 要排除的文件模式
```

### 目标FTP服务器配置
```yaml
destination:
  host: "destination.example.com"  # 目标FTP服务器地址
  port: 21                        # 目标FTP服务器端口
  username: "username"            # 用户名
  password: "password"            # 密码
  use_passive: true               # 是否使用被动模式
  directory: "/path/to/destination/directory"  # 目标目录
  overwrite: true                 # 是否覆盖已存在的文件
  preserve_structure: true        # 是否保留目录结构
  archive_after_transfer: true    # 传输后是否归档源文件
  archive_dir: "/path/to/archive"  # 归档目录
```

### 文件传输配置
```yaml
transfer:
  chunk_size: 8192   # 传输块大小
  max_retries: 3     # 最大重试次数
  retry_delay: 5     # 重试间隔（秒）
  timeout: 30        # 超时时间（秒）
```

### 日志配置
```yaml
log:
  level: "INFO"              # 日志级别：DEBUG, INFO, WARNING, ERROR
  file: "/path/to/log/ftp_transfer.log"  # 日志文件路径
  rotation: "1 week"         # 日志轮转策略
  retention: "1 month"       # 日志保留时间
  compression: "gz"          # 压缩格式
```

### 邮件通知配置
```yaml
email:
  enable: false                  # 是否启用邮件通知
  smtp_server: "smtp.example.com"  # SMTP服务器地址
  smtp_port: 587                 # SMTP服务器端口
  username: "email@example.com"   # 邮箱用户名
  password: "password"            # 邮箱密码
  use_tls: true                  # 是否使用TLS加密
  from_email: "email@example.com" # 发件人邮箱
  to_emails: ["recipient@example.com"]  # 收件人邮箱列表
  subject: "FTP文件传输结果通知"     # 邮件主题
```

## 邮件通知场景

工具会根据不同的执行情况发送相应的邮件通知：

1. **完全成功**：发送统计信息，包括找到的文件列表和数量
2. **部分成功**：列出失败的文件及原因
3. **失败过多**：当失败文件数量超过阈值时发送警告
4. **服务器连接失败**：专门报告连接错误

## 部署说明

### 常规部署
1. 安装Python 3.6或更高版本
2. 安装ftp_transfer包：`pip install ftp_transfer`
3. 创建配置文件并根据您的需求进行配置
4. 通过命令行或脚本执行文件传输任务

### 定时任务部署

在Linux系统上，您可以使用cron来设置定时任务：

```bash
# 编辑crontab配置
crontab -e

# 添加定时任务（每天凌晨2点执行）
0 2 * * * /path/to/python /path/to/ftp_transfer --config /path/to/config.yaml >> /path/to/cron.log 2>&1
```

在Windows系统上，您可以使用任务计划程序来设置定时任务。

## 注意事项

1. 确保FTP服务器的连接信息正确无误
2. 确保目标目录和归档目录存在且具有写入权限
3. 对于大批量文件传输，建议适当调整`chunk_size`和`timeout`参数
4. 在生产环境中使用时，建议启用日志轮转和压缩功能
5. 对于重要任务，建议启用邮件通知功能以便及时了解任务执行情况

## 跨平台兼容性

本工具支持以下操作系统：
- Windows
- Linux
- macOS

工具会自动适应不同操作系统的文件路径和系统特性，确保在各种环境下都能正常工作。

## 许可证

MIT License

## 版本信息

要查看当前版本和更新内容，可以使用以下命令：

```bash
ftp_transfer -v
```
