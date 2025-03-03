#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志工具模块

提供应用程序日志记录功能，支持控制台和文件输出，
以及不同级别的日志过滤。
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Union, Optional

from loguru import logger


def setup_logger(log_path: Union[str, Path], debug: bool = False) -> None:
    """设置日志记录器
    
    配置loguru日志记录器，添加控制台和文件处理器
    
    Args:
        log_path: 日志文件目录或文件路径
        debug: 是否启用调试模式，影响日志级别
    """
    # 移除默认处理器
    logger.remove()
    
    # 确保日志目录存在
    log_dir = Path(log_path)
    if log_dir.suffix:  # 如果是文件路径，获取其父目录
        log_dir = log_dir.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 确定日志文件路径
    if Path(log_path).suffix:
        log_file = Path(log_path)
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = Path(log_path) / f"evemonitor_{today}.log"
    
    # 日志格式
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # 确定日志级别
    console_level = "DEBUG" if debug else "INFO"
    file_level = "DEBUG" if debug else "INFO"
    
    # 添加控制台处理器
    logger.add(
        sys.stderr, 
        format=log_format, 
        level=console_level, 
        colorize=True
    )
    
    # 添加文件处理器
    logger.add(
        log_file,
        format=log_format,
        level=file_level,
        rotation="10 MB",  # 当日志达到10MB时轮换
        retention="30 days",  # 保留30天的日志
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    if debug:
        logger.info("调试模式已启用")


def get_log_files(log_dir: Union[str, Path], days: int = 7) -> list:
    """获取最近的日志文件列表
    
    Args:
        log_dir: 日志目录路径
        days: 获取最近几天的日志，默认7天
        
    Returns:
        日志文件路径列表，按时间降序排序
    """
    log_dir = Path(log_dir)
    if not log_dir.exists() or not log_dir.is_dir():
        return []
    
    log_files = []
    for f in log_dir.glob("evemonitor_*.log*"):
        if f.is_file():
            log_files.append(f)
    
    # 按修改时间排序，最新的在前
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 只返回最近N天的日志
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_timestamp = cutoff_time.timestamp()
    
    recent_logs = [f for f in log_files if os.path.getmtime(f) >= cutoff_timestamp]
    
    return recent_logs 