import os
import sys
import site
import importlib.resources
from typing import List, Tuple, Callable, Optional

def _get_system_share_paths() -> List[str]:
    """获取系统共享目录路径（跨平台兼容）"""
    share_paths = []
    
    # 根据操作系统类型添加系统标准共享目录
    if os.name == 'posix':  # Unix/Linux/macOS
        if os.path.exists('/usr/share'):
            share_paths.append('/usr/share')
        if os.path.exists('/usr/local/share'):
            share_paths.append('/usr/local/share')
    elif os.name == 'nt':  # Windows
        # Windows没有标准的share目录，我们可以添加Program Files下的可能位置
        program_files = os.environ.get('ProgramFiles', '')
        if program_files and os.path.exists(program_files):
            share_paths.append(os.path.join(program_files, 'Common Files'))
    
    # 添加Python的site-packages中的共享目录
    try:
        for site_path in site.getsitepackages():
            share_path = os.path.join(site_path, 'share')
            if os.path.exists(share_path):
                share_paths.append(share_path)
    except AttributeError:
        # 某些Python环境可能没有getsitepackages方法
        pass
    
    # 添加用户目录
    user_home = os.path.expanduser('~')
    if os.name == 'posix':
        user_share = os.path.join(user_home, '.local', 'share')
    elif os.name == 'nt':
        user_share = os.path.join(user_home, 'AppData', 'Local')
    
    if user_share and os.path.exists(user_share):
        share_paths.append(user_share)
    
    return share_paths

def _paths_to_try(file_path: str) -> List[Callable[[], str]]:
    """生成尝试查找文件的多个路径函数（跨平台兼容）"""
    return [
        # 方式1: 从当前工作目录查找
        lambda: os.path.join(os.getcwd(), file_path),
        # 方式2: 从包安装位置的父目录查找
        lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path),
        # 方式3: 从Python安装目录查找
        lambda: os.path.join(os.path.dirname(sys.executable), file_path),
        # 方式4: 从用户目录查找
        lambda: os.path.join(os.path.expanduser('~'), file_path),
    ]

def _get_installed_examples_paths() -> List[str]:
    """获取安装后的examples目录路径（跨平台兼容）"""
    example_paths = []
    
    # 获取系统共享目录
    for share_path in _get_system_share_paths():
        example_paths.append(os.path.join(share_path, 'ftp_transfer', 'examples'))
    
    # 添加Python安装目录下的share路径
    python_share = os.path.join(os.path.dirname(sys.executable), 'share', 'ftp_transfer', 'examples')
    example_paths.append(python_share)
    
    # Windows特定路径
    if os.name == 'nt':
        # 添加可能的Windows安装路径
        program_files = os.environ.get('ProgramFiles', '')
        if program_files:
            example_paths.append(os.path.join(program_files, 'ftp_transfer', 'examples'))
        
        # 添加AppData路径
        app_data = os.environ.get('APPDATA', '')
        if app_data:
            example_paths.append(os.path.join(app_data, 'ftp_transfer', 'examples'))
    
    return example_paths

def find_from_examples(file_name: str) -> str:
    """从 examples 目录查找文件，支持开发环境和安装环境"""
    # 首先尝试开发环境中的examples目录
    for path_func in _paths_to_try(os.path.join('examples', file_name)):
        path = path_func()
        if os.path.exists(path):
            return path
    
    # 然后尝试安装环境中的examples目录
    for examples_path in _get_installed_examples_paths():
        path = os.path.join(examples_path, file_name)
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"无法找到 {file_name}。请确认包已正确安装，或尝试重新安装。")

def find_from_package(file_name: str) -> str:
    """从包安装位置查找文件"""
    for path_func in _paths_to_try(file_name):
        path = path_func()
        if os.path.exists(path):
            return path
    
    # 尝试从系统共享目录查找
    for share_path in _get_system_share_paths():
        path = os.path.join(share_path, 'doc', 'ftp_transfer', file_name)
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"无法找到 {file_name}")

def read_example_file(file_name: str) -> str:
    """读取示例文件内容，提供完整的错误处理"""
    try:
        file_path = find_from_examples(file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        # 作为最后的后备，提供一个内置的配置示例
        if file_name == 'ftp_config.yaml.example':
            return """
# FTP文件传输配置示例

# 源FTP服务器配置
source:
  host: "source.example.com"
  port: 21
  username: "username"
  password: "password"
  use_passive: true
  directory: "/path/to/source/directory"
  file_patterns: ["*.txt", "*.pdf"]
  exclude_patterns: ["*.tmp", ".*~"]

# 目标FTP服务器配置
destination:
  host: "destination.example.com"
  port: 21
  username: "username"
  password: "password"
  use_passive: true
  directory: "/path/to/destination/directory"
  overwrite: true
  preserve_structure: true
  archive_after_transfer: true
  archive_dir: "/path/to/archive"

# 文件传输配置
transfer:
  chunk_size: 8192
  max_retries: 3
  retry_delay: 5
  timeout: 30

# 日志配置
log:
  level: "INFO"
  file: "/path/to/log/ftp_transfer.log"
  rotation: "1 week"
  retention: "1 month"
  compression: "gz"

# 通知配置
email:
  enable: false
  smtp_server: "smtp.example.com"
  smtp_port: 587
  username: "email@example.com"
  password: "password"
  use_tls: true
  from_email: "email@example.com"
  to_emails: ["recipient@example.com"]
  subject: "FTP文件传输结果通知"
"""
        raise e
