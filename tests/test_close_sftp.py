import logging
import sys
import traceback
from unittest.mock import MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, '/opt/Dev/Code/Python/ftp_transfer')

# 导入修改过的close_sftp函数
from ftp_transfer.ftp_operations import close_sftp

# 配置日志级别以查看调试信息
logging.basicConfig(level=logging.DEBUG)

# 创建一个模拟的SFTP客户端对象来测试close_sftp函数
def test_close_sftp():
    print("测试close_sftp函数...")
    
    # 创建一个模拟的SFTP客户端对象
    mock_sftp = MagicMock()
    
    try:
        # 调用我们修改过的close_sftp函数
        close_sftp(mock_sftp)
        
        # 验证sftp.close()是否被调用
        mock_sftp.close.assert_called_once()
        print("测试成功: close_sftp函数正确调用了sftp.close()")
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_close_sftp()
    sys.exit(0 if success else 1)