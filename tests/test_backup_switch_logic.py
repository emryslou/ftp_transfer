import os
import sys
import yaml
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
from ftp_transfer.core import FTPTransfer

class TestBackupSwitchLogic(unittest.TestCase):
    def setUp(self):
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        
        # 创建一个基本的配置模板
        self.base_config = {
            'source': {
                'host': 'test_host',
                'port': 21,
                'user': 'test_user',
                'password': 'test_password',
                'directory': '/test/dir',
                'encoding': 'utf-8',
                'use_ftps': False,
                'tls_implicit': False,
                'use_passive': True,
            },
            'destination': {
                'host': 'dest_host',
                'port': 21,
                'user': 'dest_user',
                'password': 'dest_password',
                'directory': '/dest/dir',
                'encoding': 'utf-8',
                'use_ftps': False,
                'tls_implicit': False,
                'use_passive': True,
            },
            'log': {
                'file': 'test.log',
                'rotation': '1 week',
                'retention': '1 month',
                'level': 'INFO'
            },
            'email': {
                'enable': False
            }
        }
    
    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('ftp_transfer.core.connect_ftp')
    @patch('ftp_transfer.core.get_file_list')
    @patch('ftp_transfer.core.file_exists')
    @patch('ftp_transfer.core.download_file')
    @patch('ftp_transfer.core.upload_file')
    @patch('ftp_transfer.core.move_remote_file')
    @patch('ftp_transfer.core.send_email_notification')
    def test_backup_disabled_skipped(self, mock_email, mock_move, mock_upload, 
                                   mock_download, mock_exists, mock_file_list, 
                                   mock_connect):
        """测试当backup_enabled为False时，即使有backup_directory，也不会执行备份"""
        # 配置：备份开关关闭，但有备份目录
        config = self.base_config.copy()
        config['source']['backup_enabled'] = False
        config['source']['backup_directory'] = '/backup/dir'
        
        # 保存配置文件
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # 设置mock返回值
        mock_source_ftp = MagicMock()
        mock_dest_ftp = MagicMock()
        mock_connect.side_effect = [mock_source_ftp, mock_dest_ftp]
        mock_file_list.return_value = ['test_file.txt']
        mock_exists.return_value = False
        mock_download.return_value = True
        mock_upload.return_value = True
        
        # 创建FTPTransfer实例并执行传输
        ftp_transfer = FTPTransfer(self.config_path)
        ftp_transfer.transfer_files()
        
        # 验证move_remote_file没有被调用
        mock_move.assert_not_called()
        
        # 验证有一条日志记录表明备份功能被禁用
        self.assertIn(ftp_transfer.success_files[0], 'test_file.txt')
    
    @patch('ftp_transfer.core.connect_ftp')
    @patch('ftp_transfer.core.get_file_list')
    @patch('ftp_transfer.core.file_exists')
    @patch('ftp_transfer.core.download_file')
    @patch('ftp_transfer.core.upload_file')
    @patch('ftp_transfer.core.move_remote_file')
    @patch('ftp_transfer.core.send_email_notification')
    def test_backup_enabled_with_directory(self, mock_email, mock_move, mock_upload, 
                                         mock_download, mock_exists, mock_file_list, 
                                         mock_connect):
        """测试当backup_enabled为True并且有backup_directory时，会执行备份"""
        # 配置：备份开关打开，并且有备份目录
        config = self.base_config.copy()
        config['source']['backup_enabled'] = True
        config['source']['backup_directory'] = '/backup/dir'
        
        # 保存配置文件
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # 设置mock返回值
        mock_source_ftp = MagicMock()
        mock_dest_ftp = MagicMock()
        mock_connect.side_effect = [mock_source_ftp, mock_dest_ftp]
        mock_file_list.return_value = ['test_file.txt']
        mock_exists.return_value = False
        mock_download.return_value = True
        mock_upload.return_value = True
        mock_move.return_value = True
        
        # 创建FTPTransfer实例并执行传输
        ftp_transfer = FTPTransfer(self.config_path)
        ftp_transfer.transfer_files()
        
        # 验证move_remote_file被调用
        mock_move.assert_called_once()
        
        # 验证有一条日志记录表明备份功能被禁用
        self.assertIn(ftp_transfer.success_files[0], 'test_file.txt')
    
    @patch('ftp_transfer.core.connect_ftp')
    @patch('ftp_transfer.core.get_file_list')
    @patch('ftp_transfer.core.file_exists')
    @patch('ftp_transfer.core.download_file')
    @patch('ftp_transfer.core.upload_file')
    @patch('ftp_transfer.core.move_remote_file')
    @patch('ftp_transfer.core.send_email_notification')
    def test_backup_enabled_without_directory(self, mock_email, mock_move, mock_upload, 
                                            mock_download, mock_exists, mock_file_list, 
                                            mock_connect):
        """测试当backup_enabled为True但没有backup_directory时，不会执行备份"""
        # 配置：备份开关打开，但没有备份目录
        config = self.base_config.copy()
        config['source']['backup_enabled'] = True
        config['source']['backup_directory'] = ''
        
        # 保存配置文件
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # 设置mock返回值
        mock_source_ftp = MagicMock()
        mock_dest_ftp = MagicMock()
        mock_connect.side_effect = [mock_source_ftp, mock_dest_ftp]
        mock_file_list.return_value = ['test_file.txt']
        mock_exists.return_value = False
        mock_download.return_value = True
        mock_upload.return_value = True
        
        # 创建FTPTransfer实例并执行传输
        ftp_transfer = FTPTransfer(self.config_path)
        ftp_transfer.transfer_files()
        
        # 验证move_remote_file没有被调用
        mock_move.assert_not_called()
        
        # 验证有一条日志记录表明备份功能被禁用
        self.assertIn(ftp_transfer.success_files[0], 'test_file.txt')

def run_tests():
    print("开始测试源服务器文件备份开关在业务逻辑中的实现...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBackupSwitchLogic)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n测试结果摘要:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！源服务器文件备份开关功能在业务逻辑中已正确实现。")
        print("功能特点:")
        print("1. 当backup_enabled为False时，无论是否有backup_directory，都不会执行备份")
        print("2. 当backup_enabled为True但没有backup_directory时，不会执行备份")
        print("3. 当backup_enabled为True并且有backup_directory时，会执行备份")
    else:
        print("\n❌ 测试失败，请检查代码实现。")

if __name__ == "__main__":
    import sys
    run_tests()