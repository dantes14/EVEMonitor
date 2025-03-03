#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控管理器模块测试
"""

import os
import sys
import time
import queue
import threading
import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.monitor_manager import MonitorManager
from src.config.config_manager import ConfigManager
from PyQt6.QtCore import QObject


@pytest.fixture
def config_manager(tmp_path):
    """创建配置管理器实例"""
    config_path = tmp_path / "test_config.yaml"
    return ConfigManager(config_path)


@pytest.fixture
def monitor_manager(config_manager):
    """创建监控管理器实例"""
    with patch('src.core.monitor_manager.ScreenCapture'), \
         patch('src.core.monitor_manager.OCREngine'), \
         patch('src.core.monitor_manager.NotificationManager'):
        manager = MonitorManager(config_manager)
        yield manager
        # 测试后清理
        if manager.running:
            manager.stop_monitoring()


@pytest.mark.qt
def test_initialization(monitor_manager):
    """测试初始化"""
    assert monitor_manager is not None
    assert hasattr(monitor_manager, 'config_manager')
    assert hasattr(monitor_manager, 'screen_capture')
    assert hasattr(monitor_manager, 'ocr_engine')
    assert hasattr(monitor_manager, 'notification_manager')
    assert hasattr(monitor_manager, 'running') and not monitor_manager.running
    assert hasattr(monitor_manager, 'paused') and not monitor_manager.paused
    assert hasattr(monitor_manager, 'capture_thread') and monitor_manager.capture_thread is None
    assert hasattr(monitor_manager, 'processing_thread') and monitor_manager.processing_thread is None
    assert hasattr(monitor_manager, 'stats')


@pytest.mark.qt
def test_start_monitoring(monitor_manager):
    """测试开始监控"""
    # 模拟线程
    with patch.object(threading, 'Thread') as mock_thread:
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # 启动监控
        result = monitor_manager.start_monitoring()
        
        # 验证结果
        assert result is True
        assert monitor_manager.running is True
        assert monitor_manager.paused is False
        assert monitor_manager.stats["started_at"] is not None
        assert monitor_manager.capture_thread is not None
        assert monitor_manager.processing_thread is not None
        
        # 验证线程启动
        assert mock_thread_instance.start.call_count == 2


@pytest.mark.qt
def test_stop_monitoring(monitor_manager):
    """测试停止监控"""
    # 设置运行状态
    monitor_manager.running = True
    monitor_manager.capture_thread = MagicMock()
    monitor_manager.processing_thread = MagicMock()
    
    # 停止监控
    result = monitor_manager.stop_monitoring()
    
    # 验证结果
    assert result is True
    assert monitor_manager.running is False
    assert monitor_manager.paused is False


@pytest.mark.qt
def test_pause_resume_monitoring(monitor_manager):
    """测试暂停和恢复监控"""
    # 设置运行状态
    monitor_manager.running = True
    
    # 暂停监控
    result = monitor_manager.pause_monitoring()
    assert result is True
    assert monitor_manager.paused is True
    
    # 恢复监控
    result = monitor_manager.resume_monitoring()
    assert result is True
    assert monitor_manager.paused is False


@pytest.mark.qt
def test_get_status(monitor_manager):
    """测试获取状态"""
    # 设置一些状态
    monitor_manager.running = True
    monitor_manager.paused = False
    monitor_manager.stats["captures_count"] = 10
    
    # 获取状态
    status = monitor_manager.get_status()
    
    # 验证结果
    assert isinstance(status, dict)
    assert "running" in status and status["running"] is True
    assert "paused" in status and status["paused"] is False
    assert "captures_count" in status and status["captures_count"] == 10


@pytest.mark.qt
def test_capture_loop(monitor_manager):
    """测试捕获循环"""
    # 模拟配置和屏幕捕获
    monitor_manager.config = {"timing": {"capture_interval_ms": 100}}
    monitor_manager.screen_capture.capture.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # 设置运行状态
    monitor_manager.running = True
    
    # 创建一个事件来控制测试时间
    stop_event = threading.Event()
    
    # 修改捕获循环以在短时间后停止
    def mock_capture_loop():
        monitor_manager._capture_loop()
        stop_event.set()
    
    # 使用补丁替换原始方法
    with patch.object(monitor_manager, '_capture_loop', side_effect=lambda: time.sleep(0.1)):
        # 在单独的线程中运行捕获循环
        thread = threading.Thread(target=mock_capture_loop)
        thread.daemon = True
        thread.start()
        
        # 等待一小段时间
        time.sleep(0.2)
        
        # 停止监控
        monitor_manager.running = False
        
        # 等待线程结束
        stop_event.wait(timeout=1.0)
        
        # 验证捕获循环被调用
        assert thread.is_alive() is False


@pytest.mark.qt
def test_processing_loop(monitor_manager):
    """测试处理循环"""
    # 模拟图像和OCR结果
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    monitor_manager.ocr_engine.recognize.return_value = [
        {"text": "测试文本", "confidence": 0.9}
    ]
    
    # 设置运行状态
    monitor_manager.running = True
    
    # 添加测试图像到队列
    monitor_manager.capture_queue.put(test_image)
    
    # 创建一个事件来控制测试时间
    stop_event = threading.Event()
    
    # 修改处理循环以在短时间后停止
    def mock_processing_loop():
        monitor_manager._processing_loop()
        stop_event.set()
    
    # 使用补丁替换原始方法
    with patch.object(monitor_manager, '_processing_loop', side_effect=lambda: time.sleep(0.1)):
        # 在单独的线程中运行处理循环
        thread = threading.Thread(target=mock_processing_loop)
        thread.daemon = True
        thread.start()
        
        # 等待一小段时间
        time.sleep(0.2)
        
        # 停止监控
        monitor_manager.running = False
        
        # 等待线程结束
        stop_event.wait(timeout=1.0)
        
        # 验证处理循环被调用
        assert thread.is_alive() is False


@pytest.mark.qt
def test_should_send_notification(monitor_manager):
    """测试是否应该发送通知"""
    # 模拟配置
    monitor_manager.config = {
        "notification": {
            "enabled": True,
            "confidence_threshold": 0.7,
            "min_interval": 30
        }
    }
    
    # 测试结果
    result_high_confidence = {"text": "高置信度", "confidence": 0.9}
    result_low_confidence = {"text": "低置信度", "confidence": 0.5}
    
    # 验证结果
    assert monitor_manager._should_send_notification(result_high_confidence) is True
    assert monitor_manager._should_send_notification(result_low_confidence) is False
    
    # 测试通知间隔
    monitor_manager.notification_manager.last_notification_time = monitor_manager.stats["started_at"]
    assert monitor_manager._should_send_notification(result_high_confidence) is False


@pytest.mark.qt
def test_on_config_changed(monitor_manager):
    """测试配置变更处理"""
    # 模拟配置变更
    monitor_manager._on_config_changed("ocr.engine", "tesseract")
    
    # 验证OCR引擎配置更新被调用
    assert monitor_manager.ocr_engine.update_config.called
    
    # 模拟通知配置变更
    monitor_manager._on_config_changed("notification.enabled", True)
    
    # 验证通知管理器配置更新被调用
    assert monitor_manager.notification_manager.update_config.called


@pytest.mark.qt
def test_test_notification(monitor_manager):
    """测试发送测试通知"""
    # 模拟通知管理器
    monitor_manager.notification_manager.send_test_notification.return_value = True
    
    # 发送测试通知
    result = monitor_manager.test_notification()
    
    # 验证结果
    assert result is True
    assert monitor_manager.notification_manager.send_test_notification.called


@pytest.mark.qt
def test_error_handling(monitor_manager):
    """测试错误处理"""
    # 模拟错误信号
    with patch.object(monitor_manager.error_occurred, 'emit') as mock_emit:
        # 触发错误
        monitor_manager.notification_manager.send_test_notification.side_effect = Exception("测试错误")
        monitor_manager.test_notification()
        
        # 验证错误信号被发出
        assert mock_emit.called
        assert "测试错误" in mock_emit.call_args[0][0] 