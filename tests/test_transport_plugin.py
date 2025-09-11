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

# 导入传输协议插件
from ftp_transfer.transport.factory import TransportFactory
from ftp_transfer.transport.base import BaseTransport
from ftp_transfer.transport.ftp import FTPTransport
from ftp_transfer.transport.sftp import SFTPTransport

class TestTransportPlugin(unittest.TestCase):
    
    def setUp(self):
        # 准备测试配置
        self.ftp_config = {
            'type': 'ftp',
            'host': 'test.ftp.server',
            'user': 'test_user',
            'password': 'test_pass',
            'port': 21,
            'encoding': 'utf-8',
            'use_ftps': False,
            'tls_implicit': False,
            'use_passive': True
        }
        
        self.sftp_config = {
            'type': 'sftp',
            'host': 'test.sftp.server',
            'user': 'test_user',
            'password': 'test_pass',
            'port': 22,
            'key_file': None,
            'passphrase': None
        }
        
    @patch('ftp_transfer.transport.ftp.ftplib.FTP')
    def test_create_ftp_transport(self, mock_ftp):
        """测试创建FTP传输实例"""
        # 创建FTP传输实例
        transport = TransportFactory.create_transport(self.ftp_config)
        
        # 验证是否创建了正确类型的实例
        self.assertIsInstance(transport, FTPTransport)
        self.assertIsInstance(transport, BaseTransport)
        
        # 验证配置是否正确设置
        self.assertEqual(transport.host, self.ftp_config['host'])
        self.assertEqual(transport.port, self.ftp_config['port'])
    
    @patch('ftp_transfer.transport.sftp.paramiko.Transport')
    def test_create_sftp_transport(self, mock_transport):
        """测试创建SFTP传输实例"""
        # 创建SFTP传输实例
        transport = TransportFactory.create_transport(self.sftp_config)
        
        # 验证是否创建了正确类型的实例
        self.assertIsInstance(transport, SFTPTransport)
        self.assertIsInstance(transport, BaseTransport)
        
        # 验证配置是否正确设置
        self.assertEqual(transport.host, self.sftp_config['host'])
        self.assertEqual(transport.port, self.sftp_config['port'])
    
    @patch('ftp_transfer.transport.ftp.ftplib.FTP')
    def test_ftp_connect_and_disconnect(self, mock_ftp):
        """测试FTP连接和断开"""
        # 模拟FTP连接
        mock_ftp_instance = mock_ftp.return_value
        mock_ftp_instance.login.return_value = '230 Login successful'
        mock_ftp_instance.cwd.return_value = '250 Directory successfully changed.'
        
        # 创建并连接FTP传输实例
        transport = TransportFactory.create_transport(self.ftp_config)
        connect_result = TransportFactory.connect_transport(transport)
        
        # 验证连接是否成功
        self.assertTrue(connect_result)
        mock_ftp_instance.login.assert_called_once_with(
            self.ftp_config['user'], self.ftp_config['password']
        )
        
        # 断开连接
        TransportFactory.disconnect_transport(transport)
        mock_ftp_instance.quit.assert_called_once()
    
    @patch('ftp_transfer.transport.sftp.paramiko.SSHClient')
    def test_sftp_connect_and_disconnect(self, mock_ssh_client):
        """测试SFTP连接和断开"""
        # 模拟SFTP连接
        mock_ssh_instance = mock_ssh_client.return_value
        mock_sftp = MagicMock()
        mock_ssh_instance.open_sftp.return_value = mock_sftp
        
        # 创建并连接SFTP传输实例
        transport = TransportFactory.create_transport(self.sftp_config)
        connect_result = TransportFactory.connect_transport(transport)
        
        # 验证连接是否成功
        self.assertTrue(connect_result)
        mock_ssh_instance.connect.assert_called_once_with(
            hostname=self.sftp_config['host'],
            port=self.sftp_config['port'],
            username=self.sftp_config['user'],
            password=self.sftp_config['password']
        )
        
        # 断开连接
        TransportFactory.disconnect_transport(transport)
        mock_sftp.close.assert_called_once()
        mock_ssh_instance.close.assert_called_once()
    
    @patch('ftp_transfer.transport.ftp.ftplib.FTP')
    def test_ftp_file_operations(self, mock_ftp):
        """测试FTP文件操作"""
        # 模拟FTP连接和文件操作
        mock_ftp_instance = mock_ftp.return_value
        mock_ftp_instance.login.return_value = '230 Login successful'
        mock_ftp_instance.cwd.return_value = '250 Directory successfully changed.'
        mock_ftp_instance.size.return_value = 1024
        
        # 模拟retrlines方法
        def mock_retrlines(cmd, callback):
            if cmd.startswith('NLST'):
                for file in ['file1.txt', 'file2.txt', 'subdir']:
                    callback(file)
            return '226 Transfer complete'
        mock_ftp_instance.retrlines.side_effect = mock_retrlines
        
        # 创建并连接FTP传输实例
        transport = TransportFactory.create_transport(self.ftp_config)
        TransportFactory.connect_transport(transport)
        
        # 模拟_is_directory方法，使subdir被识别为目录，file1.txt和file2.txt被识别为文件
        original_is_directory = transport._is_directory
        transport._is_directory = lambda filename: filename == 'subdir'
        
        # 测试获取文件列表 - 只返回文件，不返回目录
        file_list = transport.get_file_list('/test/dir')
        self.assertEqual(file_list, ['file1.txt', 'file2.txt'])
        # 检查是否调用了cwd，但不验证具体参数，因为实际实现可能使用pwd()
        mock_ftp_instance.cwd.assert_called()
        mock_ftp_instance.retrlines.assert_called_once_with('NLST', unittest.mock.ANY)
        
        # 恢复原始方法
        transport._is_directory = original_is_directory
        
        # 测试文件是否存在 - file_exists方法需要两个参数：directory和filename
        mock_ftp_instance.size.return_value = 1024
        exists = transport.file_exists('/test/dir', 'file1.txt')
        self.assertTrue(exists)
        mock_ftp_instance.size.assert_called_with('file1.txt')
    
    @patch('ftp_transfer.transport.sftp.paramiko.SSHClient')
    def test_sftp_file_operations(self, mock_ssh_client):
        """测试SFTP文件操作"""
        # 模拟SFTP连接和文件操作
        mock_ssh_instance = mock_ssh_client.return_value
        mock_sftp = MagicMock()
        mock_ssh_instance.open_sftp.return_value = mock_sftp
        # 33188 表示普通文件，16877 表示目录
        mock_sftp.listdir_attr.return_value = [
            MagicMock(filename='file1.txt', st_mode=33188, st_size=1024),
            MagicMock(filename='file2.txt', st_mode=33188, st_size=2048),
            MagicMock(filename='subdir', st_mode=16877, st_size=0)
        ]
        
        # 创建并连接SFTP传输实例
        transport = TransportFactory.create_transport(self.sftp_config)
        TransportFactory.connect_transport(transport)
        
        # 测试获取文件列表 - 只返回文件，不返回目录
        file_list = transport.get_file_list('/test/dir')
        self.assertEqual(file_list, ['file1.txt', 'file2.txt'])
        mock_sftp.listdir_attr.assert_called_with('/test/dir')
        
        # 测试文件是否存在
        mock_sftp.stat.return_value = MagicMock()
        exists = transport.file_exists('/test/dir', 'file1.txt')
        self.assertTrue(exists)
        mock_sftp.stat.assert_called_with('/test/dir/file1.txt')

if __name__ == '__main__':
    unittest.main()