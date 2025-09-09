from typing import Optional
from loguru import logger

# 全局trace_id变量
_current_trace_id = ""

def set_trace_id(trace_id: str) -> None:
    """
    设置当前的trace_id
    
    :param trace_id: 要设置的trace_id
    """
    global _current_trace_id
    _current_trace_id = trace_id

def get_trace_id() -> str:
    """
    获取当前的trace_id
    
    :return: 当前的trace_id
    """
    return _current_trace_id

# 自定义格式化器，在日志中包含trace_id
def _custom_formatter(record):
    trace_id = _current_trace_id if _current_trace_id else "-"
    record["extra"]["trace_id"] = trace_id
    return "[{time:YYYY-MM-DD HH:mm:ss.SSS}][{extra[trace_id]}]| {level: <8} | {name}:{function}:{line} - {message}\n"

def setup_logger(
    log_file: str = "ftp_transfer.log",
    rotation: str = "1 week",
    retention: str = "1 month",
    level: str = "INFO",
    console_output: bool = True
) -> None:
    """
    配置日志系统
    
    :param log_file: 日志文件路径
    :param rotation: 日志轮转策略
    :param retention: 日志保留时间
    :param level: 日志级别
    :param console_output: 是否在控制台输出日志
    """
    # 移除默认配置
    logger.remove()
    
    # 确保全局trace_id不为空
    global _current_trace_id
    if not _current_trace_id:
        _current_trace_id = "unknown"
    
    # 添加文件输出，确保使用自定义格式化器
    logger.add(
        log_file,
        rotation=rotation,
        retention=retention,
        level=level,
        encoding='utf-8',
        format=_custom_formatter
    )
    
    # 添加控制台输出（如果启用），确保使用自定义格式化器
    if console_output:
        logger.add(
            sink=print,
            level=level,
            format=_custom_formatter
        )
    
    logger.info("日志系统初始化完成")
