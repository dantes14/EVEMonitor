#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块测试
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.main_window import MainWindow
from src.config.config_manager import ConfigManager
from src.core.monitor_manager import MonitorManager
from PyQt6.QtWidgets import QApplication, QTabWidget, QStatusBar, QToolBar


@pytest.fixture
def app():
    """创建QApplication实例"""
    app = QApplication(sys.argv)
    yield app
    app.quit()


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
        return MonitorManager(config_manager)


@pytest.fixture
def main_window(app, config_manager, monitor_manager):
    """创建主窗口实例"""
    with patch('src.ui.main_window.MonitorStatusWidget'), \
         patch('src.ui.main_window.ScreenConfigWidget'), \
         patch('src.ui.main_window.OCRConfigWidget'), \
         patch('src.ui.main_window.NotificationConfigWidget'), \
         patch('src.ui.main_window.QSystemTrayIcon'):
        window = MainWindow(config_manager, monitor_manager, debug_mode=True)
        yield window
        window.close()


@pytest.mark.qt
def test_initialization(main_window):
    """测试初始化"""
    assert main_window is not None
    assert hasattr(main_window, 'config_manager')
    assert hasattr(main_window, 'monitor_manager')
    assert hasattr(main_window, 'tab_widget')
    assert hasattr(main_window, 'status_bar')
    assert hasattr(main_window, 'toolbar')
    assert hasattr(main_window, 'monitor_status_widget')
    assert hasattr(main_window, 'screen_config_widget')
    assert hasattr(main_window, 'ocr_config_widget')
    assert hasattr(main_window, 'notification_config_widget')


@pytest.mark.qt
def test_tab_widget(main_window):
    """测试选项卡窗口部件"""
    assert isinstance(main_window.tab_widget, QTabWidget)
    assert main_window.tab_widget.count() >= 2  # 至少有监控和配置两个选项卡


@pytest.mark.qt
def test_status_bar(main_window):
    """测试状态栏"""
    assert isinstance(main_window.status_bar, QStatusBar)
    assert main_window.statusBar() is main_window.status_bar


@pytest.mark.qt
def test_toolbar(main_window):
    """测试工具栏"""
    assert isinstance(main_window.toolbar, QToolBar)
    assert len(main_window.toolbar.actions()) > 0


@pytest.mark.qt
def test_start_stop_monitoring(main_window):
    """测试开始和停止监控"""
    # 模拟监控管理器
    main_window.monitor_manager.start_monitoring.return_value = True
    main_window.monitor_manager.stop_monitoring.return_value = True
    
    # 测试开始监控
    main_window._on_start_monitoring()
    assert main_window.monitor_manager.start_monitoring.called
    
    # 测试停止监控
    main_window._on_stop_monitoring()
    assert main_window.monitor_manager.stop_monitoring.called


@pytest.mark.qt
def test_on_monitoring_started(main_window):
    """测试监控开始回调"""
    with patch.object(main_window, '_update_status_display') as mock_update:
        main_window._on_monitoring_started()
        assert mock_update.called


@pytest.mark.qt
def test_on_monitoring_stopped(main_window):
    """测试监控停止回调"""
    with patch.object(main_window, '_update_status_display') as mock_update:
        main_window._on_monitoring_stopped()
        assert mock_update.called


@pytest.mark.qt
def test_on_status_updated(main_window):
    """测试状态更新回调"""
    status = {"running": True, "captures_count": 10}
    with patch.object(main_window, '_update_status_display') as mock_update:
        main_window._on_status_updated(status)
        assert mock_update.called


@pytest.mark.qt
def test_on_error_occurred(main_window):
    """测试错误发生回调"""
    with patch('src.ui.main_window.QMessageBox.warning') as mock_warning:
        main_window._on_error_occurred("测试错误")
        assert mock_warning.called


@pytest.mark.qt
def test_on_config_changed(main_window):
    """测试配置变更回调"""
    main_window._on_config_changed("ui.theme", "dark")
    assert main_window.config == main_window.config_manager.get_config()


@pytest.mark.qt
def test_update_status_display(main_window):
    """测试更新状态显示"""
    # 模拟监控管理器状态
    main_window.monitor_manager.get_status.return_value = {
        "running": True,
        "paused": False,
        "captures_count": 10,
        "queue_size": 2,
        "max_queue_size": 5,
        "processing_time_ms": 150,
        "started_at": "2023-01-01 12:00:00"
    }
    
    # 更新状态显示
    main_window._update_status_display()
    
    # 验证状态栏更新
    assert main_window.status_bar.currentMessage() != ""


@pytest.mark.qt
def test_save_load_window_settings(main_window):
    """测试保存和加载窗口设置"""
    # 模拟QSettings
    with patch('src.ui.main_window.QSettings') as mock_settings:
        # 保存设置
        main_window._save_window_settings()
        assert mock_settings.called
        
        # 加载设置
        main_window._load_window_settings()
        assert mock_settings.called 