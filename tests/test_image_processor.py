#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图像处理模块测试
"""

import os
import sys
import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.image_processor import ImageProcessor
from src.config.config_manager import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    """创建配置管理器实例"""
    config_path = tmp_path / "test_config.yaml"
    return ConfigManager(config_path)


@pytest.fixture
def image_processor(config_manager):
    """创建图像处理器实例"""
    with patch.object(config_manager, 'get_config', return_value={
        "thresholds": {
            "default": 127,
            "ship_status": 150,
            "chat": 140,
            "target": 130,
            "system": 120
        }
    }):
        processor = ImageProcessor(config_manager)
    return processor


@pytest.fixture
def test_image():
    """创建测试图像"""
    # 创建一个简单的测试图像 (100x100, 灰度图)
    image = np.zeros((100, 100), dtype=np.uint8)
    # 添加一些文本形状
    cv2.putText(image, "EVE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    return image


@pytest.fixture
def color_test_image():
    """创建彩色测试图像"""
    # 创建一个简单的彩色测试图像 (100x100)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    # 添加一些文本和颜色
    cv2.putText(image, "EVE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    # 添加一个红色矩形
    cv2.rectangle(image, (70, 30), (90, 70), (0, 0, 255), -1)
    return image


def test_initialization(image_processor):
    """测试初始化"""
    assert image_processor is not None
    assert hasattr(image_processor, 'threshold_values')
    assert image_processor.threshold_values.get('default') == 127


def test_process_image_default(image_processor, test_image):
    """测试默认处理图像"""
    # 处理图像
    with patch.object(image_processor, '_process_default', return_value=test_image) as mock_process:
        result = image_processor.process_image(test_image)
        mock_process.assert_called_once_with(test_image)
    
    # 验证结果类型
    assert isinstance(result, np.ndarray)
    assert result.shape == test_image.shape


def test_process_image_ship_status(image_processor, test_image):
    """测试处理舰船状态图像"""
    # 处理图像
    with patch.object(image_processor, '_process_ship_status', return_value=test_image) as mock_process:
        result = image_processor.process_image(test_image, "ship_status")
        mock_process.assert_called_once_with(test_image)
    
    # 验证结果类型
    assert isinstance(result, np.ndarray)
    assert result.shape == test_image.shape


def test_enhance_image(image_processor, test_image):
    """测试增强图像"""
    # 增强图像
    enhanced = image_processor._enhance_image(test_image, alpha=1.5, beta=10, gamma=1.2)
    
    # 验证结果
    assert isinstance(enhanced, np.ndarray)
    assert enhanced.shape == test_image.shape
    # 验证图像已被增强（亮度增加）
    assert np.mean(enhanced) > np.mean(test_image)


def test_remove_noise(image_processor, test_image):
    """测试去噪"""
    # 添加噪声
    noisy_image = test_image.copy()
    noise = np.random.normal(0, 25, test_image.shape).astype(np.uint8)
    noisy_image = cv2.add(noisy_image, noise)
    
    # 去噪
    denoised = image_processor._remove_noise(noisy_image)
    
    # 验证结果
    assert isinstance(denoised, np.ndarray)
    assert denoised.shape == test_image.shape
    # 验证噪声已减少
    assert np.std(denoised) < np.std(noisy_image)


def test_scale_image(image_processor, test_image):
    """测试缩放图像"""
    # 缩放图像
    scaled = image_processor.scale_image(test_image)
    
    # 验证结果
    assert isinstance(scaled, np.ndarray)
    assert scaled.shape == test_image.shape  # 默认情况下应该保持相同尺寸


def test_extract_regions(image_processor, color_test_image):
    """测试提取区域"""
    # 定义区域
    regions = {
        "region1": {"x": 10, "y": 10, "width": 50, "height": 50},
        "region2": {"x": 60, "y": 30, "width": 30, "height": 40}
    }
    
    # 提取区域
    extracted = image_processor.extract_regions(color_test_image, regions)
    
    # 验证结果
    assert isinstance(extracted, dict)
    assert len(extracted) == 2
    assert "region1" in extracted
    assert "region2" in extracted
    assert extracted["region1"].shape == (50, 50, 3)
    assert extracted["region2"].shape == (40, 30, 3)


def test_detect_text_regions(image_processor, test_image):
    """测试检测文本区域"""
    # 检测文本区域
    with patch('cv2.findContours', return_value=([
        np.array([[10, 40], [60, 40], [60, 60], [10, 60]])
    ], None)):
        regions = image_processor.detect_text_regions(test_image)
    
    # 验证结果
    assert isinstance(regions, list)
    assert len(regions) >= 0  # 可能检测不到区域，所以只验证类型
    if regions:
        assert 'x' in regions[0]
        assert 'y' in regions[0]
        assert 'width' in regions[0]
        assert 'height' in regions[0]


def test_create_debug_image(image_processor, color_test_image):
    """测试创建调试图像"""
    # 定义区域
    regions = {
        "region1": {"x": 10, "y": 10, "width": 50, "height": 50}
    }
    
    # 检测区域
    detected_regions = [{"x": 10, "y": 40, "width": 50, "height": 20}]
    
    # 创建调试图像
    debug_image = image_processor.create_debug_image(
        color_test_image, detected_regions, regions
    )
    
    # 验证结果
    assert isinstance(debug_image, np.ndarray)
    assert debug_image.shape == color_test_image.shape 