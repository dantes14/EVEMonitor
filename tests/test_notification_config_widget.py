#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知配置组件测试
"""

import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.widgets.notification_config_widget import NotificationConfigWidget
from src.config.config_manager import ConfigManager


@pytest.fixture(scope="session")
def app():
    """创建QApplication实例"""
    app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def config_manager(tmp_path):
    """创建配置管理器实例"""
    config_path = tmp_path / "test_config.yaml"
    config_manager = ConfigManager(config_path)
    # 设置默认配置
    config_manager.set_config("notification", {
        "method": "system",
        "sound": True,
        "volume": 0.7,
        "popup": True,
        "duration": 5
    })
    return config_manager


@pytest.fixture
def widget(config_manager, app):
    """创建通知配置组件实例"""
    widget = NotificationConfigWidget(config_manager)
    widget.show()
    yield widget
    widget.close()


def test_initial_state(widget):
    """测试初始状态"""
    assert widget.method_combo.currentText() == "system"
    assert widget.sound_check.isChecked() is True
    assert widget.volume_slider.value() == 70
    assert widget.popup_check.isChecked() is True
    assert widget.duration_spin.value() == 5


def test_method_change(widget, config_manager):
    """测试通知方式变更"""
    widget.method_combo.setCurrentText("custom")
    config = config_manager.get_config()
    assert config["notification"]["method"] == "custom"


def test_sound_toggle(widget, config_manager):
    """测试声音通知开关"""
    widget.sound_check.setChecked(False)
    config = config_manager.get_config()
    assert config["notification"]["sound"] is False


def test_volume_change(widget, config_manager):
    """测试音量调整"""
    widget.volume_slider.setValue(50)
    config = config_manager.get_config()
    assert config["notification"]["volume"] == 0.5


def test_popup_toggle(widget, config_manager):
    """测试弹窗通知开关"""
    widget.popup_check.setChecked(False)
    config = config_manager.get_config()
    assert config["notification"]["popup"] is False


def test_duration_change(widget, config_manager):
    """测试弹窗显示时间调整"""
    widget.duration_spin.setValue(10)
    config = config_manager.get_config()
    assert config["notification"]["duration"] == 10


def test_config_update(widget, config_manager):
    """测试配置更新"""
    # 模拟配置更新
    config_manager.set_config("notification", {
        "method": "custom",
        "sound": False,
        "volume": 0.5,
        "popup": False,
        "duration": 10
    })
    
    # 验证UI更新
    assert widget.method_combo.currentText() == "custom"
    assert widget.sound_check.isChecked() is False
    assert widget.volume_slider.value() == 50
    assert widget.popup_check.isChecked() is False
    assert widget.duration_spin.value() == 10


def test_invalid_config(widget, config_manager):
    """测试无效配置处理"""
    # 设置无效配置
    config_manager.set_config("notification", {})
    
    # 验证使用默认值
    assert widget.method_combo.currentText() == "system"
    assert widget.sound_check.isChecked() is True
    assert widget.volume_slider.value() == 70
    assert widget.popup_check.isChecked() is True
    assert widget.duration_spin.value() == 5 