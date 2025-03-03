#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR配置组件测试
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
from src.ui.widgets.ocr_config_widget import OCRConfigWidget
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
    config_manager.set_config("ocr", {
        "engine": "paddleocr",
        "language": "ch",
        "confidence_threshold": 0.6,
        "use_gpu": False,
        "num_threads": 4,
        "batch_size": 1,
        "paddle": {
            "model_dir": "",
            "use_det": True,
            "use_cls": True,
            "use_server_mode": False
        },
        "tesseract": {
            "executable_path": "",
            "tessdata_dir": "",
            "config": ""
        },
        "roi": {
            "system_name": {
                "enabled": True,
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 30
            },
            "ship_table": {
                "enabled": True,
                "x": 0,
                "y": 0,
                "width": 400,
                "height": 200
            }
        }
    })
    return config_manager


@pytest.fixture
def widget(config_manager, app):
    """创建OCR配置组件实例"""
    widget = OCRConfigWidget(config_manager)
    widget.show()
    yield widget
    widget.close()


def test_initial_state(widget):
    """测试初始状态"""
    assert widget.engine_combo.currentText() == "PaddleOCR"
    assert widget.language_combo.currentText() == "ch"
    assert widget.confidence_spin.value() == 0.6
    assert widget.use_gpu_check.isChecked() is False
    assert widget.num_threads_spin.value() == 4
    assert widget.batch_size_spin.value() == 1
    assert widget.model_dir_edit.text() == ""
    assert widget.use_det_check.isChecked() is True
    assert widget.use_cls_check.isChecked() is True
    assert widget.use_server_check.isChecked() is False
    assert widget.tesseract_path_edit.text() == ""
    assert widget.tessdata_dir_edit.text() == ""
    assert widget.tesseract_config_edit.text() == ""
    assert widget.system_name_enabled_check.isChecked() is True
    assert widget.system_x_spin.value() == 0
    assert widget.system_y_spin.value() == 0
    assert widget.system_width_spin.value() == 200
    assert widget.system_height_spin.value() == 30
    assert widget.ship_table_enabled_check.isChecked() is True
    assert widget.ship_table_x_spin.value() == 0
    assert widget.ship_table_y_spin.value() == 0
    assert widget.ship_table_width_spin.value() == 400
    assert widget.ship_table_height_spin.value() == 200


def test_engine_change(widget, config_manager):
    """测试OCR引擎切换"""
    widget.engine_combo.setCurrentText("Tesseract")
    assert config_manager.get_config("ocr.engine") == "Tesseract"
    assert widget.paddle_group.isVisible() is False
    assert widget.tesseract_group.isVisible() is True


def test_language_change(widget, config_manager):
    """测试语言设置"""
    widget.language_combo.setCurrentText("en")
    assert config_manager.get_config("ocr.language") == "en"


def test_confidence_threshold_change(widget, config_manager):
    """测试置信度阈值设置"""
    widget.confidence_spin.setValue(0.8)
    assert config_manager.get_config("ocr.confidence_threshold") == 0.8


def test_gpu_setting_change(widget, config_manager):
    """测试GPU设置"""
    widget.use_gpu_check.setChecked(True)
    assert config_manager.get_config("ocr.use_gpu") is True


def test_num_threads_change(widget, config_manager):
    """测试线程数设置"""
    widget.num_threads_spin.setValue(8)
    assert config_manager.get_config("ocr.num_threads") == 8


def test_batch_size_change(widget, config_manager):
    """测试批量处理大小设置"""
    widget.batch_size_spin.setValue(2)
    assert config_manager.get_config("ocr.batch_size") == 2


def test_paddle_settings_change(widget, config_manager):
    """测试PaddleOCR特有设置"""
    widget.model_dir_edit.setText("/path/to/model")
    assert config_manager.get_config("ocr.paddle.model_dir") == "/path/to/model"
    
    widget.use_det_check.setChecked(False)
    assert config_manager.get_config("ocr.paddle.use_det") is False
    
    widget.use_cls_check.setChecked(False)
    assert config_manager.get_config("ocr.paddle.use_cls") is False
    
    widget.use_server_check.setChecked(True)
    assert config_manager.get_config("ocr.paddle.use_server_mode") is True


def test_tesseract_settings_change(widget, config_manager):
    """测试Tesseract特有设置"""
    widget.tesseract_path_edit.setText("/path/to/tesseract")
    assert config_manager.get_config("ocr.tesseract.executable_path") == "/path/to/tesseract"
    
    widget.tessdata_dir_edit.setText("/path/to/tessdata")
    assert config_manager.get_config("ocr.tesseract.tessdata_dir") == "/path/to/tessdata"
    
    widget.tesseract_config_edit.setText("--psm 6")
    assert config_manager.get_config("ocr.tesseract.config") == "--psm 6"


def test_roi_settings_change(widget, config_manager):
    """测试区域设置"""
    # 系统名称区域
    widget.system_name_enabled_check.setChecked(False)
    assert config_manager.get_config("ocr.roi.system_name.enabled") is False
    
    widget.system_x_spin.setValue(100)
    assert config_manager.get_config("ocr.roi.system_name.x") == 100
    
    widget.system_y_spin.setValue(200)
    assert config_manager.get_config("ocr.roi.system_name.y") == 200
    
    widget.system_width_spin.setValue(300)
    assert config_manager.get_config("ocr.roi.system_name.width") == 300
    
    widget.system_height_spin.setValue(40)
    assert config_manager.get_config("ocr.roi.system_name.height") == 40
    
    # 舰船表格区域
    widget.ship_table_enabled_check.setChecked(False)
    assert config_manager.get_config("ocr.roi.ship_table.enabled") is False
    
    widget.ship_table_x_spin.setValue(150)
    assert config_manager.get_config("ocr.roi.ship_table.x") == 150
    
    widget.ship_table_y_spin.setValue(250)
    assert config_manager.get_config("ocr.roi.ship_table.y") == 250
    
    widget.ship_table_width_spin.setValue(500)
    assert config_manager.get_config("ocr.roi.ship_table.width") == 500
    
    widget.ship_table_height_spin.setValue(300)
    assert config_manager.get_config("ocr.roi.ship_table.height") == 300


def test_config_update(widget, config_manager):
    """测试配置更新"""
    # 模拟配置更新
    config_manager.set_config("ocr.engine", "Tesseract")
    config_manager.set_config("ocr.language", "en")
    config_manager.set_config("ocr.confidence_threshold", 0.8)
    config_manager.set_config("ocr.use_gpu", True)
    config_manager.set_config("ocr.num_threads", 8)
    config_manager.set_config("ocr.batch_size", 2)
    
    # 验证UI更新
    assert widget.engine_combo.currentText() == "Tesseract"
    assert widget.language_combo.currentText() == "en"
    assert widget.confidence_spin.value() == 0.8
    assert widget.use_gpu_check.isChecked() is True
    assert widget.num_threads_spin.value() == 8
    assert widget.batch_size_spin.value() == 2


def test_invalid_config(widget, config_manager):
    """测试无效配置处理"""
    # 设置无效配置
    config_manager.set_config("ocr", {})
    
    # 验证使用默认值
    assert widget.engine_combo.currentText() == "PaddleOCR"
    assert widget.language_combo.currentText() == "ch"
    assert widget.confidence_spin.value() == 0.6
    assert widget.use_gpu_check.isChecked() is False
    assert widget.num_threads_spin.value() == 4
    assert widget.batch_size_spin.value() == 1


def test_missing_config(widget, config_manager):
    """测试缺失配置处理"""
    # 删除OCR配置
    config = config_manager.get_config()
    del config["ocr"]
    config_manager.set_config("ocr", None)
    
    # 验证使用默认值
    assert widget.engine_combo.currentText() == "PaddleOCR"
    assert widget.language_combo.currentText() == "ch"
    assert widget.confidence_spin.value() == 0.6
    assert widget.use_gpu_check.isChecked() is False
    assert widget.num_threads_spin.value() == 4
    assert widget.batch_size_spin.value() == 1


def test_invalid_config_type(widget, config_manager):
    """测试配置类型错误处理"""
    # 设置错误类型的配置
    config_manager.set_config("ocr", "invalid")
    
    # 验证使用默认值
    assert widget.engine_combo.currentText() == "PaddleOCR"
    assert widget.language_combo.currentText() == "ch"
    assert widget.confidence_spin.value() == 0.6
    assert widget.use_gpu_check.isChecked() is False
    assert widget.num_threads_spin.value() == 4
    assert widget.batch_size_spin.value() == 1 