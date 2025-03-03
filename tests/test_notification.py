#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知管理器测试模块
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.core.notification import NotificationManager
from src.config.config_manager import ConfigManager


@pytest.fixture
def app():
    """创建QApplication实例"""
    app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def config_manager():
    """创建配置管理器实例"""
    config = {
        "notification": {
            "enabled": True,
            "title": "EVEMonitor",
            "min_interval": 1,  # 测试时使用较小的间隔
            "system_notify": True,
            "sound_notify": True,
            "sound_file": "test.wav"
        }
    }
    return ConfigManager(default_config=config)


@pytest.fixture
def notification_manager(config_manager):
    """创建通知管理器实例"""
    return NotificationManager(config_manager, test_mode=True)


def test_initialization(notification_manager):
    """测试初始化"""
    assert notification_manager.config is not None
    assert notification_manager.tray_icon is None  # 测试模式下不创建托盘图标
    assert notification_manager.last_notification_time is None
    assert notification_manager.notification_count == 0
    assert notification_manager.test_mode is True


def test_send_notification(notification_manager):
    """测试发送通知"""
    # 发送测试通知
    result = notification_manager.send_notification("测试通知")
    assert result is True
    assert notification_manager.notification_count == 1
    assert notification_manager.last_notification_time is not None


def test_notification_interval(notification_manager):
    """测试通知间隔"""
    # 发送第一条通知
    notification_manager.send_notification("第一条通知")
    first_time = notification_manager.last_notification_time
    
    # 立即发送第二条通知（应该被限制）
    result = notification_manager.send_notification("第二条通知")
    assert result is False
    assert notification_manager.notification_count == 1
    
    # 等待间隔时间后发送
    notification_manager.last_notification_time = datetime.now() - timedelta(seconds=2)
    result = notification_manager.send_notification("第三条通知")
    assert result is True
    assert notification_manager.notification_count == 2


def test_notification_disabled(notification_manager):
    """测试通知禁用"""
    # 禁用通知
    notification_manager.config["notification"]["enabled"] = False
    
    # 尝试发送通知
    result = notification_manager.send_notification("测试通知")
    assert result is False
    assert notification_manager.notification_count == 0


def test_test_notification(notification_manager):
    """测试发送测试通知"""
    result = notification_manager.send_test_notification()
    assert result is True
    assert notification_manager.notification_count == 1


def test_update_config(notification_manager):
    """测试更新配置"""
    new_config = {
        "notification": {
            "enabled": True,
            "title": "新标题",
            "min_interval": 5,
            "system_notify": False,
            "sound_notify": False
        }
    }
    
    notification_manager.update_config(new_config)
    assert notification_manager.config == new_config
    assert notification_manager.config["notification"]["title"] == "新标题"
    assert notification_manager.config["notification"]["min_interval"] == 5


def test_invalid_sound_file(notification_manager):
    """测试无效的声音文件"""
    # 设置不存在的声音文件
    notification_manager.config["notification"]["sound_file"] = "nonexistent.wav"
    
    # 发送通知（应该正常发送，只是不播放声音）
    result = notification_manager.send_notification("测试通知")
    assert result is True
    assert notification_manager.notification_count == 1 