import yaml
import getpass
import traceback
import os
from loguru import logger
from typing import Dict, Any, Optional

def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    :param config_path: 配置文件路径
    :return: 配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        logger.debug(traceback.format_exc())
        raise
    except yaml.YAMLError as e:
        logger.error(f"配置文件格式错误: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def update_config(config_path: str, updates: Dict[str, Any]) -> None:
    """修改或补充现有配置文件
    
    Args:
        config_path: 配置文件路径
        updates: 要更新的配置内容
    """
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        # 加载现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # 递归更新配置
        def recursive_update(current: Dict[str, Any], update_values: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in update_values.items():
                if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                    # 如果当前值和新值都是字典，递归更新
                    current[key] = recursive_update(current[key], value)
                else:
                    # 否则直接替换
                    current[key] = value
            return current
        
        # 应用更新
        updated_config = recursive_update(config, updates)
        
        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"配置文件已成功更新: {config_path}")
        
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def server_config(_config: dict|None = None, backup: bool = True) -> dict: 
    """
    配置服务器信息
    
    :return: 服务器配置字典
    """

    default_config = {
        'use_sftp': input("是否使用SFTP? (y/n, 默认n): ").lower() == 'y', 
        'host': input("服务器地址: "),
        'port': None,
        'user': input("用户名: "),
        'password': None,
        'directory': input("目录路径: "),
        'encoding': input("文件编码 (默认: utf-8): ") or 'utf-8',
        'enable_backup': None,
        'backup_directory': None,
        'use_ftps': False,
        'tls_implicit': False,
        'use_passive': True,
        'key_file': None,
        'passphrase': None,
    }

    if backup:
        default_config['enable_backup'] = input("是否启用备份功能? (y/n, 默认y): ").lower() != 'n'
        if default_config['enable_backup']:
                default_config['backup_directory'] = input("备份目录路径 (可选，按Enter跳过): ") or None
    else:
        default_config['enable_backup'] = False

    # 如果使用SFTP，询问密钥文件和密码
    if default_config['use_sftp']:
        default_config['password'] = input("密码 (按Enter键如果不设置密码，使用密钥认证): ") or None
        default_config['port'] = int(input("端口 (默认: 22): ") or 21)
        if not default_config['password']:
            default_config['key_file'] = input("私钥文件路径 (可选，按Enter跳过): ") or None
            if not default_config['key_file']:
                default_config['passphrase'] = input("私钥密码 (可选，按Enter跳过): ") or None
    else:
        default_config['password'] = input("密码: ") or None
        default_config['use_ftps'] = input("是否使用FTPS? (y/n, 默认n): ").lower() == 'y'
        default_config['port'] = int(input("端口 (默认: FTP=21, FTPS=990)") or (990 if default_config['use_ftps'] else 21))
        default_config['tls_implicit'] = input("是否使用隐式TLS? (y/n, 默认n): ").lower() == 'y'
        default_config['use_passive'] = input("是否使用被动模式? (y/n, 默认y): ").lower() != 'n'
        
    return default_config

def update_server_config(server_config: dict, backup: bool = True) -> dict:
    """
    更新服务器配置
    
    :param server_config: 现有服务器配置
    :param backup: 是否启用备份配置
    :return: 更新后的服务器配置
    """
    # 复制配置，避免直接修改传入的字典
    updated_config = server_config.copy()
    
    # 确保所有必要的配置项存在
    default_server_config = {
        'host': '',
        'port': 21,
        'user': '',
        'password': None,
        'directory': '',
        'encoding': 'utf-8',
        'use_ftps': False,
        'tls_implicit': False,
        'use_passive': True,
        'use_sftp': False,
        'key_file': None,
        'passphrase': None
    }
    
    if backup:
        default_server_config['enable_backup'] = False
        default_server_config['backup_directory'] = None
    
    # 合并默认配置
    for key, default_value in default_server_config.items():
        if key not in updated_config:
            updated_config[key] = default_value
    
    print(f"当前地址: {updated_config['host']}")
    updated_config['host'] = input("新地址 (按Enter保持当前): ") or updated_config['host']
    
    print(f"当前端口: {updated_config['port']}")
    new_port = input("新端口 (按Enter保持当前): ")
    if new_port:
        updated_config['port'] = int(new_port)
    
    print(f"当前用户名: {updated_config['user']}")
    updated_config['user'] = input("新用户名 (按Enter保持当前): ") or updated_config['user']
    
    # 询问是否修改密码
    if input("是否修改密码? (y/n, 默认n): ").lower() == 'y':
        updated_config['password'] = input("新密码 (按Enter键如果不设置密码，使用密钥认证): ")
    
    print(f"当前目录: {updated_config['directory']}")
    updated_config['directory'] = input("新目录 (按Enter保持当前): ") or updated_config['directory']
    
    print(f"当前文件编码: {updated_config['encoding']}")
    updated_config['encoding'] = input("新编码 (按Enter保持当前): ") or updated_config['encoding']
    
    print(f"当前使用FTPS: {'是' if updated_config['use_ftps'] else '否'}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['use_ftps'] = input("是否使用FTPS? (y/n): ").lower() == 'y'
        if updated_config['use_ftps']:
            print(f"当前使用隐式TLS: {'是' if updated_config['tls_implicit'] else '否'}")
            if input("是否修改? (y/n, 默认n): ").lower() == 'y':
                updated_config['tls_implicit'] = input("是否使用隐式TLS? (y/n): ").lower() == 'y'
                # 如果使用隐式TLS且端口为21，自动调整为990
                if updated_config['tls_implicit'] and updated_config['port'] == 21:
                    print("检测到使用隐式TLS，自动将端口设置为990")
                    updated_config['port'] = 990
    
    print(f"当前使用被动模式: {'是' if updated_config['use_passive'] else '否'}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['use_passive'] = input("是否使用被动模式? (y/n): ").lower() != 'n'
    
    if backup:
        print(f"当前启用备份: {'是' if updated_config['enable_backup'] else '否'}")
        if input("是否修改? (y/n, 默认n): ").lower() == 'y':
            updated_config['enable_backup'] = input("是否启用备份功能? (y/n): ").lower() != 'n'
            if updated_config['enable_backup']:
                print(f"当前备份目录: {updated_config['backup_directory'] or '未设置'}")
                updated_config['backup_directory'] = input("新备份目录 (按Enter保持当前): ") or updated_config['backup_directory']
    
    # SFTP相关配置
    print(f"当前使用SFTP: {'是' if updated_config.get('use_sftp', False) else '否'}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['use_sftp'] = input("是否使用SFTP? (y/n): ").lower() == 'y'
        # 如果切换到SFTP且端口为21，自动调整为22
        if updated_config['use_sftp'] and updated_config['port'] == 21:
            print("检测到使用SFTP，自动将端口设置为22")
            updated_config['port'] = 22
    
    # 如果使用SFTP，询问密钥文件和密码
    if updated_config.get('use_sftp', False):
        print(f"当前私钥文件: {updated_config.get('key_file', None) or '未设置'}")
        updated_config['key_file'] = input("新私钥文件路径 (按Enter保持当前): ") or updated_config.get('key_file', None)
        
        # 询问是否修改私钥密码
        if input("是否修改私钥密码? (y/n, 默认n): ").lower() == 'y':
            updated_config['passphrase'] = input("新私钥密码 (按Enter键如果不设置): ") or None
    
    return updated_config

def update_file_filter_config(file_filter_config: dict) -> dict:
    """
    更新文件过滤规则配置
    
    :param file_filter_config: 现有文件过滤配置
    :return: 更新后的文件过滤配置
    """
    updated_config = file_filter_config.copy()
    
    # 确保所有必要的配置项存在
    default_file_filter_config = {
        'type': 'all'
    }
    
    # 合并默认配置
    for key, default_value in default_file_filter_config.items():
        if key not in updated_config:
            updated_config[key] = default_value
    
    print(f"当前过滤类型: {updated_config.get('type', 'all')}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['type'] = input("新过滤类型 (all/pattern/extension/creation_time/modification_time): ") or 'all'
        
        if updated_config['type'] == 'pattern':
            # 确保pattern配置项存在
            if 'pattern' not in updated_config:
                updated_config['pattern'] = ''
            
            current_pattern = updated_config.get('pattern', '')
            print(f"当前匹配模式: {current_pattern}")
            updated_config['pattern'] = input("新匹配模式 (如\"*.txt\"或\"report_2023*\"): ") or current_pattern
        elif updated_config['type'] == 'extension':
            # 确保extensions配置项存在
            if 'extensions' not in updated_config:
                updated_config['extensions'] = []
            
            current_extensions = updated_config.get('extensions', [])
            print(f"当前后缀列表: {', '.join(current_extensions) if current_extensions else '无'}")
            extensions_input = input("新后缀列表 (用逗号分隔，如\"txt,csv,xlsx\"): ")
            updated_config['extensions'] = [ext.strip() for ext in extensions_input.split(',')] if extensions_input else current_extensions
        elif updated_config['type'] in ['creation_time', 'modification_time']:
            # 确保time_type和time_value配置项存在
            if 'time_type' not in updated_config:
                updated_config['time_type'] = 'since'
            if 'time_value' not in updated_config:
                updated_config['time_value'] = ''
            
            current_time_type = updated_config.get('time_type', 'since')
            print(f"当前时间过滤类型: {current_time_type}")
            updated_config['time_type'] = input("新时间过滤类型 (since/before): ") or current_time_type
            
            current_time_value = updated_config.get('time_value', '')
            print(f"当前时间值: {current_time_value}")
            updated_config['time_value'] = input("新时间值 (格式: YYYY-MM-DD或YYYY-MM-DD HH:MM:SS): ") or current_time_value
    
    return updated_config

def update_log_config(log_config: dict) -> dict:
    """
    更新日志配置
    
    :param log_config: 现有日志配置
    :return: 更新后的日志配置
    """
    updated_config = log_config.copy()
    
    # 确保所有必要的配置项存在
    default_log_config = {
        'enabled': True,
        'level': 'INFO',
        'file': 'ftp_transfer.log'
    }
    
    # 合并默认配置
    for key, default_value in default_log_config.items():
        if key not in updated_config:
            updated_config[key] = default_value
    
    print(f"当前启用日志: {'是' if updated_config.get('enabled', True) else '否'}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['enabled'] = input("是否启用日志? (y/n): ").lower() != 'n'
    
    print(f"当前日志级别: {updated_config.get('level', 'INFO')}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['level'] = input("新日志级别 (DEBUG, INFO, WARNING, ERROR): ") or updated_config.get('level', 'INFO')
    
    print(f"当前日志文件: {updated_config.get('file', 'ftp_transfer.log')}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['file'] = input("新日志文件路径: ") or updated_config.get('file', 'ftp_transfer.log')
    
    return updated_config

def update_email_config(email_config: dict) -> dict:
    """
    更新邮件通知配置
    
    :param email_config: 现有邮件配置
    :return: 更新后的邮件配置
    """
    updated_config = email_config.copy()
    
    # 确保所有必要的配置项存在
    default_email_config = {
        'enabled': False,
        'smtp_server': '',
        'smtp_port': 587,
        'use_tls': True,
        'username': '',
        'password': '',
        'from_address': '',
        'to_address': '',
        'subject': 'FTP/SFTP传输任务完成通知'
    }
    
    # 合并默认配置
    for key, default_value in default_email_config.items():
        if key not in updated_config:
            updated_config[key] = default_value
    
    print(f"当前启用邮件通知: {'是' if updated_config.get('enabled', False) else '否'}")
    if input("是否修改? (y/n, 默认n): ").lower() == 'y':
        updated_config['enabled'] = input("是否启用邮件通知? (y/n): ").lower() == 'y'
        
        if updated_config['enabled']:
            print(f"当前SMTP服务器: {updated_config.get('smtp_server', '')}")
            updated_config['smtp_server'] = input("新SMTP服务器地址: ") or updated_config.get('smtp_server', '')
            
            print(f"当前SMTP端口: {updated_config.get('smtp_port', 587)}")
            new_port = input("新SMTP端口 (默认: 587): ")
            if new_port:
                updated_config['smtp_port'] = int(new_port)
            
            print(f"当前使用TLS: {'是' if updated_config.get('use_tls', True) else '否'}")
            if input("是否修改? (y/n, 默认n): ").lower() == 'y':
                updated_config['use_tls'] = input("是否使用TLS? (y/n): ").lower() != 'n'
            
            print(f"当前用户名: {updated_config.get('username', '')}")
            updated_config['username'] = input("新用户名: ") or updated_config.get('username', '')
            
            # 询问是否修改密码
            if input("是否修改密码? (y/n, 默认n): ").lower() == 'y':
                updated_config['password'] = input("新密码或授权码: ")
            
            print(f"当前发件人地址: {updated_config.get('from_address', '')}")
            updated_config['from_address'] = input("新发件人地址: ") or updated_config.get('from_address', '')
            
            print(f"当前收件人地址: {updated_config.get('to_address', '')}")
            updated_config['to_address'] = input("新收件人地址: ") or updated_config.get('to_address', '')
            
            print(f"当前邮件主题: {updated_config.get('subject', 'FTP/SFTP传输任务完成通知')}")
            updated_config['subject'] = input("新邮件主题: ") or updated_config.get('subject', 'FTP/SFTP传输任务完成通知')
    
    return updated_config

def create_config(config_file_path: str) -> None:
    """
    交互式创建配置文件
    
    :param config_file_path: 配置文件路径
    """
    try:
        print("欢迎创建FTP/SFTP传输工具配置文件")
        print("==================================")
        
        config = {}
        
        # 源服务器配置
        print("\n配置源服务器信息:")
        config['source'] = server_config()
        
        # 添加文件过滤规则配置
        print("\n配置文件过滤规则:")
        file_filter_config = {
            'type': input("文件过滤类型 (all/pattern/extension/creation_time/modification_time, 默认: all): ") or 'all'
        }
        
        if file_filter_config['type'] == 'pattern':
            file_filter_config['pattern'] = input("文件匹配模式 (如\"*.txt\"或\"report_2023*\"): ")
        elif file_filter_config['type'] == 'extension':
            extensions_input = input("文件后缀列表 (用逗号分隔，如\"txt,csv,xlsx\"): ")
            file_filter_config['extensions'] = [ext.strip() for ext in extensions_input.split(',')] if extensions_input else []
        elif file_filter_config['type'] in ['creation_time', 'modification_time']:
            file_filter_config['time_type'] = input("时间过滤类型 (since/before, 默认: since): ") or 'since'
            file_filter_config['time_value'] = input("时间值 (格式: YYYY-MM-DD或YYYY-MM-DD HH:MM:SS): ")
        config['source']['file_filter'] = file_filter_config
        
        # 目标服务器配置
        print("\n配置目标服务器信息:")
        config['destination'] = server_config(backup=False)
        
        # 日志配置
        print("\n配置日志设置:")
        log_config = {
            'enabled': input("是否启用日志? (y/n, 默认y): ").lower() != 'n',
            'level': None,
            'file': None,
        }
        if log_config['enabled']:
            log_config['level'] = input("日志级别 (DEBUG, INFO, WARNING, ERROR, 默认: INFO): ") or 'INFO'
            log_config['file'] = input("日志文件路径 (默认: ftp_transfer.log): ") or 'ftp_transfer.log'
        config['log'] = log_config
        
        # 邮件通知配置
        print("\n配置邮件通知:")
        email_config = {
            'enabled': input("是否启用邮件通知? (y/n, 默认n): ").lower() == 'y'
        }
        
        if email_config['enabled']:
            email_config['smtp_server'] = input("SMTP服务器地址: ")
            email_config['smtp_port'] = int(input("SMTP服务器端口 (默认: 587): ") or 587)
            email_config['use_tls'] = input("是否使用TLS? (y/n, 默认y): ").lower() != 'n'
            email_config['username'] = input("发件人邮箱: ")
            email_config['password'] = input("发件人密码或授权码: ")
            email_config['from_address'] = input("发件人地址 (默认与用户名相同): ") or email_config['username']
            email_config['to_address'] = input("收件人地址: ")
            email_config['subject'] = input("邮件主题 (默认: FTP/SFTP传输任务完成通知): ") or "FTP/SFTP传输任务完成通知"
        
        config['email'] = email_config
        
        # 确保配置文件目录存在
        os.makedirs(os.path.dirname(os.path.abspath(config_file_path)), exist_ok=True)
        
        # 写入配置文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
    except Exception as e:
        print(f"创建配置文件失败: {str(e)}")
        logger.error(f"创建配置文件失败: {str(e)}")


def interactive_update_config(config_file_path: str) -> None:
    """
    交互式更新配置文件
    
    :param config_file_path: 配置文件路径
    """
    try:
        # 加载现有配置
        config = load_config(config_file_path)
        
        print("欢迎更新FTP/SFTP传输工具配置文件")
        print("==================================")
        
        # 确保所有必要的配置节存在
        if 'source' not in config:
            print("配置文件中缺少源服务器配置，将创建默认配置")
            config['source'] = server_config()
        
        if 'destination' not in config:
            print("配置文件中缺少目标服务器配置，将创建默认配置")
            config['destination'] = server_config(backup=False)
        
        if 'log' not in config:
            print("配置文件中缺少日志配置，将创建默认配置")
            config['log'] = {
                'enabled': True,
                'level': 'INFO',
                'file': 'ftp_transfer.log'
            }
        
        if 'email' not in config:
            print("配置文件中缺少邮件通知配置，将创建默认配置")
            config['email'] = {
                'enabled': False
            }
        
        # 更新源服务器配置
        print("\n更新源服务器信息:")
        config['source'] = update_server_config(config['source'])
        
        # 更新文件过滤规则配置
        print("\n更新文件过滤规则:")
        # 确保file_filter配置存在
        if 'file_filter' not in config['source']:
            config['source']['file_filter'] = {'type': 'all'}
        
        config['source']['file_filter'] = update_file_filter_config(config['source']['file_filter'])
        
        # 更新目标服务器配置
        print("\n更新目标服务器信息:")
        # 确保file_exists_strategy配置存在
        if 'file_exists_strategy' not in config['destination']:
            config['destination']['file_exists_strategy'] = 'rename'
        
        # 显示并询问是否修改文件存在处理策略
        print(f"当前文件存在处理策略: {config['destination']['file_exists_strategy']}")
        if input("是否修改? (y/n, 默认n): ").lower() == 'y':
            config['destination']['file_exists_strategy'] = input("新处理策略 (skip/overwrite/rename): ") or 'rename'
        
        config['destination'] = update_server_config(config['destination'], backup=False)
        
        # 更新日志配置
        print("\n更新日志设置:")
        config['log'] = update_log_config(config['log'])
        
        # 更新邮件通知配置
        print("\n更新邮件通知设置:")
        config['email'] = update_email_config(config['email'])
        
        # 写入更新后的配置文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"\n配置文件已成功更新: {config_file_path}")
        
    except Exception as e:
        print(f"更新配置文件失败: {str(e)}")
        logger.error(f"更新配置文件失败: {str(e)}")
