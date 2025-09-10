import os
import sys
import traceback
import os
from datetime import datetime
import ftplib  # 新增：导入ftplib模块
import re  # 新增：导入re库以支持正则表达式匹配
from typing import List, Tuple, Dict, Optional, Any
from loguru import logger

from .config import load_config, create_config
from .config_utils import DEFAULT_CONFIG_PATH, _ensure_directory_exists, generate_trace_id, generate_archive_dir
from .notification import send_email_notification
from .logger import set_trace_id, setup_logger
from .ftp_operations import (
    connect_ftp,
    connect_sftp,
    get_file_list,
    get_sftp_file_list,
    download_file,
    sftp_download_file,
    upload_file,
    sftp_upload_file,
    move_remote_file,
    sftp_move_remote_file,
    file_exists,
    sftp_file_exists,
    close_sftp,
    get_file_modification_time,  # 新增：导入获取文件修改时间的函数
    get_sftp_file_info  # 新增：导入获取SFTP文件信息的函数
)
from . import __version__, __author__, __email__

class FTPTransfer:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        初始化FTP传输工具，从YAML配置文件加载配置
        
        :param config_path: 配置文件路径，默认为用户目录下的.ftp_transfer/ftp_config.yaml
        """
        # 生成trace_id，用于追踪本次运行
        self.trace_id = generate_trace_id()
        # 设置全局trace_id，使所有日志都包含这个ID
        set_trace_id(self.trace_id)
        
        # 检测配置文件是否存在，如果不存在则创建
        if not os.path.exists(config_path):
            # 先使用基本日志输出，因为日志系统尚未完全配置
            print(f"配置文件不存在: {config_path}，开始创建...")
            create_config(config_path)
            print("配置文件创建成功，程序将使用新创建的配置继续运行。")
        
        # 加载配置
        self.config = load_config(config_path)
        
        # 初始化日志（在设置trace_id和加载配置后进行）
        log_config = self.config.get('log', {})
        log_file = log_config.get('file', 'ftp_transfer.log')
        log_rotation = log_config.get('rotation', '1 week')
        log_retention = log_config.get('retention', '1 month')
        log_level = log_config.get('level', 'INFO')
        
        # 保存日志路径作为实例变量，用于后续展示
        self.log_file = log_file
        
        # 使用setup_logger函数配置日志
        setup_logger(log_file, log_rotation, log_retention, log_level)
        
        logger.info("开始FTP传输任务")
        logger.info(f"日志文件路径: {os.path.abspath(self.log_file)}")
        
        # 提取配置参数
        source_config = self.config.get('source', {})
        self.source_host = source_config.get('host', '')
        self.source_port = source_config.get('port', 21)  # 获取端口，默认21
        self.source_user = source_config.get('user', '')
        self.source_pass = source_config.get('password', '')
        self.source_dir = source_config.get('directory', '')
        self.source_backup_dir = source_config.get('backup_directory', '')
        self.source_enable_backup = source_config.get('enable_backup', True)  # 新增：备份功能开关，默认开启
        self.source_encoding = source_config.get('encoding', 'utf-8')
        # FTPS相关配置
        self.source_use_ftps = source_config.get('use_ftps', False)
        self.source_tls_implicit = source_config.get('tls_implicit', False)
        self.source_use_passive = source_config.get('use_passive', True)
        # SFTP相关配置
        self.source_use_sftp = source_config.get('use_sftp', False)
        self.source_key_file = source_config.get('key_file', None)
        self.source_passphrase = source_config.get('passphrase', None)
        # 文件过滤配置
        self.file_filter = source_config.get('file_filter', {})
        
        
        destination_config = self.config.get('destination', {})
        self.dest_host = destination_config.get('host', '')
        self.dest_port = destination_config.get('port', 21)  # 获取端口，默认21
        self.dest_user = destination_config.get('user', '')
        self.dest_pass = destination_config.get('password', '')
        self.dest_dir = destination_config.get('directory', '')
        self.dest_encoding = destination_config.get('encoding', 'utf-8')
        # FTPS相关配置
        self.dest_use_ftps = destination_config.get('use_ftps', False)
        self.dest_tls_implicit = destination_config.get('tls_implicit', False)
        self.dest_use_passive = destination_config.get('use_passive', True)
        # SFTP相关配置
        self.dest_use_sftp = destination_config.get('use_sftp', False)
        self.dest_key_file = destination_config.get('key_file', None)
        self.dest_passphrase = destination_config.get('passphrase', None)
        # 目标文件存在处理策略
        self.file_exists_strategy = destination_config.get('file_exists_strategy', 'rename')
        
        # 邮件配置
        self.email_config = self.config.get('email', {})
        self.email_enable = self.email_config.get('enable', False)
        self.failure_threshold = self.email_config.get('failure_threshold', 3)
        
        # 自动生成存档目录，无需配置
        self.archive_dir = generate_archive_dir()
        
        # 状态跟踪
        self.found_files = []
        self.success_files = []
        self.skipped_files = []
        self.failed_files = {}  # {文件名: 失败原因}
        self.errors = []
        
        # 确保存档目录存在
        _ensure_directory_exists(self.archive_dir)
        
        logger.info("FTP传输工具初始化完成")

    def _generate_timestamped_filename(self, filename: str) -> str:
        """生成带时间戳的文件名，格式为 旧文件名_年月日时分秒.后缀"""
        base_name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{base_name}_{timestamp}{ext}"

    def _filter_files(self, file_list: List[str], file_filter: Dict) -> List[str]:
        """
        根据文件过滤规则过滤文件列表
        
        :param file_list: 原始文件列表
        :param file_filter: 文件过滤规则配置
        :return: 过滤后的文件列表
        """
        if not file_filter or file_filter.get('type') == 'all':
            return file_list
        
        filtered_files = []
        filter_type = file_filter.get('type', 'all')
        
        # 连接到源服务器以获取文件时间信息（如果需要）
        source_conn = None
        need_file_info = filter_type in ['creation_time', 'modification_time']
        
        try:
            if need_file_info:
                if self.source_use_sftp:
                    # 使用SFTP连接
                    source_conn = connect_sftp(
                        self.source_host,
                        self.source_user,
                        self.source_pass,
                        self.source_port,
                        self.source_key_file,
                        self.source_passphrase
                    )
                else:
                    # 使用FTP连接
                    source_conn = connect_ftp(
                        self.source_host,
                        self.source_user,
                        self.source_pass,
                        self.source_port,
                        self.source_encoding,
                        use_ftps=self.source_use_ftps,
                        tls_implicit=self.source_tls_implicit,
                        use_passive=self.source_use_passive,
                    )
            
            for filename in file_list:
                if filter_type == 'pattern':
                    # 字符匹配文件名
                    pattern = file_filter.get('pattern', '')
                    # 将通配符转换为正则表达式
                    regex_pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
                    if re.search(regex_pattern, filename):
                        filtered_files.append(filename)
                elif filter_type == 'extension':
                    # 文件后缀匹配
                    extensions = file_filter.get('extensions', [])
                    file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
                    if any(ext.lower() == file_ext for ext in extensions):
                        filtered_files.append(filename)
                elif filter_type in ['creation_time', 'modification_time']:
                    # 时间过滤
                    try:
                        time_value_str = file_filter.get('time_value', '')
                        time_type = file_filter.get('time_type', 'since')
                        
                        # 解析时间值
                        if ' ' in time_value_str and ':' in time_value_str:
                            filter_time = datetime.strptime(time_value_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            filter_time = datetime.strptime(time_value_str, '%Y-%m-%d')
                        
                        # 获取文件时间
                        file_time = None
                        if self.source_use_sftp and source_conn:
                            file_info = get_sftp_file_info(source_conn, self.source_dir, filename)
                            if file_info:
                                if filter_type == 'modification_time':
                                    file_time = file_info['modified_time']
                                else:
                                    file_time = file_info['created_time']
                        elif not self.source_use_sftp and source_conn:
                            if filter_type == 'modification_time':
                                file_time = get_file_modification_time(source_conn, self.source_dir, filename)
                        
                        # 比较时间
                        if file_time:
                            if time_type == 'since' and file_time >= filter_time:
                                filtered_files.append(filename)
                            elif time_type == 'before' and file_time <= filter_time:
                                filtered_files.append(filename)
                    except Exception as e:
                        logger.warning(f"处理文件 {filename} 的时间信息时出错: {str(e)}")
            
            return filtered_files
        finally:
            # 关闭连接
            if need_file_info:
                if self.source_use_sftp and source_conn:
                    close_sftp(source_conn)
                elif not self.source_use_sftp and source_conn:
                    source_conn.quit()

    def _prepare_email_content(self) -> Tuple[str, str, bool]:
        """准备邮件主题和内容"""
        total_files = len(self.found_files)
        success_count = len(self.success_files)
        skipped_count = len(self.skipped_files)
        failed_count = len(self.failed_files)
        
        # 确定邮件主题前缀
        if self.errors:
            subject_prefix = "[错误]"
        elif failed_count >= self.failure_threshold:
            subject_prefix = "[警告] 失败文件过多"
        elif failed_count > 0:
            # 如果失败数量等于找到的数量，表示全部失败，不是部分成功
            if failed_count == total_files:
                subject_prefix = "[失败] 全部文件传输失败"
            else:
                subject_prefix = "[部分成功]"
        else:
            subject_prefix = ""
        
        # 构建邮件主题
        base_subject = self.email_config.get('subject', "FTP文件传输任务报告")
        subject = f"{subject_prefix} {base_subject}" if subject_prefix else base_subject
        
        # 构建HTML格式的邮件正文
        html_body_parts = []
        html_body_parts.append("<!DOCTYPE html>")
        html_body_parts.append("<html><head>")
        html_body_parts.append("<meta charset='UTF-8'>")
        html_body_parts.append("<style>")
        html_body_parts.append("table {border-collapse: collapse; width: 100%;}")
        html_body_parts.append("th, td {border: 1px solid #ddd; padding: 8px; text-align: left;}")
        html_body_parts.append("th {background-color: #f2f2f2;}")
        html_body_parts.append("tr:nth-child(even) {background-color: #f9f9f9;}")
        html_body_parts.append(".success {color: green;}")
        html_body_parts.append(".error {color: red;}")
        html_body_parts.append(".warning {color: orange;}")
        html_body_parts.append("</style>")
        html_body_parts.append("</head><body>")
        
        # 添加总体状态
        html_body_parts.append("<h2>FTP文件传输任务执行结果</h2>")
        html_body_parts.append("<table>")
        html_body_parts.append("<tr><th>项目</th><th>数量</th></tr>")
        html_body_parts.append(f"<tr><td>总文件数</td><td>{total_files}</td></tr>")
        html_body_parts.append(f"<tr><td>成功传输</td><td><span class='success'>{success_count}</span></td></tr>")
        html_body_parts.append(f"<tr><td>跳过文件</td><td>{skipped_count}</td></tr>")
        html_body_parts.append(f"<tr><td>失败文件</td><td><span class='error'>{failed_count}</span></td></tr>")
        html_body_parts.append("</table><br>")
        
        # 添加找到的文件列表表格
        html_body_parts.append("<h3>找到的文件列表</h3>")
        if self.found_files:
            html_body_parts.append("<table>")
            html_body_parts.append("<tr><th>文件名称</th></tr>")
            for file in self.found_files:
                html_body_parts.append(f"<tr><td>{file}</td></tr>")
            html_body_parts.append("</table>")
        else:
            html_body_parts.append("<p>无</p>")
        html_body_parts.append("<br>")
        
        # 添加重命名的文件表格
        if hasattr(self, 'renamed_files') and self.renamed_files:
            html_body_parts.append("<h3>重命名的文件 (目标已存在)</h3>")
            html_body_parts.append("<table>")
            html_body_parts.append("<tr><th>原文件名</th><th>实际上传文件名</th></tr>")
            for original_name, new_name in self.renamed_files.items():
                html_body_parts.append(f"<tr><td>{original_name}</td><td><span class='warning'>{new_name}</span></td></tr>")
            html_body_parts.append("</table>")
            html_body_parts.append("<br>")
        
        # 添加成功的文件表格
        if self.success_files:
            html_body_parts.append("<h3>成功传输的文件</h3>")
            html_body_parts.append("<table>")
            html_body_parts.append("<tr><th>文件名称</th></tr>")
            for file in self.success_files:
                html_body_parts.append(f"<tr><td><span class='success'>{file}</span></td></tr>")
            html_body_parts.append("</table>")
            html_body_parts.append("<br>")
        
        # 显示根据文件存在策略跳过的文件
        if self.skipped_files:
            html_body_parts.append("<h3>跳过的文件</h3>")
            html_body_parts.append("<table>")
            html_body_parts.append("<tr><th>文件名称</th></tr>")
            for file in self.skipped_files:
                html_body_parts.append(f"<tr><td>{file}</td></tr>")
            html_body_parts.append("</table>")
            html_body_parts.append("<br>")
        
        # 添加失败的文件及原因表格
        if self.failed_files:
            html_body_parts.append("<h3>失败的文件及原因</h3>")
            html_body_parts.append("<table>")
            html_body_parts.append("<tr><th>文件名称</th><th>失败原因</th></tr>")
            for file, reason in self.failed_files.items():
                html_body_parts.append(f"<tr><td><span class='error'>{file}</span></td><td>{reason}</td></tr>")
            html_body_parts.append("</table>")
            html_body_parts.append("<br>")
        
        # 添加错误信息
        if self.errors:
            html_body_parts.append("<h3>错误信息</h3>")
            html_body_parts.append("<ul>")
            for error in self.errors:
                html_body_parts.append(f"<li class='error'>{error}</li>")
            html_body_parts.append("</ul>")
            html_body_parts.append("<br>")
        
        html_body_parts.append("<p>详细日志请查看日志文件。</p>")
        html_body_parts.append("<hr>")
        html_body_parts.append(f"<p><strong>运行信息：</strong></p>")
        html_body_parts.append(f"<p>• 日志文件路径: {os.path.abspath(self.log_file)}</p>")
        html_body_parts.append(f"<p>• 运行追踪ID: {self.trace_id}</p>")
        html_body_parts.append("</body></html>")
        
        # 构建纯文本格式的邮件正文（用于不支持HTML的邮件客户端）
        plain_body_parts = []
        plain_body_parts.append("FTP文件传输任务执行结果如下：")
        plain_body_parts.append(f"总文件数: {total_files}")
        plain_body_parts.append(f"成功传输: {success_count}")
        plain_body_parts.append(f"跳过文件: {skipped_count}")
        plain_body_parts.append(f"失败文件: {failed_count}")
        plain_body_parts.append("")
        
        # 添加找到的文件列表
        plain_body_parts.append("找到的文件列表:")
        plain_body_parts.append("\n".join([f"- {f}" for f in self.found_files]) or "无")
        plain_body_parts.append("")
        
        # 添加重命名的文件
        if hasattr(self, 'renamed_files') and self.renamed_files:
            plain_body_parts.append("重命名的文件 (目标已存在):")
            for original_name, new_name in self.renamed_files.items():
                plain_body_parts.append(f"- {original_name} -> {new_name}")
            plain_body_parts.append("")
        
        # 添加成功的文件
        if self.success_files:
            plain_body_parts.append("成功传输的文件:")
            plain_body_parts.append("\n".join([f"- {f}" for f in self.success_files]))
            plain_body_parts.append("")
        
        # 显示根据文件存在策略跳过的文件
        if self.skipped_files:
            plain_body_parts.append("跳过的文件:")
            plain_body_parts.append("\n".join([f"- {f}" for f in self.skipped_files]))
            plain_body_parts.append("")
        
        # 添加失败的文件及原因
        if self.failed_files:
            plain_body_parts.append("失败的文件及原因:")
            for file, reason in self.failed_files.items():
                plain_body_parts.append(f"- {file}: {reason}")
            plain_body_parts.append("")
        
        # 添加错误信息
        if self.errors:
            plain_body_parts.append("错误信息:")
            plain_body_parts.append("\n".join([f"- {e}" for e in self.errors]))
            plain_body_parts.append("")
        plain_body_parts.append("详细日志请查看日志文件。")
        plain_body_parts.append("")
        plain_body_parts.append("运行信息：")
        plain_body_parts.append(f"• 日志文件路径: {os.path.abspath(self.log_file)}")
        plain_body_parts.append(f"• 运行追踪ID: {self.trace_id}")
        
        # 返回HTML正文和is_html=True，notification.py会处理纯文本部分
        return subject, "".join(html_body_parts), True

    def transfer_files(self) -> Tuple[int, int, int, int]:
        """
        执行文件传输流程
        
        :return: 一个元组 (找到的文件数, 成功传输的文件数, 跳过的文件数, 失败的文件数)
        """
        try:
            # 连接到源FTP/SFTP服务器
            source_conn = None
            try:
                if self.source_use_sftp:
                    # 使用SFTP连接
                    source_conn = connect_sftp(
                        self.source_host,
                        self.source_user,
                        self.source_pass,
                        self.source_port,
                        self.source_key_file,
                        self.source_passphrase
                    )
                else:
                    # 使用FTP连接
                    source_conn = connect_ftp(
                        self.source_host, 
                        self.source_user, 
                        self.source_pass,
                        self.source_port,
                        self.source_encoding,
                        use_ftps=self.source_use_ftps,
                        tls_implicit=self.source_tls_implicit,
                        use_passive=self.source_use_passive,
                    )
            except Exception as e:
                error_msg = f"连接源服务器失败: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                # 准备并发送邮件
                subject, body, is_html = self._prepare_email_content()
                send_email_notification(self.email_config, subject, body, is_html)
                return (0, 0, 0, 0)
            
            # 获取源目录文件列表
            if self.source_use_sftp:
                file_list = get_sftp_file_list(source_conn, self.source_dir)
            else:
                file_list = get_file_list(source_conn, self.source_dir)
            
            if len(file_list):
                # 应用文件过滤规则
                if hasattr(self, 'file_filter') and self.file_filter:
                    filtered_list = self._filter_files(file_list, self.file_filter)
                    logger.info(f"应用文件过滤规则后，文件数量从 {len(file_list)} 减少到 {len(filtered_list)}")
                    file_list = filtered_list
            
            total_files = len(file_list)
            
            if total_files == 0:
                logger.info("没有找到可传输的文件")
                if self.source_use_sftp:
                    close_sftp(source_conn)
                else:
                    source_conn.quit()
                # 准备并发送邮件
                subject, body, is_html = self._prepare_email_content()
                send_email_notification(self.email_config, subject, body, is_html)
                return (0, 0, 0, 0)
            
            # 连接到目标FTP/SFTP服务器
            dest_conn = None
            try:
                if self.dest_use_sftp:
                    # 使用SFTP连接
                    dest_conn = connect_sftp(
                        self.dest_host,
                        self.dest_user,
                        self.dest_pass,
                        self.dest_port,
                        self.dest_key_file,
                        self.dest_passphrase
                    )
                else:
                    # 使用FTP连接
                    dest_conn = connect_ftp(
                        self.dest_host, 
                        self.dest_user, 
                        self.dest_pass,
                        self.dest_port,
                        self.dest_encoding,
                        use_ftps=self.dest_use_ftps,
                        tls_implicit=self.dest_tls_implicit,
                        use_passive=self.dest_use_passive,
                    )
            except Exception as e:
                error_msg = f"连接目标服务器失败: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                if self.source_use_sftp:
                    close_sftp(source_conn)
                else:
                    source_conn.quit()
                # 准备并发送邮件
                subject, body, is_html = self._prepare_email_content()
                send_email_notification(self.email_config, subject, body, is_html)
                return (total_files, 0, 0, 0)
            
            # 逐个处理文件
            # 存储重命名的文件信息，用于在邮件中显示
            self.renamed_files = {}
            
            for filename in file_list:
                logger.info(f"处理文件: {filename}")
                
                # 检查目标服务器是否已存在该文件
                file_already_exists = False
                if self.dest_use_sftp:
                    file_already_exists = sftp_file_exists(dest_conn, self.dest_dir, filename)
                else:
                    file_already_exists = file_exists(dest_conn, self.dest_dir, filename)
                
                upload_filename = filename
                
                if file_already_exists:
                    strategy = self.file_exists_strategy.lower()
                    
                    if strategy == 'skip':
                        logger.info(f"目标服务器中已存在文件 {filename}，根据策略将跳过此文件")
                        self.skipped_files.append(filename)
                        continue
                    elif strategy == 'overwrite':
                        logger.warning(f"目标服务器中已存在文件 {filename}，根据策略将覆盖此文件")
                        # 仍然使用原始文件名，覆盖已有文件
                    elif strategy == 'rename':
                        # 生成带时间戳的新文件名
                        new_filename = self._generate_timestamped_filename(filename)
                        logger.warning(f"目标服务器中已存在文件 {filename}，根据策略将重命名为 {new_filename} 上传")
                        # 记录重命名的文件
                        self.renamed_files[filename] = new_filename
                        upload_filename = new_filename
                    else:
                        # 默认使用重命名策略
                        logger.warning(f"未知的文件存在策略 '{strategy}'，将默认使用重命名策略")
                        new_filename = self._generate_timestamped_filename(filename)
                        self.renamed_files[filename] = new_filename
                        upload_filename = new_filename
                
                # 创建临时本地文件路径
                local_temp_path = os.path.join(self.archive_dir, f"temp_{upload_filename}")
                
                # 从源服务器下载文件到本地临时位置
                download_success = False
                if self.source_use_sftp:
                    download_success = sftp_download_file(source_conn, filename, local_temp_path, self.source_dir)
                else:
                    # 确保在源目录
                    try:
                        source_conn.cwd(self.source_dir)
                    except ftplib.error_perm:
                        logger.error(f"无法切换到源目录: {self.source_dir}")
                        self.failed_files[filename] = f"无法切换到源目录: {self.source_dir}"
                        continue
                    
                    download_success = download_file(source_conn, filename, local_temp_path)
                
                if not download_success:
                    # 更详细的失败原因记录
                    error_details = f"下载失败: 系统找不到指定的文件 ({filename})"
                    self.failed_files[filename] = error_details
                    continue
                
                # 上传到目标服务器
                upload_success = False
                if self.dest_use_sftp:
                    upload_success = sftp_upload_file(dest_conn, local_temp_path, upload_filename, self.dest_dir)
                else:
                    dest_conn.cwd(self.dest_dir)  # 确保在目标目录
                    upload_success = upload_file(dest_conn, local_temp_path, upload_filename)
                
                if not upload_success:
                    os.remove(local_temp_path)  # 清理临时文件
                    self.failed_files[filename] = "上传失败"
                    continue
                
                # 移动源文件到备份目录（如果配置了备份目录且启用了备份功能）
                if self.source_enable_backup and self.source_backup_dir:
                    logger.info(f"将文件 {filename} 移动到源服务器备份目录 {self.source_backup_dir}")
                    move_success = False
                    if self.source_use_sftp:
                        move_success = sftp_move_remote_file(source_conn, filename, upload_filename, self.source_dir, self.source_backup_dir)
                    else:
                        move_success = move_remote_file(source_conn, filename, self.source_backup_dir + '/' + upload_filename)
                    
                    if move_success:
                        # 如果文件被重命名，记录实际上传的文件名
                        if filename in self.renamed_files:
                            self.success_files.append(f"{filename} -> {self.renamed_files[filename]}")
                        else:
                            self.success_files.append(filename)
                    else:
                        self.failed_files[filename] = "移动源文件到备份目录失败"
                else:
                    if self.source_enable_backup:
                        logger.info(f"未配置源服务器备份目录，跳过文件 {filename} 的备份")
                    else:
                        logger.info(f"源服务器备份功能已禁用，跳过文件 {filename} 的备份")
                    # 如果文件被重命名，记录实际上传的文件名
                    if filename in self.renamed_files:
                        self.success_files.append(f"{filename} -> {self.renamed_files[filename]}")
                    else:
                        self.success_files.append(filename)
                
                # 清理临时文件
                if os.path.exists(local_temp_path):
                    os.remove(local_temp_path)
            
            # 关闭连接
            if self.source_use_sftp:
                close_sftp(source_conn)
            else:
                source_conn.quit()
                
            if self.dest_use_sftp:
                close_sftp(dest_conn)
            else:
                dest_conn.quit()
            
            # 准备并发送邮件
            subject, body, is_html = self._prepare_email_content()
            send_email_notification(self.email_config, subject, body, is_html)
            
            return (total_files, len(self.success_files), len(self.skipped_files), len(self.failed_files))
        except Exception as e:
            logger.error(f"文件传输过程中发生错误: {str(e)}")
            logger.debug(traceback.format_exc())
            # 记录错误信息
            self.errors.append(f"文件传输过程中发生错误: {str(e)}")
            
            # 准备并发送邮件
            subject, body, is_html = self._prepare_email_content()
            send_email_notification(self.email_config, subject, body, is_html)
            
            return (0, 0, 0, 0)
