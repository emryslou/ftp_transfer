import os
import yaml
import getpass
import traceback
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

def interactive_update_config(config_path: str) -> None:
    """交互式修改现有配置文件，使用现有配置值作为默认值
    
    Args:
        config_path: 配置文件路径
    """
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            print(f"错误: 配置文件不存在: {config_path}")
            print("请先使用 create-config 命令创建配置文件")
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        print(f"开始交互式更新配置文件: {config_path}")
        print("注意: 直接按回车将保留当前配置值")
        print("\n========== 配置更新向导 ==========")
        
        # 加载现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # 确保配置结构完整
        if 'source' not in config:
            config['source'] = {}
        if 'destination' not in config:
            config['destination'] = {}
        if 'log' not in config:
            config['log'] = {}
        if 'email' not in config:
            config['email'] = {'enable': False}
        
        # 更新源FTP配置
        print("\n------ 源FTP服务器配置 ------")
        config['source'].update({
            'host': input(f"请输入源FTP服务器地址 (当前: {config['source'].get('host', '')}): ") or config['source'].get('host', ''),
            'port': int(input(f"请输入源FTP端口 (当前: {config['source'].get('port', 21)}): ") or str(config['source'].get('port', 21))),
            'user': input(f"请输入源FTP用户名 (当前: {config['source'].get('user', '')}): ") or config['source'].get('user', ''),
        })
        
        # 询问是否要修改密码
        if input("是否修改源FTP密码? (y/n, 默认n): ").lower() == 'y':
            config['source']['password'] = getpass.getpass("请输入源FTP密码: ")
        elif 'password' not in config['source']:
            # 如果是新配置，要求输入密码
            config['source']['password'] = getpass.getpass("请输入源FTP密码: ")
        
        config['source'].update({
            'directory': input(f"请输入源FTP目录路径 (当前: {config['source'].get('directory', '')}): ") or config['source'].get('directory', ''),
            'backup_directory': input(f"请输入源FTP备份目录路径 (当前: {config['source'].get('backup_directory', '')}): ") or config['source'].get('backup_directory', ''),
            'encoding': input(f"请输入源FTP编码 (当前: {config['source'].get('encoding', 'utf-8')}): ") or config['source'].get('encoding', 'utf-8'),
            'use_ftps': input(f"是否使用FTPS加密连接? (y/n, 当前: {'y' if config['source'].get('use_ftps', False) else 'n'}): ").lower() == 'y' if input(f"是否使用FTPS加密连接? (y/n, 当前: {'y' if config['source'].get('use_ftps', False) else 'n'}): ") else config['source'].get('use_ftps', False)
        })
        
        # 更新目标FTP配置
        print("\n------ 目标FTP服务器配置 ------")
        config['destination'].update({
            'host': input(f"请输入目标FTP服务器地址 (当前: {config['destination'].get('host', '')}): ") or config['destination'].get('host', ''),
            'port': int(input(f"请输入目标FTP端口 (当前: {config['destination'].get('port', 21)}): ") or str(config['destination'].get('port', 21))),
            'user': input(f"请输入目标FTP用户名 (当前: {config['destination'].get('user', '')}): ") or config['destination'].get('user', ''),
        })
        
        # 询问是否要修改密码
        if input("是否修改目标FTP密码? (y/n, 默认n): ").lower() == 'y':
            config['destination']['password'] = getpass.getpass("请输入目标FTP密码: ")
        elif 'password' not in config['destination']:
            # 如果是新配置，要求输入密码
            config['destination']['password'] = getpass.getpass("请输入目标FTP密码: ")
        
        config['destination'].update({
            'directory': input(f"请输入目标FTP目录路径 (当前: {config['destination'].get('directory', '')}): ") or config['destination'].get('directory', ''),
            'encoding': input(f"请输入目标FTP编码 (当前: {config['destination'].get('encoding', 'utf-8')}): ") or config['destination'].get('encoding', 'utf-8'),
            'use_ftps': input(f"是否使用FTPS加密连接? (y/n, 当前: {'y' if config['destination'].get('use_ftps', False) else 'n'}): ").lower() == 'y' if input(f"是否使用FTPS加密连接? (y/n, 当前: {'y' if config['destination'].get('use_ftps', False) else 'n'}): ") else config['destination'].get('use_ftps', False)
        })
        
        # 更新日志配置
        print("\n------ 日志配置 ------")
        config['log'].update({
            'file': input(f"请输入日志文件路径 (当前: {config['log'].get('file', 'ftp_transfer.log')}): ") or config['log'].get('file', 'ftp_transfer.log'),
            'rotation': input(f"请输入日志轮转策略 (当前: {config['log'].get('rotation', '1 week')}): ") or config['log'].get('rotation', '1 week'),
            'retention': input(f"请输入日志保留时间 (当前: {config['log'].get('retention', '1 month')}): ") or config['log'].get('retention', '1 month'),
            'level': input(f"请输入日志级别 (当前: {config['log'].get('level', 'INFO')}): ") or config['log'].get('level', 'INFO')
        })
        
        # 更新邮件配置
        print("\n------ 邮件通知配置 ------")
        current_enable = config['email'].get('enable', False)
        new_enable = input(f"是否启用邮件通知? (y/n, 当前: {'y' if current_enable else 'n'}): ").lower()
        if new_enable in ('y', 'n'):
            config['email']['enable'] = (new_enable == 'y')
        else:
            config['email']['enable'] = current_enable
        
        # 如果启用邮件通知，继续更新邮件配置
        if config['email']['enable']:
            config['email'].update({
                'subject': input(f"请输入邮件主题 (当前: {config['email'].get('subject', 'FTP文件传输任务报告')}): ") or config['email'].get('subject', 'FTP文件传输任务报告'),
                'sender': input(f"请输入发送者邮箱 (当前: {config['email'].get('sender', '')}): ") or config['email'].get('sender', ''),
                'recipients': input(f"请输入接收者邮箱 (当前: {', '.join(config['email'].get('recipients', []))}): ").split(',') if input(f"请输入接收者邮箱 (当前: {', '.join(config['email'].get('recipients', []))}): ") else config['email'].get('recipients', []),
                'smtp_server': input(f"请输入SMTP服务器地址 (当前: {config['email'].get('smtp_server', '')}): ") or config['email'].get('smtp_server', ''),
                'smtp_port': int(input(f"请输入SMTP服务器端口 (当前: {config['email'].get('smtp_port', 465)}): ") or str(config['email'].get('smtp_port', 465))),
                'smtp_username': input(f"请输入SMTP用户名 (当前: {config['email'].get('smtp_username', '')}): ") or config['email'].get('smtp_username', ''),
            })
            
            # 询问是否要修改SMTP密码
            if input("是否修改SMTP密码/授权码? (y/n, 默认n): ").lower() == 'y':
                config['email']['smtp_password'] = getpass.getpass("请输入SMTP密码或授权码: ")
            elif 'smtp_password' not in config['email']:
                # 如果是新配置，要求输入密码
                config['email']['smtp_password'] = getpass.getpass("请输入SMTP密码或授权码: ")
            
            config['email'].update({
                'failure_threshold': int(input(f"请输入失败文件数量阈值 (当前: {config['email'].get('failure_threshold', 3)}): ") or str(config['email'].get('failure_threshold', 3)))
            })
        
        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"配置文件已成功更新: {config_path}")
        print("\n========== 配置更新完成 ==========")
        print(f"配置文件已成功更新: {config_path}")
        
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        logger.debug(traceback.format_exc())
        print(f"错误: 更新配置文件失败: {str(e)}")
        raise

def create_config(config_path: str) -> None:
    """
    创建配置文件，引导用户填写必要的配置信息
    
    :param config_path: 配置文件保存路径
    """
    print("首次运行，需要创建配置文件...")
    
    # 创建配置目录（如果不存在）
    config_dir = os.path.dirname(config_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir)
        logger.info(f"创建配置目录: {config_dir}")
    
    # 引导用户填写配置信息
    config = {
        'source': {
            'host': input("请输入源FTP服务器地址: "),
            'port': int(input("请输入源FTP端口 (默认为21，隐式FTPS通常使用990): ") or "21"),
            'user': input("请输入源FTP用户名: "),
            'password': getpass.getpass("请输入源FTP密码: "),
            'directory': input("请输入源FTP目录路径: "),
            'backup_directory': input("请输入源FTP备份目录路径 (用于文件处理后备份): "),
            'encoding': input("请输入源FTP编码 (默认为'utf-8', windows系统请输入'gbk'): ") or "utf-8",
            'use_ftps': input("是否使用FTPS加密连接? (y/n, 默认n): ").lower() == 'y',
            'tls_implicit': False,  # 默认使用显式TLS
            'use_passive': True,
        },
        'destination': {
            'host': input("请输入目标FTP服务器地址: "),
            'port': int(input("请输入目标FTP端口 (默认为21，隐式FTPS通常使用990): ") or "21"),
            'user': input("请输入目标FTP用户名: "),
            'password': getpass.getpass("请输入目标FTP密码: "),
            'directory': input("请输入目标FTP目录路径: "),
            'encoding': input("请输入目标FTP编码 (默认为'utf-8', windows系统请输入'gbk'): ") or "utf-8",
            'use_ftps': input("是否使用FTPS加密连接? (y/n, 默认n): ").lower() == 'y',
            'tls_implicit': False,  # 默认使用显式TLS
            'use_passive': True,
        },
        'log': {
            'file': input("请输入日志文件路径 (默认为'ftp_transfer.log'): ") or "ftp_transfer.log",
            'rotation': input("请输入日志轮转策略 (默认为'1 week'): ") or "1 week",
            'retention': input("请输入日志保留时间 (默认为'1 month'): ") or "1 month",
            'level': input("请输入日志级别 (默认为'INFO'): ") or "INFO"
        },
        'email': {
            'enable': input("是否启用邮件通知? (y/n, 默认n): ").lower() == 'y',
        }
    }
    
    # 如果启用邮件通知，继续填写邮件配置
    if config['email']['enable']:
        config['email'].update({
            'subject': input("请输入邮件主题 (默认为'FTP文件传输任务报告'): ") or "FTP文件传输任务报告",
            'sender': input("请输入发送者邮箱: "),
            'recipients': input("请输入接收者邮箱 (多个邮箱用逗号分隔): ").split(','),
            'smtp_server': input("请输入SMTP服务器地址: "),
            'smtp_port': int(input("请输入SMTP服务器端口 (默认为465): ") or "465"),
            'smtp_username': input("请输入SMTP用户名: "),
            'smtp_password': getpass.getpass("请输入SMTP密码或授权码: "),
            'failure_threshold': int(input("请输入失败文件数量阈值 (默认为3): ") or "3")
        })
    
    # 如果启用了FTPS，询问是否使用隐式TLS
    if config['source']['use_ftps']:
        config['source']['tls_implicit'] = input("是否使用隐式TLS? (y/n, 默认n，隐式TLS通常使用端口990): ").lower() == 'y'
    
    if config['destination']['use_ftps']:
        config['destination']['tls_implicit'] = input("是否使用隐式TLS? (y/n, 默认n，隐式TLS通常使用端口990): ").lower() == 'y'
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
    logger.info(f"配置文件已创建: {config_path}")
    print(f"配置文件已创建成功: {config_path}")
