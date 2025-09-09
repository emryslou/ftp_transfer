from setuptools import setup, find_packages
import os
import sys

def read_file(filename):
    """读取文件内容，支持在不同环境中查找文件"""
    # 尝试多种方式查找文件
    paths_to_try = [
        # 方式1: 从当前脚本所在目录查找
        os.path.join(os.path.dirname(__file__), filename),
        # 方式2: 从当前工作目录查找
        os.path.join(os.getcwd(), filename),
        # 方式3: 从上级目录查找
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename),
        # 方式4: 从Python安装目录查找
        os.path.join(os.path.dirname(sys.executable), filename),
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    # 如果所有方式都失败，返回空字符串并给出警告
    print(f"警告: 无法读取文件 {filename}，将使用空内容。")
    return ""

# 定义要包含的示例文件和目录结构
examples_data = []
if os.path.exists('examples'):
    for root, dirs, files in os.walk('examples'):
        for file in files:
            file_path = os.path.join(root, file)
            # 计算相对路径，用于保持目录结构
            relative_path = os.path.relpath(root, 'examples')
            # 如果是根目录，relative_path会是'.'，需要特殊处理
            if relative_path == '.':
                # 确保在Windows上也能正确处理路径
                if os.name == 'nt':  # Windows
                    # 在Windows上，我们使用更适合Windows的安装路径
                    target_dir = os.path.join('share', 'ftp_transfer', 'examples')
                else:  # Unix/Linux/macOS
                    target_dir = 'share/ftp_transfer/examples'
            else:
                # 使用os.path.join确保跨平台路径分隔符正确
                if os.name == 'nt':
                    target_dir = os.path.join('share', 'ftp_transfer', 'examples', relative_path)
                else:
                    target_dir = f'share/ftp_transfer/examples/{relative_path}'
            examples_data.append((target_dir, [file_path]))

setup(
    name="ftp_transfer",
    version="0.0.7",
    author="Emrys Liu",
    author_email="emrys.liu@foxmail.comn",
    description="一个用于在FTP服务器之间传输文件并提供通知功能的工具",
    long_description=read_file("readme.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/emryslou/ftp_transfer",  # 替换为实际仓库地址
    packages=find_packages(),
    include_package_data=True,
    # 明确指定包数据
    package_data={
        '': ['*.md', '*.txt'],  # 包含根目录下的所有md和txt文件
    },
    # 指定额外的数据文件
    data_files=[
        # 安装readme.md和changelog.md到文档目录
        # 确保在Windows上也能正确处理路径
        (os.path.join('share', 'doc', 'ftp_transfer') if os.name == 'nt' else 'share/doc/ftp_transfer', 
         ['readme.md', 'changelog.md'])
    ] + examples_data,
    install_requires=[
        "loguru>=0.7.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "ftp_transfer = ftp_transfer.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

