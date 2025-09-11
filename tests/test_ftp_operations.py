#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import ftplib

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from ftp_transfer.ftp_operations import (
    connect_ftp,
    get_file_list,
    file_exists,
    is_directory,
    download_file,
    upload_file,
    get_file_modification_time,
    get_file_creation_time
)

class TestFTPOperations(unittest.TestCase):
    
    def setUp(self):
        # 准备测试配置
        self.ftp_config = {
            'host': 'test.ftp.server',
            'user': 'test_user',
            'password': 'test_pass',
            'port': 21,
            'encoding': 'utf-8',
            'use_ftps': False,
            'tls_implicit': False,
            'use_passive': True
        }
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    def test_get_file_modification_time_success(self, mock_ftp_class):
        """测试成功获取文件修改时间"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.return_value = '/current/dir'
        mock_ftp.cwd.return_value = None
        mock_ftp.sendcmd.return_value = '213 20230101120000'
        
        # 调用函数
        result = get_file_modification_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 12)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)
        
        # 验证方法调用
        mock_ftp.pwd.assert_called_once()
        mock_ftp.cwd.assert_any_call('/test/dir')
        mock_ftp.sendcmd.assert_called_with('MDTM test.txt')
        mock_ftp.cwd.assert_any_call('/current/dir')
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    def test_get_file_modification_time_unsupported(self, mock_ftp_class):
        """测试服务器不支持MDTM命令的情况"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.return_value = '/current/dir'
        mock_ftp.cwd.return_value = None
        mock_ftp.sendcmd.side_effect = ftplib.error_perm('500 Command not implemented')
        
        # 调用函数
        result = get_file_modification_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNone(result)
        
        # 验证方法调用
        mock_ftp.cwd.assert_any_call('/test/dir')
        mock_ftp.sendcmd.assert_called_with('MDTM test.txt')
        mock_ftp.cwd.assert_any_call('/current/dir')
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    @patch('ftp_transfer.ftp_operations.get_file_modification_time')
    def test_get_file_creation_time_with_mlst(self, mock_get_mod_time, mock_ftp_class):
        """测试使用MLST命令成功获取文件创建时间"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.return_value = '/current/dir'
        mock_ftp.cwd.return_value = None
        mlst_response = "250-Start of list for test.txt\n" \
                        " create=20230101100000;modify=20230102120000;size=1024;UNIX.mode=0644;UNIX.uid=1000;UNIX.gid=1000; type=file; test.txt\n" \
                        "250 End of list"
        mock_ftp.sendcmd.return_value = mlst_response
        
        # 调用函数
        result = get_file_creation_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)
        
        # 验证方法调用
        mock_ftp.pwd.assert_called_once()
        mock_ftp.cwd.assert_any_call('/test/dir')
        mock_ftp.sendcmd.assert_called_with('MLST test.txt')
        mock_ftp.cwd.assert_any_call('/current/dir')
        # 因为MLST成功，不应该调用get_file_modification_time
        mock_get_mod_time.assert_not_called()
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    @patch('ftp_transfer.ftp_operations.get_file_modification_time')
    def test_get_file_creation_time_with_stat(self, mock_get_mod_time, mock_ftp_class):
        """测试使用STAT命令成功获取文件创建时间"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.return_value = '/current/dir'
        mock_ftp.cwd.return_value = None
        # 第一次调用sendcmd抛出异常（MLST不支持），第二次没有调用
        mock_ftp.sendcmd.side_effect = ftplib.error_perm('500 Command not implemented')
        
        # 设置STAT命令的响应
        def mock_retrlines(cmd, callback):
            if cmd.startswith('STAT'):
                callback('Size: 1024       Created: 01-Jan-2023 10:00:00')
        mock_ftp.retrlines.side_effect = mock_retrlines
        
        # 调用函数
        result = get_file_creation_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)
        
        # 验证方法调用
        mock_ftp.cwd.assert_any_call('/test/dir')
        mock_ftp.sendcmd.assert_called_with('MLST test.txt')
        mock_ftp.retrlines.assert_called_with('STAT test.txt', unittest.mock.ANY)
        mock_ftp.cwd.assert_any_call('/current/dir')
        # 因为STAT成功，不应该调用get_file_modification_time
        mock_get_mod_time.assert_not_called()
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    @patch('ftp_transfer.ftp_operations.get_file_modification_time')
    def test_get_file_creation_time_fallback_to_modification(self, mock_get_mod_time, mock_ftp_class):
        """测试获取文件创建时间失败时回退到修改时间"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.return_value = '/current/dir'
        mock_ftp.cwd.return_value = None
        # MLST和STAT都不支持
        mock_ftp.sendcmd.side_effect = ftplib.error_perm('500 Command not implemented')
        mock_ftp.retrlines.side_effect = ftplib.error_perm('500 Command not implemented')
        
        # 设置修改时间的返回值
        expected_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_get_mod_time.return_value = expected_time
        
        # 调用函数
        result = get_file_creation_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_time)
        
        # 验证方法调用
        mock_ftp.cwd.assert_any_call('/test/dir')
        mock_ftp.sendcmd.assert_called_with('MLST test.txt')
        mock_ftp.retrlines.assert_called_with('STAT test.txt', unittest.mock.ANY)
        mock_get_mod_time.assert_called_with(mock_ftp, '.', 'test.txt')
        mock_ftp.cwd.assert_any_call('/current/dir')
    
    @patch('ftp_transfer.ftp_operations.ftplib.FTP')
    def test_get_file_creation_time_exception(self, mock_ftp_class):
        """测试获取文件创建时间时发生异常"""
        # 设置模拟对象
        mock_ftp = mock_ftp_class.return_value
        mock_ftp.pwd.side_effect = Exception('Connection error')
        
        # 调用函数
        result = get_file_creation_time(mock_ftp, '/test/dir', 'test.txt')
        
        # 验证结果
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()