import unittest
from unittest.mock import Mock, patch
from ftp_transfer.core import FTPTransfer

class TestFTPTransfer(unittest.TestCase):
    """FTP传输工具的单元测试"""
    
    @patch('ftp_transfer.core.load_config')
    @patch('ftp_transfer.core.setup_logger')
    def setUp(self, mock_setup_logger, mock_load_config):
        """测试前的准备工作"""
        # 模拟配置
        mock_config = {
            'source': {
                'host': 'test.source.com',
                'user': 'user',
                'password': 'pass',
                'directory': '/test/source'
            },
            'destination': {
                'host': 'test.dest.com',
                'user': 'user',
                'password': 'pass',
                'directory': '/test/dest'
            },
            'archive_directory': './archive',
            'log': {},
            'email': {
                'enable': False
            }
        }
        mock_load_config.return_value = mock_config
        
        self.ftp_transfer = FTPTransfer('test_config.yaml')
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.ftp_transfer.source_host, 'test.source.com')
        self.assertEqual(self.ftp_transfer.dest_host, 'test.dest.com')
        self.assertEqual(self.ftp_transfer.archive_dir, './archive')
    
    @patch('ftp_transfer.core.os.path.exists')
    @patch('ftp_transfer.core.os.makedirs')
    def test_ensure_directory_exists(self, mock_makedirs, mock_exists):
        """测试确保目录存在的方法"""
        # 测试目录不存在的情况
        mock_exists.return_value = False
        self.ftp_transfer._ensure_directory_exists('./test_dir')
        mock_makedirs.assert_called_once_with('./test_dir')
        
        # 测试目录已存在的情况
        mock_exists.return_value = True
        mock_makedirs.reset_mock()
        self.ftp_transfer._ensure_directory_exists('./test_dir')
        mock_makedirs.assert_not_called()

if __name__ == '__main__':
    unittest.main()
