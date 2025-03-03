#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR引擎测试
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.ocr_engine import OCREngine
from src.config.config_manager import ConfigManager


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
        }
    })
    return config_manager


@pytest.fixture
def ocr_engine(config_manager):
    """创建OCR引擎实例"""
    engine = OCREngine(config_manager)
    yield engine
    engine.stop()


def test_initialization(ocr_engine):
    """测试初始化"""
    assert ocr_engine.engine_type == "paddleocr"
    assert ocr_engine.language == "ch"
    assert ocr_engine.confidence_threshold == 0.6
    assert ocr_engine.use_gpu is False
    assert ocr_engine.num_threads == 4
    assert ocr_engine.batch_size == 1
    assert ocr_engine.running is False
    assert ocr_engine.ocr_thread is None


def test_config_update(ocr_engine, config_manager):
    """测试配置更新"""
    # 更新配置
    config_manager.set_config("ocr.engine", "tesseract")
    config_manager.set_config("ocr.language", "en")
    config_manager.set_config("ocr.confidence_threshold", 0.8)
    config_manager.set_config("ocr.use_gpu", True)
    config_manager.set_config("ocr.num_threads", 8)
    config_manager.set_config("ocr.batch_size", 2)
    
    # 更新引擎配置
    ocr_engine.update_config()
    
    # 验证更新
    assert ocr_engine.engine_type == "tesseract"
    assert ocr_engine.language == "en"
    assert ocr_engine.confidence_threshold == 0.8
    assert ocr_engine.use_gpu is True
    assert ocr_engine.num_threads == 8
    assert ocr_engine.batch_size == 2


def test_recognize_with_tesseract(ocr_engine, config_manager):
    """测试Tesseract文本识别"""
    # 切换到Tesseract引擎
    config_manager.set_config("ocr.engine", "tesseract")
    ocr_engine.update_config()
    
    # 创建测试图像
    image = np.zeros((100, 200), dtype=np.uint8)
    # 这里应该添加一些测试文本到图像中
    
    # 执行识别
    results = ocr_engine._recognize_with_tesseract(image)
    
    # 验证结果
    assert isinstance(results, list)
    # 这里应该添加更多的结果验证


def test_error_handling(ocr_engine, config_manager):
    """测试错误处理"""
    # 测试无效的引擎类型
    config_manager.set_config("ocr.engine", "invalid")
    ocr_engine.update_config()
    assert ocr_engine.engine_type == "tesseract"  # 应该自动切换到Tesseract
    
    # 测试无效的图像输入
    with pytest.raises(Exception):
        ocr_engine._recognize_with_tesseract(None)
    
    # 测试无效的配置
    config_manager.set_config("ocr", "invalid")
    ocr_engine.update_config()
    assert ocr_engine.engine_type == "tesseract"  # 应该使用默认值


def test_thread_safety(ocr_engine, config_manager):
    """测试线程安全"""
    import threading
    
    def update_config():
        config_manager.set_config("ocr.confidence_threshold", 0.9)
        ocr_engine.update_config()
    
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
    assert ocr_engine.confidence_threshold == 0.9 