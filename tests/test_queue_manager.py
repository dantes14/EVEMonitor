#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
队列管理器测试
"""

import os
import sys
import time
import queue
import threading
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.queue_manager import QueueManager


@pytest.fixture
def queue_manager():
    """创建队列管理器实例"""
    manager = QueueManager()
    yield manager
    # 测试完成后停止队列管理器
    manager.stop()


def test_initialization(queue_manager):
    """测试初始化"""
    # 验证默认队列是否已创建
    assert queue_manager.get_queue("default") is not None
    assert queue_manager.get_queue("notification") is not None
    assert queue_manager.get_queue("screenshot") is not None
    assert queue_manager.get_queue("ocr") is not None
    assert queue_manager.get_queue("ocr_task") is not None
    assert queue_manager.get_queue("ocr_result") is not None
    assert queue_manager.get_queue("analysis_result") is not None


def test_create_queue(queue_manager):
    """测试创建队列"""
    # 创建新队列
    assert queue_manager.create_queue("test_queue", 50)
    
    # 验证队列已创建
    test_queue = queue_manager.get_queue("test_queue")
    assert test_queue is not None
    assert test_queue.maxsize == 50
    
    # 创建已存在的队列应返回False
    assert not queue_manager.create_queue("test_queue", 100)


def test_get_queue(queue_manager):
    """测试获取队列"""
    # 获取存在的队列
    default_queue = queue_manager.get_queue("default")
    assert default_queue is not None
    assert isinstance(default_queue, queue.Queue)
    
    # 获取不存在的队列
    assert queue_manager.get_queue("nonexistent") is None


def test_put_and_get(queue_manager):
    """测试放入和获取数据"""
    # 放入数据
    data = {"test": "data"}
    assert queue_manager.put(data, "default")
    
    # 获取数据
    success, result = queue_manager.get("default")
    assert success
    assert result == data
    
    # 队列为空时获取数据
    success, result = queue_manager.get("default", timeout=0.1)
    assert not success
    assert result is None


def test_get_queue_size(queue_manager):
    """测试获取队列大小"""
    # 空队列
    assert queue_manager.get_queue_size("default") == 0
    
    # 放入数据后
    queue_manager.put({"test": "data"}, "default")
    assert queue_manager.get_queue_size("default") == 1
    
    # 获取数据后
    queue_manager.get("default")
    assert queue_manager.get_queue_size("default") == 0
    
    # 不存在的队列
    assert queue_manager.get_queue_size("nonexistent") == -1


def test_register_callback(queue_manager):
    """测试注册回调函数"""
    # 定义回调函数
    callback_data = []
    
    def test_callback(data):
        callback_data.append(data)
    
    # 注册回调
    assert queue_manager.register_callback("default", test_callback)
    
    # 放入数据
    test_data = {"test": "callback"}
    queue_manager.put(test_data, "default")
    
    # 获取数据，这将触发回调
    queue_manager.get("default")
    
    # 验证回调被调用
    assert len(callback_data) == 1
    assert callback_data[0] == test_data


def test_start_listener(queue_manager):
    """测试启动监听器"""
    # 定义回调函数
    callback_data = []
    
    def test_callback(data):
        callback_data.append(data)
    
    # 启动监听器
    assert queue_manager.start_listener("default", test_callback)
    
    # 放入数据
    test_data = {"test": "listener"}
    queue_manager.put(test_data, "default")
    
    # 等待监听器处理数据
    time.sleep(0.1)
    
    # 验证回调被调用
    assert len(callback_data) == 1
    assert callback_data[0] == test_data


def test_stop(queue_manager):
    """测试停止队列管理器"""
    # 启动监听器
    def dummy_callback(data):
        pass
    
    queue_manager.start_listener("default", dummy_callback)
    
    # 停止队列管理器
    queue_manager.stop()
    
    # 验证停止标志
    assert not queue_manager._running 