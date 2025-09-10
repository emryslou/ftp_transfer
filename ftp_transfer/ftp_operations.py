import os
import ftplib
import traceback
import os
from typing import List, Dict, Optional, Union
import logging
import paramiko  # 新增：导入paramiko库以支持SFTP
import datetime  # 新增：导入datetime库以支持时间处理

logger = logging.getLogger(__name__)

def connect_ftp(
    host: str, 
    user: str, 
    password: str, 
    port: int = 21, 
    encoding: str = 'utf-8',
    use_ftps: bool = False,
    tls_implicit: bool = False,
    tls_verify: bool = True,
    use_passive: bool = True,
) -> Union[ftplib.FTP, ftplib.FTP_TLS]:
    """
    连接到FTP或FTPS服务器
    
    :param host: FTP/FTPS服务器主机名或IP地址
    :param user: 用户名
    :param password: 密码
    :param port: 端口号，默认为21
    :param encoding: 编码格式，默认为utf-8
    :param use_ftps: 是否使用FTPS加密连接，默认为False
    :param tls_implicit: 是否使用隐式TLS（通常使用端口990），默认为False
    :param tls_verify: 是否验证服务器证书，默认为True
    :return: FTP或FTP_TLS连接对象
    :raises: 连接失败时抛出异常
    """
    try:
        if use_ftps:
            # 使用FTPS连接
            logger.info(f"连接到FTPS服务器: {host}:{port}")
            if tls_implicit:
                # 隐式TLS连接
                ftp = ftplib.FTP_TLS()
                ftp.encoding = encoding
                ftp.connect(host, port, timeout=30)
                ftp.login(user, password)
                # 对于隐式TLS，通常不需要显式调用prot_p()
            else:
                # 显式TLS连接（默认）
                ftp = ftplib.FTP_TLS()
                ftp.encoding = encoding
                ftp.connect(host, port, timeout=30)
                ftp.login(user, password)
                # 切换到安全数据连接
                ftp.prot_p()
            logger.info(f"成功连接到FTPS服务器: {host}")
        else:
            # 使用普通FTP连接
            ftp = ftplib.FTP(encoding=encoding)
            logger.info(f"连接到FTP服务器: {host}:{port}")
            ftp.connect(host, port, timeout=30)
            logger.info(f"登录到FTP服务器: {user}")
            ftp.login(user, password)
            logger.info(f"成功连接到FTP服务器: {host}")
        
        # 设置被动模式
        ftp.set_pasv(use_passive)
        return ftp
    except Exception as e:
        conn_type = "FTPS" if use_ftps else "FTP"
        error_msg = f"连接{conn_type}服务器失败 {host}:{port}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        raise

def get_file_list(ftp: ftplib.FTP, directory: str) -> List[str]:
    """
    获取FTP目录中的文件列表
    
    :param ftp: FTP连接对象
    :param directory: 目录路径
    :return: 文件列表
    """
    file_list = []
    try:
        ftp.cwd(directory)
        logger.info(f"获取目录文件列表: {directory}")
        
        # 列出目录内容
        ftp.retrlines('NLST', lambda line: file_list.append(line))
        
        # 过滤出文件（排除目录）
        files_only = []
        for filename in file_list:
            logger.info(f"检查文件: {filename} at {directory}")
            if file_exists(ftp, directory, filename) and not is_directory(ftp, filename):
                files_only.append(filename)
        
        logger.info(f"在目录 {directory} 中找到 {len(files_only)} 个文件")
        return files_only
    except Exception as e:
        error_msg = f"获取文件列表失败: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        raise

def is_directory(ftp: ftplib.FTP, filename: str) -> bool:
    """
    检查是否为目录
    
    :param ftp: FTP连接对象
    :param filename: 文件名
    :return: 是否为目录
    """
    try:
        current_dir = ftp.pwd()
        ftp.cwd(filename)
        ftp.cwd(current_dir)
        return True
    except ftplib.error_perm:
        return False

def file_exists(ftp: ftplib.FTP, directory: str, filename: str) -> bool:
    """
    检查文件是否存在
    
    :param ftp: FTP连接对象
    :param directory: 目录路径
    :param filename: 文件名
    :return: 文件是否存在
    """
    try:
        original_dir = ftp.pwd()
        ftp.cwd(directory)
        
        # 尝试获取文件大小，文件不存在会抛出异常
        try:
            ftp.size(filename)
            exists = True
        except ftplib.error_perm:
            exists = False
        
        ftp.cwd(original_dir)
        return exists
    except Exception as e:
        logger.error(f"检查文件存在性时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def download_file(ftp: ftplib.FTP, filename: str, local_path: str) -> bool:
    """
    从FTP服务器下载文件
    
    :param ftp: FTP连接对象
    :param filename: 文件名
    :param local_path: 本地保存路径
    :return: 下载是否成功
    """
    try:
        logger.info(f"下载文件: {filename} -> {local_path}")
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        logger.info(f"文件下载成功: {filename}")
        return True
    except Exception as e:
        error_msg = f"下载文件失败 {filename}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        
        # 清理失败的下载文件
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e2:
                logger.warning(f"清理临时文件失败: {str(e2)}")
        
        return False

def upload_file(ftp: ftplib.FTP, local_path: str, remote_filename: str) -> bool:
    """
    上传文件到FTP服务器
    
    :param ftp: FTP连接对象
    :param local_path: 本地文件路径
    :param remote_filename: 远程文件名
    :return: 上传是否成功
    """
    try:
        logger.info(f"上传文件: {local_path} -> {remote_filename}")
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_filename}', f)
        logger.info(f"文件上传成功: {remote_filename}")
        return True
    except Exception as e:
        error_msg = f"上传文件失败 {remote_filename}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return False

def move_remote_file(ftp: ftplib.FTP, source_filename: str, dest_filename: str) -> bool:
    """
    在FTP服务器上移动或重命名文件
    
    :param ftp: FTP连接对象
    :param source_filename: 源文件名
    :param dest_filename: 目标文件名
    :return: 移动是否成功
    """
    try:
        logger.info(f"移动文件: {source_filename} -> {dest_filename}")
        ftp.rename(source_filename, dest_filename)
        logger.info(f"文件移动成功: {source_filename} -> {dest_filename}")
        return True
    except Exception as e:
        error_msg = f"移动文件失败 {source_filename} -> {dest_filename}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return False

def connect_sftp(
    host: str, 
    user: str, 
    password: str, 
    port: int = 22, 
    key_file: Optional[str] = None,
    passphrase: Optional[str] = None,
) -> paramiko.SFTPClient:
    """
    连接到SFTP服务器
    
    :param host: SFTP服务器主机名或IP地址
    :param user: 用户名
    :param password: 密码（如果使用密码认证）
    :param port: 端口号，默认为22
    :param key_file: SSH私钥文件路径（如果使用密钥认证）
    :param passphrase: 私钥密码（如果私钥有密码）
    :return: SFTP客户端对象
    :raises: 连接失败时抛出异常
    """
    try:
        logger.info(f"连接到SFTP服务器: {host}:{port}")
        # 创建SSH客户端
        ssh_client = paramiko.SSHClient()
        # 自动添加未知主机密钥
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接服务器
        if key_file:
            # 使用密钥认证
            logger.info(f"使用密钥文件 {key_file} 连接到SFTP服务器")
            key = paramiko.RSAKey.from_private_key_file(key_file, password=passphrase) if passphrase \
                else paramiko.RSAKey.from_private_key_file(key_file)
            ssh_client.connect(hostname=host, port=port, username=user, pkey=key)
        else:
            # 使用密码认证
            logger.info(f"使用密码连接到SFTP服务器")
            ssh_client.connect(hostname=host, port=port, username=user, password=password)
        
        # 创建SFTP客户端
        sftp_client = ssh_client.open_sftp()
        logger.info(f"成功连接到SFTP服务器: {host}")
        return sftp_client
    except Exception as e:
        error_msg = f"连接SFTP服务器失败 {host}:{port}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        raise

def get_sftp_file_list(sftp: paramiko.SFTPClient, directory: str) -> List[str]:
    """
    获取SFTP目录中的文件列表
    
    :param sftp: SFTP客户端对象
    :param directory: 目录路径
    :return: 文件列表
    """
    file_list = []
    try:
        logger.info(f"获取SFTP目录文件列表: {directory}")
        
        # 列出目录内容
        for item in sftp.listdir_attr(directory):
            # 只添加文件（排除目录）
            if not item.st_mode & 0o40000:  # 0o40000 表示目录
                file_list.append(item.filename)
                logger.info(f"找到文件: {item.filename}")
        
        logger.info(f"在SFTP目录 {directory} 中找到 {len(file_list)} 个文件")
        return file_list
    except Exception as e:
        error_msg = f"获取SFTP文件列表失败: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        raise

def sftp_file_exists(sftp: paramiko.SFTPClient, directory: str, filename: str) -> bool:
    """
    检查SFTP服务器上文件是否存在
    
    :param sftp: SFTP客户端对象
    :param directory: 目录路径
    :param filename: 文件名
    :return: 文件是否存在
    """
    try:
        file_path = os.path.join(directory, filename).replace('\\', '/')
        # 尝试获取文件属性，如果文件不存在会抛出异常
        sftp.stat(file_path)
        logger.info(f"SFTP文件存在: {file_path}")
        return True
    except FileNotFoundError:
        logger.info(f"SFTP文件不存在: {file_path}")
        return False
    except Exception as e:
        logger.error(f"检查SFTP文件存在性时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def sftp_download_file(sftp: paramiko.SFTPClient, filename: str, local_path: str, directory: str = ".") -> bool:
    """
    从SFTP服务器下载文件
    
    :param sftp: SFTP客户端对象
    :param filename: 文件名
    :param local_path: 本地保存路径
    :param directory: 远程目录路径，默认为当前目录
    :return: 下载是否成功
    """
    try:
        remote_path = os.path.join(directory, filename).replace('\\', '/')
        logger.info(f"从SFTP下载文件: {remote_path} -> {local_path}")
        sftp.get(remote_path, local_path)
        logger.info(f"SFTP文件下载成功: {remote_path}")
        return True
    except Exception as e:
        error_msg = f"下载SFTP文件失败 {remote_path}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        
        # 清理失败的下载文件
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e2:
                logger.warning(f"清理临时文件失败: {str(e2)}")
        
        return False

def sftp_upload_file(sftp: paramiko.SFTPClient, local_path: str, remote_filename: str, directory: str = ".") -> bool:
    """
    上传文件到SFTP服务器
    
    :param sftp: SFTP客户端对象
    :param local_path: 本地文件路径
    :param remote_filename: 远程文件名
    :param directory: 远程目录路径，默认为当前目录
    :return: 上传是否成功
    """
    try:
        remote_path = os.path.join(directory, remote_filename).replace('\\', '/')
        logger.info(f"上传文件到SFTP: {local_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
        logger.info(f"SFTP文件上传成功: {remote_path}")
        return True
    except Exception as e:
        error_msg = f"上传SFTP文件失败 {remote_path}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return False

def sftp_move_remote_file(sftp: paramiko.SFTPClient, source_filename: str, dest_filename: str, source_dir: str = ".", dest_dir: str = ".") -> bool:
    """
    在SFTP服务器上移动或重命名文件
    
    :param sftp: SFTP客户端对象
    :param source_filename: 源文件名
    :param dest_filename: 目标文件名
    :param source_dir: 源文件所在目录，默认为当前目录
    :param dest_dir: 目标文件所在目录，默认为当前目录
    :return: 移动是否成功
    """
    try:
        source_path = os.path.join(source_dir, source_filename).replace('\\', '/')
        dest_path = os.path.join(dest_dir, dest_filename).replace('\\', '/')
        logger.info(f"移动SFTP文件: {source_path} -> {dest_path}")
        sftp.rename(source_path, dest_path)
        logger.info(f"SFTP文件移动成功: {source_path} -> {dest_path}")
        return True
    except Exception as e:
        error_msg = f"移动SFTP文件失败 {source_path} -> {dest_path}: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return False

def close_sftp(sftp: paramiko.SFTPClient) -> None:
    """
    关闭SFTP连接
    
    :param sftp: SFTP客户端对象
    """
    try:
        # 获取SSH客户端并关闭
        ssh_client = sftp.get_channel().get_transport().get_ssh_client()
        sftp.close()
        ssh_client.close()
        logger.info("SFTP连接已关闭")
    except Exception as e:
        logger.warning(f"关闭SFTP连接时出错: {str(e)}")
        logger.debug(traceback.format_exc())


def get_file_modification_time(ftp: ftplib.FTP, directory: str, filename: str) -> Optional[datetime.datetime]:
    """
    获取FTP服务器上文件的修改时间
    
    :param ftp: FTP连接对象
    :param directory: 目录路径
    :param filename: 文件名
    :return: 文件的修改时间，如果失败则返回None
    """
    try:
        original_dir = ftp.pwd()
        ftp.cwd(directory)
        
        # 使用MDTM命令获取文件修改时间
        # 注意：MDTM命令可能不被所有FTP服务器支持
        try:
            mdtm_response = ftp.sendcmd(f'MDTM {filename}')
            # 响应格式通常是 "213 YYYYMMDDHHMMSS"
            if mdtm_response.startswith('213'):
                timestamp_str = mdtm_response[4:18]  # 提取时间戳部分
                # 解析时间戳，格式为：YYYYMMDDHHMMSS
                year = int(timestamp_str[0:4])
                month = int(timestamp_str[4:6])
                day = int(timestamp_str[6:8])
                hour = int(timestamp_str[8:10])
                minute = int(timestamp_str[10:12])
                second = int(timestamp_str[12:14])
                
                return datetime.datetime(year, month, day, hour, minute, second)
        except ftplib.error_perm:
            logger.warning(f"无法获取文件 {filename} 的修改时间，服务器不支持MDTM命令")
        
        ftp.cwd(original_dir)
        return None
    except Exception as e:
        logger.error(f"获取文件修改时间时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return None


def get_sftp_file_info(sftp: paramiko.SFTPClient, directory: str, filename: str) -> Optional[Dict]:
    """
    获取SFTP服务器上文件的信息，包括修改时间和创建时间
    
    :param sftp: SFTP客户端对象
    :param directory: 目录路径
    :param filename: 文件名
    :return: 包含文件信息的字典，如果失败则返回None
    """
    try:
        full_path = os.path.join(directory, filename)
        stat = sftp.stat(full_path)
        
        file_info = {
            'filename': filename,
            'size': stat.st_size,
            'modified_time': datetime.datetime.fromtimestamp(stat.st_mtime),
            'created_time': datetime.datetime.fromtimestamp(stat.st_ctime) if hasattr(stat, 'st_ctime') else None
        }
        
        return file_info
    except Exception as e:
        logger.error(f"获取SFTP文件信息时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return None