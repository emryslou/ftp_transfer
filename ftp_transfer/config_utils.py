import os
import traceback
import uuid
from typing import Dict, Any, Tuple, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'ftp_transfer', 'config.yaml')


def _ensure_directory_exists(directory_path: str) -> None:
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            logger.info(f"创建目录: {directory_path}")
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise


def generate_trace_id() -> str:
    """生成一个唯一的追踪ID"""
    return str(uuid.uuid4())


def generate_archive_dir() -> str:
    """生成临时存档目录路径"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'ftp_transfer', 'archives', timestamp)
    _ensure_directory_exists(archive_dir)
    return archive_dir


def prepare_ftp_connection(config: Dict[str, Any], ftp_type: str) -> Dict[str, Any]:
    """准备FTP连接配置，确保所有必要的配置项都存在"""
    if ftp_type not in config:
        logger.error(f"配置中缺少{ftp_type}配置")
        raise ValueError(f"配置中缺少{ftp_type}配置")
    
    ftp_config = config[ftp_type]
    
    # 确保必要的配置项存在
    required_keys = ['host', 'port', 'user', 'password', 'directory', 'encoding']
    for key in required_keys:
        if key not in ftp_config:
            logger.error(f"{ftp_type}配置中缺少{key}")
            raise ValueError(f"{ftp_type}配置中缺少{key}")
    
    return ftp_config


def validate_config_structure(config: Dict[str, Any]) -> None:
    """验证配置结构的完整性"""
    # 验证必要的配置部分
    required_sections = ['source', 'destination', 'log']
    for section in required_sections:
        if section not in config:
            logger.error(f"配置中缺少{section}部分")
            raise ValueError(f"配置中缺少{section}部分")
    
    # 验证源FTP配置
    prepare_ftp_connection(config, 'source')
    
    # 验证目标FTP配置
    prepare_ftp_connection(config, 'destination')
    
    # 验证日志配置
    log_config = config['log']
    if 'file' not in log_config:
        log_config['file'] = 'ftp_transfer.log'
    if 'rotation' not in log_config:
        log_config['rotation'] = '1 week'
    if 'retention' not in log_config:
        log_config['retention'] = '1 month'
    if 'level' not in log_config:
        log_config['level'] = 'INFO'
    
    # 如果存在邮件配置，验证其结构
    if 'email' in config:
        email_config = config['email']
        if email_config.get('enable', False):
            email_required_keys = ['subject', 'sender', 'recipients', 'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password']
            for key in email_required_keys:
                if key not in email_config:
                    logger.warning(f"邮件配置中缺少{key}，可能影响邮件发送功能")
            
            if 'failure_threshold' not in email_config:
                email_config['failure_threshold'] = 3