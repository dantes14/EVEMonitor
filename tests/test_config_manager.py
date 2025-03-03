#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器测试
"""

import os
import sys
import pytest
import yaml
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager


@pytest.fixture
def config_path(tmp_path):
    """创建临时配置文件路径"""
    return tmp_path / "test_config.yaml"


@pytest.fixture
def config_manager(config_path):
    """创建配置管理器实例"""
    return ConfigManager(config_path)


def test_initialization(config_manager, config_path):
    """测试初始化"""
    assert config_manager.config_path == config_path
    assert isinstance(config_manager.config, dict)
    assert "version" in config_manager.config
    assert "app" in config_manager.config
    assert "screen" in config_manager.config
    assert "ocr" in config_manager.config
    assert "notification" in config_manager.config
    assert "appearance" in config_manager.config


def test_get_config(config_manager):
    """测试获取配置"""
    # 获取完整配置
    config = config_manager.get_config()
    assert isinstance(config, dict)
    assert "version" in config
    
    # 获取特定配置项
    version = config_manager.get_config("version")
    assert version == "1.0.0"
    
    # 获取嵌套配置项
    engine = config_manager.get_config("ocr.engine")
    assert engine == "paddleocr"
    
    # 获取不存在的配置项
    value = config_manager.get_config("nonexistent")
    assert value is None
    
    # 获取不存在的嵌套配置项
    value = config_manager.get_config("ocr.nonexistent")
    assert value is None


def test_set_config(config_manager):
    """测试设置配置"""
    # 设置顶层配置项
    config_manager.set_config("version", "2.0.0")
    assert config_manager.get_config("version") == "2.0.0"
    
    # 设置嵌套配置项
    config_manager.set_config("ocr.engine", "tesseract")
    assert config_manager.get_config("ocr.engine") == "tesseract"
    
    # 设置字典配置
    config_manager.set_config("ocr", {
        "engine": "paddleocr",
        "language": "en"
    })
    assert config_manager.get_config("ocr.engine") == "paddleocr"
    assert config_manager.get_config("ocr.language") == "en"
    
    # 设置None值
    config_manager.set_config("ocr", None)
    assert config_manager.get_config("ocr") is None


def test_config_merge(config_manager):
    """测试配置合并"""
    # 准备测试数据
    default_config = {
        "version": "1.0.0",
        "app": {
            "debug": False,
            "first_run": True
        }
    }
    
    user_config = {
        "version": "2.0.0",
        "app": {
            "debug": True
        }
    }
    
    # 测试合并
    merged = config_manager._merge_config(default_config, user_config)
    
    # 验证结果
    assert merged["version"] == "2.0.0"  # 用户配置覆盖默认配置
    assert merged["app"]["debug"] is True  # 用户配置覆盖默认配置
    assert merged["app"]["first_run"] is True  # 保留默认配置


def test_config_save_load(config_manager, config_path):
    """测试配置保存和加载"""
    # 修改配置
    config_manager.set_config("version", "2.0.0")
    config_manager.set_config("ocr.engine", "tesseract")
    
    # 保存配置
    config_manager.save_config()
    
    # 验证配置文件存在
    assert config_path.exists()
    
    # 创建新的配置管理器实例
    new_config_manager = ConfigManager(config_path)
    
    # 验证配置已加载
    assert new_config_manager.get_config("version") == "2.0.0"
    assert new_config_manager.get_config("ocr.engine") == "tesseract"


def test_config_export_import(config_manager, tmp_path):
    """测试配置导出和导入"""
    # 修改配置
    config_manager.set_config("version", "2.0.0")
    config_manager.set_config("ocr.engine", "tesseract")
    
    # 导出配置
    export_path = tmp_path / "exported_config.yaml"
    assert config_manager.export_config(export_path)
    assert export_path.exists()
    
    # 导入配置
    import_path = tmp_path / "imported_config.yaml"
    assert config_manager.import_config(import_path)
    
    # 验证导入的配置
    assert config_manager.get_config("version") == "2.0.0"
    assert config_manager.get_config("ocr.engine") == "tesseract"


def test_config_reset(config_manager):
    """测试配置重置"""
    # 修改配置
    config_manager.set_config("version", "2.0.0")
    config_manager.set_config("ocr.engine", "tesseract")
    
    # 重置配置
    config_manager.reset_config()
    
    # 验证配置已重置
    assert config_manager.get_config("version") == "1.0.0"
    assert config_manager.get_config("ocr.engine") == "paddleocr"


def test_thread_safety(config_manager):
    """测试线程安全"""
    import threading
    
    def update_config():
        config_manager.set_config("version", "2.0.0")
        config_manager.set_config("ocr.engine", "tesseract")
    
    # 创建多个线程同时更新配置
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=update_config)
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 验证最终配置
    assert config_manager.get_config("version") == "2.0.0"
    assert config_manager.get_config("ocr.engine") == "tesseract"


def test_config_changed_signal(config_manager):
    """测试配置变更信号"""
    from PyQt6.QtCore import QObject
    
    class SignalReceiver(QObject):
        def __init__(self):
            super().__init__()
            self.received_key = None
            self.received_value = None
        
        def on_config_changed(self, key, value):
            self.received_key = key
            self.received_value = value
    
    # 创建信号接收器
    receiver = SignalReceiver()
    config_manager.config_changed.connect(receiver.on_config_changed)
    
    # 修改配置
    config_manager.set_config("version", "2.0.0")
    
    # 验证信号
    assert receiver.received_key == "version"
    assert receiver.received_value == "2.0.0"


def test_config_reloaded_signal(config_manager):
    """测试配置重载信号"""
    from PyQt6.QtCore import QObject
    
    class SignalReceiver(QObject):
        def __init__(self):
            super().__init__()
            self.received = False
        
        def on_config_reloaded(self):
            self.received = True
    
    # 创建信号接收器
    receiver = SignalReceiver()
    config_manager.config_reloaded.connect(receiver.on_config_reloaded)
    
    # 重载配置
    config_manager.load_config()
    
    # 验证信号
    assert receiver.received 