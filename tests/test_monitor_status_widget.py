#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控状态组件测试
"""

import os
import sys
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.widgets.monitor_status_widget import MonitorStatusWidget
from src.config.config_manager import ConfigManager
from PyQt6.QtWidgets import QApplication, QProgressBar, QTableWidgetItem
from PyQt6.QtCore import Qt


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
        "monitor": {
            "max_table_rows": 100
        }
    }
    return ConfigManager(default_config=config)


@pytest.fixture
def monitor_status_widget(app, config_manager):
    """创建监控状态组件实例"""
    with patch('src.ui.widgets.monitor_status_widget.psutil'):
        widget = MonitorStatusWidget(config_manager)
        yield widget
        widget.update_timer.stop()


@pytest.mark.qt
def test_initialization(monitor_status_widget):
    """测试初始化"""
    assert monitor_status_widget is not None
    assert hasattr(monitor_status_widget, 'config_manager')
    assert hasattr(monitor_status_widget, 'config')
    assert hasattr(monitor_status_widget, 'status_label')
    assert hasattr(monitor_status_widget, 'cpu_progress')
    assert hasattr(monitor_status_widget, 'memory_progress')
    assert hasattr(monitor_status_widget, 'refresh_button')
    assert hasattr(monitor_status_widget, 'table')
    assert hasattr(monitor_status_widget, 'update_timer')
    
    # 验证表格列数
    assert monitor_status_widget.table.columnCount() == 5
    
    # 验证表格标题
    headers = [monitor_status_widget.table.horizontalHeaderItem(i).text() 
               for i in range(monitor_status_widget.table.columnCount())]
    assert headers == ["时间", "区域", "识别文本", "置信度", "状态"]


@pytest.mark.qt
def test_update_status(monitor_status_widget):
    """测试更新状态"""
    # 模拟psutil返回值
    with patch('src.ui.widgets.monitor_status_widget.psutil') as mock_psutil:
        mock_psutil.cpu_percent.return_value = 50
        mock_memory = MagicMock()
        mock_memory.percent = 60
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # 更新状态
        monitor_status_widget._update_status()
        
        # 验证进度条值
        assert monitor_status_widget.cpu_progress.value() == 50
        assert monitor_status_widget.memory_progress.value() == 60


@pytest.mark.qt
def test_update_progress_bar_color(monitor_status_widget):
    """测试更新进度条颜色"""
    # 创建测试进度条
    progress_bar = QProgressBar()
    
    # 测试不同值的颜色
    monitor_status_widget._update_progress_bar_color(progress_bar, 50)
    assert "green" in progress_bar.styleSheet()
    
    monitor_status_widget._update_progress_bar_color(progress_bar, 70)
    assert "orange" in progress_bar.styleSheet()
    
    monitor_status_widget._update_progress_bar_color(progress_bar, 90)
    assert "red" in progress_bar.styleSheet()


@pytest.mark.qt
def test_start_monitoring(monitor_status_widget):
    """测试开始监控"""
    monitor_status_widget.start_monitoring()
    assert monitor_status_widget.status_label.text() == "状态：监控中"
    assert not monitor_status_widget.refresh_button.isEnabled()


@pytest.mark.qt
def test_stop_monitoring(monitor_status_widget):
    """测试停止监控"""
    monitor_status_widget.stop_monitoring()
    assert monitor_status_widget.status_label.text() == "状态：已停止"
    assert monitor_status_widget.refresh_button.isEnabled()


@pytest.mark.qt
def test_add_monitor_data_with_datetime(monitor_status_widget):
    """测试添加监控数据（使用datetime）"""
    # 添加测试数据
    time_value = datetime.now()
    region = {"x": 100, "y": 200}
    text = "测试文本"
    confidence = 0.85
    status = "成功"
    
    monitor_status_widget.add_monitor_data(time_value, region, text, confidence, status)
    
    # 验证表格行数
    assert monitor_status_widget.table.rowCount() == 1
    
    # 验证表格内容
    assert monitor_status_widget.table.item(0, 0).text() == time_value.strftime("%Y-%m-%d %H:%M:%S")
    assert monitor_status_widget.table.item(0, 1).text() == "100, 200"
    assert monitor_status_widget.table.item(0, 2).text() == "测试文本"
    assert monitor_status_widget.table.item(0, 3).text() == "0.85%"
    assert monitor_status_widget.table.item(0, 4).text() == "成功"
    
    # 验证状态颜色
    assert monitor_status_widget.table.item(0, 4).foreground().color() == Qt.GlobalColor.green


@pytest.mark.qt
def test_add_monitor_data_with_string(monitor_status_widget):
    """测试添加监控数据（使用字符串）"""
    # 添加测试数据
    time_value = "2023-01-01 12:00:00"
    region = "区域1"
    text = "测试文本"
    confidence = 0.65
    status = "警告"
    
    monitor_status_widget.add_monitor_data(time_value, region, text, confidence, status)
    
    # 验证表格内容
    assert monitor_status_widget.table.item(0, 0).text() == "2023-01-01 12:00:00"
    assert monitor_status_widget.table.item(0, 1).text() == "区域1"
    assert monitor_status_widget.table.item(0, 4).text() == "警告"
    
    # 验证状态颜色
    assert monitor_status_widget.table.item(0, 4).foreground().color() == Qt.GlobalColor.yellow


@pytest.mark.qt
def test_add_monitor_data_error_status(monitor_status_widget):
    """测试添加监控数据（错误状态）"""
    # 添加测试数据
    monitor_status_widget.add_monitor_data("时间", "区域", "文本", 0.5, "错误")
    
    # 验证状态颜色
    assert monitor_status_widget.table.item(0, 4).foreground().color() == Qt.GlobalColor.red


@pytest.mark.qt
def test_max_table_rows(monitor_status_widget):
    """测试表格最大行数限制"""
    # 设置最大行数
    monitor_status_widget.config["monitor"]["max_table_rows"] = 5
    
    # 添加超过最大行数的数据
    for i in range(10):
        monitor_status_widget.add_monitor_data(f"时间{i}", f"区域{i}", f"文本{i}", 0.9, "成功")
    
    # 验证表格行数不超过最大值
    assert monitor_status_widget.table.rowCount() == 5
    
    # 验证保留的是最新的数据
    assert monitor_status_widget.table.item(0, 0).text() == "时间5"
    assert monitor_status_widget.table.item(4, 0).text() == "时间9" 