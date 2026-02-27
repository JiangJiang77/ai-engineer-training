"""日志工具

配置系统日志
"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str = "customer_service", level: int = None) -> logging.Logger:
    """配置日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
    
    Returns:
        配置好的日志器
    """
    # 如果没有指定level，从环境变量读取
    if level is None:
        import os
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level_str, logging.INFO)
    
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False  # 不传播到父logger
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 文件handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "customer_service.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # 文件记录更详细的日志
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 模块名称
    
    Returns:
        日志记录器
    """
    # 确保根logger已配置
    root_logger = logging.getLogger("customer_service")
    if not root_logger.handlers:
        setup_logger("customer_service")
    
    # 返回子logger
    return logging.getLogger(f"customer_service.{name}")


# 默认日志器
logger = setup_logger()


