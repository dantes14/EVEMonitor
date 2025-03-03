#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕捕获模块测试
"""

import os
import sys
import time
import threading
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.screen_capture import ScreenCapture
from src.config.config_manager import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    """创建配置管理器实例"""
    config_path = tmp_path / "test_config.yaml"
    return ConfigManager(config_path)


@pytest.fixture
def screen_capture(config_manager):
    """创建屏幕捕获实例"""
    capture = ScreenCapture(config_manager)
    yield capture
    # 测试后清理
    capture.stop_capture()


@pytest.mark.qt
def test_initialization(screen_capture):
    """测试初始化"""
    assert screen_capture is not None
    assert hasattr(screen_capture, '_running') and not screen_capture._running
    assert hasattr(screen_capture, '_capture_thread') and screen_capture._capture_thread is None
    assert hasattr(screen_capture, '_fps') and screen_capture._fps == 0


@pytest.mark.qt
def test_get_fps(screen_capture):
    """测试获取FPS"""
    # 初始FPS应为0
    assert screen_capture.get_fps() == 0
    
    # 手动设置FPS
    screen_capture._fps = 30
    assert screen_capture.get_fps() == 30


@pytest.mark.qt
def test_start_and_stop_capture(screen_capture):
    """测试启动和停止捕获"""
    # 模拟配置
    emulator_configs = [
        {"title": "测试模拟器", "id": "test1", "x": 0, "y": 0, "width": 800, "height": 600}
    ]
    
    # 使用mock替代实际的截图函数
    with patch.object(screen_capture, '_capture_loop'):
        # 启动捕获
        result = screen_capture.start_capture(emulator_configs)
        assert result is True
        assert screen_capture._running is True
        assert screen_capture._capture_thread is not None
        
        # 停止捕获
        screen_capture.stop_capture()
        assert screen_capture._running is False


@pytest.mark.qt
def test_get_screen_size(screen_capture):
    """测试获取屏幕尺寸"""
    with patch('src.core.screen_capture.QGuiApplication') as mock_app:
        # 模拟屏幕尺寸
        mock_screen = MagicMock()
        type(mock_screen).availableGeometry = PropertyMock(
            return_value=MagicMock(width=MagicMock(return_value=1920), height=MagicMock(return_value=1080))
        )
        mock_app.primaryScreen.return_value = mock_screen
        
        # 获取屏幕尺寸
        size = screen_capture.get_screen_size()
        assert isinstance(size, dict)
        assert 'width' in size
        assert 'height' in size


@pytest.mark.qt
def test_set_capture_interval(screen_capture):
    """测试设置捕获间隔"""
    # 设置间隔
    screen_capture.set_capture_interval(0.5)
    
    # 验证间隔已设置
    assert screen_capture._interval == 0.5


@pytest.mark.qt
def test_get_available_monitors(screen_capture):
    """测试获取可用监视器"""
    with patch('src.core.screen_capture.mss.mss') as mock_mss:
        # 模拟监视器列表
        mock_instance = MagicMock()
        mock_instance.monitors = [
            {'left': 0, 'top': 0, 'width': 1920, 'height': 1080},  # monitor 0 是虚拟的全屏幕
            {'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'name': '显示器 1'},
            {'left': 1920, 'top': 0, 'width': 1920, 'height': 1080, 'name': '显示器 2'}
        ]
        mock_mss.return_value = mock_instance
        
        # 获取监视器列表
        monitors = screen_capture.get_available_monitors()
        
        # 验证结果
        assert isinstance(monitors, list)
        assert len(monitors) == 2  # 应该只返回实际的监视器，不包括虚拟全屏
        assert 'name' in monitors[0]
        assert 'width' in monitors[0]
        assert 'height' in monitors[0]


@pytest.mark.qt
def test_save_screenshot(screen_capture, tmp_path):
    """测试保存截图"""
    # 创建一个简单的测试图像
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[:, :] = [255, 0, 0]  # 红色图像
    
    # 保存截图
    save_path = tmp_path
    result_path = screen_capture.save_screenshot(test_image, "test", save_path)
    
    # 验证文件已创建
    assert Path(result_path).exists()
    
    # 验证是否为图像文件
    saved_image = cv2.imread(result_path)
    assert saved_image is not None
    assert saved_image.shape == (100, 100, 3)


@pytest.mark.qt
def test_update_config(screen_capture, config_manager):
    """测试更新配置"""
    # 更新配置
    with patch.object(screen_capture, 'get_screen_size', return_value={'width': 1920, 'height': 1080}):
        screen_capture.update_config()
    
    # 验证配置已更新
    config = config_manager.get_config()
    assert 'screen' in config
    assert 'monitor_mode' in config['screen'] 