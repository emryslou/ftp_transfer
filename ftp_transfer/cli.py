import argparse
import os
import sys
import json
from typing import Dict, Any
import logging
from . import __version__, __author__, __email__
from .config import update_config, interactive_update_config, create_config
from .config_utils import DEFAULT_CONFIG_PATH
from .core import FTPTransfer
from .logger import setup_logger
from .utils import find_from_examples, find_from_package

# 设置日志
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="FTP文件传输工具")
    
    # 全局参数
    parser.add_argument('-c', '--config', type=str, default=DEFAULT_CONFIG_PATH,
                      help=f'配置文件路径，默认为{DEFAULT_CONFIG_PATH}')
    parser.add_argument('--version', '-v', action='store_true',
                      help='显示版本信息')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 传输文件命令（默认）
    transfer_parser = subparsers.add_parser('transfer', help='传输文件')
    transfer_parser.add_argument('-c', '--config', type=str, default=DEFAULT_CONFIG_PATH,
                                help=f'配置文件路径，默认为{DEFAULT_CONFIG_PATH}')
    
    # 版本信息命令
    # version_parser = subparsers.add_parser('version', help='显示版本信息及更新内容')
    
    # 更新配置命令
    update_parser = subparsers.add_parser('update-config', help='更新配置文件')
    update_parser.add_argument('config_path', type=str, nargs='?', default=DEFAULT_CONFIG_PATH,
                              help=f'配置文件路径，默认为{DEFAULT_CONFIG_PATH}')
    update_parser.add_argument('config_items', nargs='*',
                              help='配置项和值，格式为 key=value，支持嵌套键使用点表示法，如：source.port=2121 email.enable=false')
    
    # 交互式更新配置命令
    interactive_update_parser = subparsers.add_parser('interactive-update-config', help='使用交互式向导修改现有配置文件')
    interactive_update_parser.add_argument('config_path', type=str, nargs='?', default=DEFAULT_CONFIG_PATH,
                                         help=f'配置文件路径，默认为{DEFAULT_CONFIG_PATH}')
    
    # 创建配置命令
    create_parser = subparsers.add_parser('create-config', help='创建新的配置文件')
    create_parser.add_argument('config_path', type=str, nargs='?', default=DEFAULT_CONFIG_PATH,
                              help=f'配置文件路径，默认为{DEFAULT_CONFIG_PATH}')
    
    # 配置文件示例命令
    # config_example_parser = subparsers.add_parser('config-example', help='显示配置文件示例')
    
    return parser.parse_args()


def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """将嵌套字典展平，使用点表示法连接键"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def handle_version() -> None:
    """处理版本信息显示"""
    print(f"FTP文件传输工具 v{__version__}")
    print(f"作者: {__author__}")
    print(f"邮箱: {__email__}")
    sys.exit(0)


def handle_version_command() -> None:
    """处理version子命令"""
    print(f"FTP文件传输工具 v{__version__}")
    print(f"作者: {__author__}")
    print(f"邮箱: {__email__}")
    print("\n版本更新内容:")
    with open(find_from_package('changelog.md'), 'r', encoding='utf-8') as f:
        for line in f:
            print(line, end='')
        print()
    sys.exit(0)


def handle_update_config(args: argparse.Namespace) -> None:
    """处理更新配置命令"""
    try:
        # 创建要更新的配置字典
        updates = {}
        
        for item in args.config_items:
            if '=' not in item:
                print(f"错误: 配置项格式不正确: {item}，应为 key=value 格式")
                sys.exit(1)
            
            key, value = item.split('=', 1)
            keys = key.split('.')
            
            # 创建嵌套字典
            current = updates
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 尝试解析值的类型
            try:
                # 尝试解析为JSON
                parsed_value = json.loads(value.lower())
            except json.JSONDecodeError:
                # 如果不是有效的JSON，保持为字符串
                parsed_value = value
            
            current[keys[-1]] = parsed_value
        
        if not updates:
            print("错误: 未指定要更新的配置项")
            print("使用示例: python -m ftp_transfer update-config source.port=2121 email.enable=false")
            print("如果需要交互式修改配置，请使用: python -m ftp_transfer interactive-update-config")
            sys.exit(1)
        
        # 更新配置
        update_config(args.config_path, updates)
        print(f"配置文件已成功更新: {args.config_path}")
        print(f"更新的配置项:")
        for key_path, value in _flatten_dict(updates).items():
            print(f"  {key_path} = {value}")
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        print(f"错误: 更新配置失败: {str(e)}")
        sys.exit(1)


def handle_interactive_update_config(args: argparse.Namespace) -> None:
    """处理交互式更新配置命令"""
    try:
        interactive_update_config(args.config_path)
    except Exception as e:
        logger.error(f"交互式更新配置失败: {str(e)}")
        print(f"错误: 交互式更新配置失败: {str(e)}")
        sys.exit(1)


def handle_create_config(args: argparse.Namespace) -> None:
    """处理创建配置命令"""
    try:
        create_config(args.config_path)
        print(f"配置文件已成功创建: {args.config_path}")
    except Exception as e:
        logger.error(f"创建配置失败: {str(e)}")
        print(f"错误: 创建配置失败: {str(e)}")
        sys.exit(1)


def handle_transfer(args: argparse.Namespace) -> None:
    """处理文件传输命令"""
    try:
        # 如果命令是transfer，使用args.config，否则使用args.config_path
        config_path = args.config if hasattr(args, 'config') and args.config else DEFAULT_CONFIG_PATH
        ftp_transfer = FTPTransfer(config_path)
        total, success, skipped, failed = ftp_transfer.transfer_files()
        
        logger.info(
            f"传输结果: 找到 {total} 个，成功 {success} 个，"\
            f"跳过 {skipped} 个，失败 {failed} 个"
        )
        print(f"\n传输结果摘要:")
        print(f"- 总文件数: {total}")
        print(f"- 成功传输: {success}")
        print(f"- 传输失败: {failed}")
        print(f"- 跳过传输: {skipped}")
        print(f"- 临时存档目录: {ftp_transfer.archive_dir}")
        print(f"- 日志文件路径: {os.path.abspath(ftp_transfer.log_file)}")
        print(f"- 运行追踪ID: {ftp_transfer.trace_id}")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        print(f"错误: 程序执行失败: {str(e)}")
        sys.exit(1)



def handle_config_example():
    """处理配置文件示例"""
    print("配置文件示例:")
    print("=" * 60)
    
    try:
        # 尝试读取示例文件
        example_content = read_example_file('ftp_config.yaml.example')
        print(example_content)
        print("=" * 60)
        print("提示：可以使用 'ftp_transfer create-config [路径]' 命令创建新的配置文件。")
        
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        print("=" * 60)
        print("请确保包已正确安装，或尝试通过 pip 重新安装。")

def main() -> None:
    """主函数入口"""
    args = parse_args()
    
    # 处理版本参数和命令
    if args.version:
        handle_version()
    
    if args.command == 'version':
        handle_version_command()
    
    setup_logger()
    # 处理不同的命令
    if args.command == 'update-config':
        handle_update_config(args)
    elif args.command == 'interactive-update-config':
        handle_interactive_update_config(args)
    elif args.command == 'create-config':
        handle_create_config(args)
    elif args.command == 'config-example':
        handle_config_example()
    else:
        # 默认处理传输文件命令
        handle_transfer(args)


if __name__ == "__main__":
    main()