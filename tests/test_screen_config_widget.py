#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕配置组件测试
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
from src.ui.widgets.screen_config_widget import ScreenConfigWidget
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
    config_manager.set_config("screen", {
        "monitor_mode": "full_screen",
        "custom_region": {
            "x": 0,
            "y": 0,
            "width": 1920,
            "height": 1080
        },
        "grid_layout": {
            "rows": 2,
            "columns": 2,
            "spacing": 10
        },
        "simulators": []
    })
    return config_manager


@pytest.fixture
def widget(config_manager, app):
    """创建屏幕配置组件实例"""
    widget = ScreenConfigWidget(config_manager)
    widget.show()
    yield widget
    widget.close()


def test_initial_state(widget):
    """测试初始状态"""
    assert widget.monitor_mode_combo.currentText() == "全屏"
    assert widget.custom_region_group.isEnabled() is False
    assert widget.grid_layout_group.isEnabled() is False


def test_monitor_mode_change(widget, config_manager):
    """测试监控模式变更"""
    widget.monitor_mode_combo.setCurrentText("自定义区域")
    assert config_manager.get_config("screen.monitor_mode") == "自定义区域"
    assert widget.custom_region_group.isEnabled() is True
    assert widget.grid_layout_group.isEnabled() is False


def test_custom_region_change(widget, config_manager):
    """测试自定义区域变更"""
    # 切换到自定义区域模式
    widget.monitor_mode_combo.setCurrentText("自定义区域")
    
    # 更新区域设置
    widget.x_spin.setValue(100)
    widget.y_spin.setValue(200)
    widget.width_spin.setValue(800)
    widget.height_spin.setValue(600)
    
    assert config_manager.get_config("screen.custom_region.x") == 100
    assert config_manager.get_config("screen.custom_region.y") == 200
    assert config_manager.get_config("screen.custom_region.width") == 800
    assert config_manager.get_config("screen.custom_region.height") == 600


def test_grid_layout_change(widget, config_manager):
    """测试网格布局变更"""
    # 切换到网格布局模式
    widget.monitor_mode_combo.setCurrentText("网格布局")
    
    # 更新网格设置
    widget.rows_spin.setValue(3)
    widget.cols_spin.setValue(4)
    widget.spacing_spin.setValue(20)
    
    assert config_manager.get_config("screen.grid_layout.rows") == 3
    assert config_manager.get_config("screen.grid_layout.columns") == 4
    assert config_manager.get_config("screen.grid_layout.spacing") == 20


def test_config_update(widget, config_manager):
    """测试配置更新"""
    # 模拟配置更新
    config_manager.set_config("screen.monitor_mode", "网格布局")
    config_manager.set_config("screen.grid_layout.rows", 2)
    config_manager.set_config("screen.grid_layout.columns", 3)
    config_manager.set_config("screen.grid_layout.spacing", 15)
    
    # 验证UI更新
    assert widget.monitor_mode_combo.currentText() == "网格布局"
    assert widget.rows_spin.value() == 2
    assert widget.cols_spin.value() == 3
    assert widget.spacing_spin.value() == 15


def test_invalid_config(widget, config_manager):
    """测试无效配置处理"""
    # 设置无效配置
    config_manager.set_config("screen", {})
    
    # 验证使用默认值
    assert widget.monitor_mode_combo.currentText() == "全屏"
    assert widget.custom_region_group.isEnabled() is False
    assert widget.grid_layout_group.isEnabled() is False


def test_missing_config(widget, config_manager):
    """测试缺失配置处理"""
    # 删除屏幕配置
    config = config_manager.get_config()
    del config["screen"]
    config_manager.set_config("screen", None)
    
    # 验证使用默认值
    assert widget.monitor_mode_combo.currentText() == "全屏"
    assert widget.custom_region_group.isEnabled() is False
    assert widget.grid_layout_group.isEnabled() is False


def test_invalid_config_type(widget, config_manager):
    """测试配置类型错误处理"""
    # 设置错误类型的配置
    config_manager.set_config("screen", "invalid")
    
    # 验证使用默认值
    assert widget.monitor_mode_combo.currentText() == "全屏"
    assert widget.custom_region_group.isEnabled() is False
    assert widget.grid_layout_group.isEnabled() is False 