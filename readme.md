# FTP Transfer Tool

一个功能强大的FTP/SFTP文件传输工具，用于在FTP/SFTP服务器之间高效传输文件并提供完整的通知功能。支持配置文件驱动、文件过滤、自动归档和多平台兼容。

## 功能特点

- **多服务器文件传输**：从源FTP/SFTP服务器扫描并上传文件到目标FTP/SFTP服务器
- **灵活的文件过滤**：通过文件模式、扩展名、时间戳等多种方式精确控制需要传输的文件
- **安全的文件处理**：支持文件存在检查，可配置三种不同的文件存在处理策略（跳过、覆盖、重命名）
- **完整的归档机制**：上传成功后将源文件自动移动到指定目录或跳过备份
- **详细的日志记录**：实现全面的日志记录，支持日志级别设置
- **智能邮件通知**：根据执行情况（成功、部分成功、失败）发送不同的邮件通知
- **配置文件驱动**：基于YAML配置文件，易于管理和自动化部署
- **跨平台兼容**：同时支持Windows、Linux、macOS等操作系统
- **支持SFTP协议**：同时支持传统FTP和安全的SFTP协议传输
- **支持FTPS协议**：支持通过TLS加密的FTPS协议传输

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

### 源服务器配置
```yaml
source:
  host: "source.example.com"  # 源FTP/SFTP服务器地址
  port: 21                    # 端口，FTP默认21，SFTP默认22
  user: "username"            # 用户名
  password: "password"        # 密码
  directory: "/path/to/source"  # 源目录路径
  encoding: utf-8             # 文件编码，默认为utf-8
  use_ftps: false             # 是否使用FTPS，默认false
  tls_implicit: false         # 是否使用隐式TLS，默认false
  use_passive: true           # 是否使用被动模式，默认true
  enable_backup: true         # 处理完成后是否备份文件到备份目录，默认true
  backup_directory: "/path/to/backup"  # 备份目录路径
  use_sftp: false             # 是否使用SFTP，默认false
  key_file: "/path/to/key.pem"  # SFTP私钥文件路径
  passphrase: "your_passphrase"  # SFTP私钥密码
  
  # 文件过滤规则配置
  file_filter:
    type: "modification_time"  # 文件过滤类型，可选值：all(全部文件), pattern(按字符匹配), extension(按后缀匹配), modification_time(按修改时间)
    pattern: "*.txt"           # 当type为pattern时，指定匹配模式
    extensions: ["txt", "csv", "xlsx"]  # 当type为extension时，指定文件后缀列表
    time_value: # 当type为modification_time时，指定时间值
      - "2023-01-02 00:00:00"   # 当type为modification_time时，指定时间值
      - "2023-01-01 00:00:00"   # 当type为modification_time时，指定时间值
```
### 文件过滤规则说明
* 当type为`all`时，不进行文件过滤
* 当type为`pattern`时，根据`pattern`进行文件过滤
   ```pattern = foo* 表示 foo 开头的所有文件
   pattern = *bar 表示 bar 结尾的所有文件
   pattern = *bar* 表示包含 bar 的所有文件
   pattern = foo*bar 表示 foo 开头且包含 bar 的所有文件
   pattern = *bar*baz 表示包含 bar 且包含 baz 的所有文件
   pattern = *barbaz* 表示包含 barbaz 的所有文件
* 当type为`extension`时，根据`extensions`进行文件过滤```
* 当type为`modification_time`时，根据`time_value`进行文件过滤
   ```time_value: # 表示 2023 年 1 月 2 日 00:00:00 之后修改的文件
    - "2023-01-02 00:00:00"  # 表示 2023 年 1 月 2 日 00:00:00 之后修改的文件
   time_value: # 表示 文件时间在 2023 年 1 月 2 日 00:00:00 到 2023 年 1 月 3 日 00:00:00 之间
    - "2023-01-02 00:00:00"  # 表示 2023 年 1 月 2 日 00:00:00 之前修改的文件
    - "2022-01-01 00:00:00"  # 表示 2022 年 1 月 1 日 00:00:00 之前修改的文件
   time_value: #
    - "current_day"  # 表示当前日期之前修改的文件
   time_value: # 文件时间在 最近一天修改的文件
    - "current_day"  # 表示当前日期之前修改的文件
    - "days_before_1"  # 表示当前周之前修改的文件```

### 时间值说明
```
时间值，格式：YYYY-MM-DD HH:MM:SS, 或者 current_day, current_hour, current_minute, current_time, days_before_{n}, hours_before_{n}, minutes_before_{n}
假设当前时间为 2025-09-11 12:15:31.383282
**current_day** -- 当天: 例如 2025-09-11 00:00:00, # 动态计算
**current_hour** -- 当前小时: 例如 2025-09-11 12:00:00, # 动态计算
**current_minute** -- 当前分钟: 例如 2025-09-11 12:15:00, # 动态计算
**current_time** -- 当前时间: 例如 2025-09-11 12:15:31, # 动态计算
**days_before_{n}** -- 前n天: 例如 days_before_1 -- 前1天: 2025-09-10 00:00:00, days_before_2 -- 前2天: 2025-09-09 00:00:00, # 动态计算
**hours_before_{n}** -- 前n小时: 例如 hours_before_1 -- 前1小时: 2025-09-11 11:00:00, hours_before_2 -- 前2小时: 2025-09-11 10:00:00, # 动态计算
**minutes_before_{n}** -- 前n分钟: 例如 minutes_before_1 -- 前1分钟: 2025-09-11 12:14:00, minutes_before_2 -- 前2分钟: 2025-09-11 12:13:00, # 动态计算
```

### 目标服务器配置
```yaml
destination:
  host: "destination.example.com"  # 目标FTP/SFTP服务器地址
  port: 21                        # 端口，FTP默认21，SFTP默认22
  user: "username"                # 用户名
  password: "password"            # 密码
  directory: "/path/to/destination"  # 目标目录路径
  encoding: utf-8                 # 文件编码，默认为utf-8
  use_ftps: false                 # 是否使用FTPS，默认false
  tls_implicit: false             # 是否使用隐式TLS，默认false
  use_passive: true               # 是否使用被动模式，默认true
  use_sftp: false                 # 是否使用SFTP，默认false
  key_file: "/path/to/key.pem"    # SFTP私钥文件路径
  passphrase: "your_passphrase"    # SFTP私钥密码
  file_exists_strategy: "rename"  # 文件存在处理策略，可选值：skip(跳过), overwrite(覆盖), rename(重命名)
```

### 文件存在处理策略说明

目标服务器上已存在同名文件时，工具提供三种不同的处理策略：

- **skip**: 当目标服务器中已存在同名文件时，跳过该文件的上传
- **overwrite**: 当目标服务器中已存在同名文件时，覆盖已存在的文件
- **rename**: 当目标服务器中已存在同名文件时，生成带时间戳的新文件名进行上传

### 日志配置
```yaml
log:
  enabled: true              # 是否启用日志，默认true
  level: "INFO"              # 日志级别：DEBUG, INFO, WARNING, ERROR
  file: "/path/to/ftp_transfer.log"  # 日志文件路径
```

### 邮件通知配置
```yaml
email:
  enabled: false                  # 是否启用邮件通知，默认false
  smtp_server: "smtp.example.com"  # SMTP服务器地址
  smtp_port: 587                 # SMTP服务器端口
  use_tls: true                  # 是否使用TLS，默认true
  username: "email@example.com"   # 发件人邮箱
  password: "email_password"      # 发件人密码或授权码
  from_address: "email@example.com" # 发件人地址
  to_address: "recipient@example.com"  # 收件人地址
  subject: "FTP/SFTP传输任务完成通知"  # 邮件主题
  failure_threshold: 3           # 失败文件数量阈值，超过此值发送警告邮件
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

1. 确保FTP/SFTP服务器的连接信息正确无误
2. 确保目标目录和归档目录存在且具有写入权限
3. 对于大批量文件传输，建议根据网络情况调整超时设置
4. 在生产环境中使用时，建议启用日志功能以便追踪问题
5. 对于重要任务，建议启用邮件通知功能以便及时了解任务执行情况
6. 使用SFTP协议时，确保私钥文件权限正确（推荐600权限）
7. 对于文件存在处理策略，建议根据实际业务需求选择合适的选项
8. 在跨时区环境中使用时，注意文件时间戳的处理可能会有差异

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
