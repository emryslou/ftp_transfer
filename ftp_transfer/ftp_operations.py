import os
import ftplib
import traceback
from typing import List, Dict, Optional, Union
import logging

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