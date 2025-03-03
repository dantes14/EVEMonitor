#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志工具测试
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger_utils import setup_logger, get_log_files
from loguru import logger


@pytest.fixture
def temp_log_dir():
    """创建临时日志目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        yield log_dir


def test_setup_logger_with_directory(temp_log_dir):
    """测试使用目录设置日志记录器"""
    # 设置日志记录器
    setup_logger(temp_log_dir, debug=True)
    
    # 写入一条日志
    logger.debug("测试日志记录")
    
    # 检查日志文件是否创建
    log_files = list(temp_log_dir.glob("*.log"))
    assert len(log_files) == 1
    
    # 检查日志内容
    with open(log_files[0], "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "测试日志记录" in log_content


def test_setup_logger_with_file(temp_log_dir):
    """测试使用文件路径设置日志记录器"""
    # 创建特定的日志文件路径
    log_file = temp_log_dir / "specific_log.log"
    
    # 设置日志记录器
    setup_logger(log_file, debug=False)
    
    # 写入一条日志
    logger.info("测试特定文件日志记录")
    
    # 检查日志文件是否存在
    assert log_file.exists()
    
    # 检查日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "测试特定文件日志记录" in log_content


def test_get_log_files(temp_log_dir):
    """测试获取日志文件列表"""
    # 创建一些测试日志文件
    log_files = [
        temp_log_dir / "test_log_1.log",
        temp_log_dir / "test_log_2.log",
        temp_log_dir / "test_log_3.log",
    ]
    
    # 创建文件
    for log_file in log_files:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("测试日志内容")
    
    # 获取最近的日志文件
    recent_logs = get_log_files(temp_log_dir, days=7)
    
    # 验证返回的日志文件数量
    assert len(recent_logs) == 3
    
    # 验证所有文件都在返回结果中
    for log_file in log_files:
        assert str(log_file) in [str(path) for path in recent_logs]


def test_get_log_files_with_invalid_dir():
    """测试获取不存在目录中的日志文件"""
    # 使用不存在的目录
    non_existent_dir = Path("/non_existent_dir")
    
    # 获取日志文件
    logs = get_log_files(non_existent_dir)
    
    # 验证返回空列表
    assert len(logs) == 0


def test_log_levels(temp_log_dir):
    """测试不同日志级别"""
    # 设置日志记录器（非调试模式）
    log_file = temp_log_dir / "log_levels.log"
    setup_logger(log_file, debug=False)
    
    # 写入不同级别的日志
    logger.debug("调试日志")
    logger.info("信息日志")
    logger.warning("警告日志")
    logger.error("错误日志")
    
    # 检查日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        # 在非调试模式下，debug日志不应该被记录
        assert "调试日志" not in log_content
        assert "信息日志" in log_content
        assert "警告日志" in log_content
        assert "错误日志" in log_content
    
    # 设置为调试模式
    setup_logger(log_file, debug=True)
    
    # 重新写入日志
    logger.debug("调试日志2")
    
    # 验证调试日志被记录
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "调试日志2" in log_content 