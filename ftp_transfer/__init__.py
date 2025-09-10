"""
FTP Transfer Tool
一个用于在FTP服务器之间传输文件并提供通知功能的工具包
"""

__version__ = "0.0.8.1"
__author__ = "Emrys.Liu"
__email__ = "emrys.liu@foxmail.com"

from .core import FTPTransfer
from .config import load_config
