#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析模块测试
"""

import os
import sys
import time
from datetime import datetime
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.data_analyzer import DataAnalyzer
from src.config.config_manager import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    """创建配置管理器实例"""
    config_path = tmp_path / "test_config.yaml"
    return ConfigManager(config_path)


@pytest.fixture
def data_analyzer(config_manager):
    """创建数据分析器实例"""
    with patch.object(config_manager, 'get_config', return_value={
        "analysis": {
            "intervals": {
                "ship_status": 5,
                "target": 5,
                "chat": 10,
                "system": 15
            },
            "alerts": {
                "ship_health": {
                    "shield_threshold": 50,
                    "armor_threshold": 70,
                    "structure_threshold": 90,
                    "cooldown": 60
                },
                "chat_keywords": ["紧急", "救援", "红色警报"],
                "targets": ["海盗", "敌对"],
                "system_names": ["吉他", "危险星系"],
                "cooldown": 30
            }
        }
    }):
        analyzer = DataAnalyzer(config_manager)
    return analyzer


@pytest.fixture
def ocr_ship_status_result():
    """创建OCR舰船状态识别结果"""
    return [
        {"text": "护盾: 75%", "confidence": 0.95, "box": [10, 20, 100, 40]},
        {"text": "装甲: 90%", "confidence": 0.93, "box": [10, 50, 100, 70]},
        {"text": "结构: 100%", "confidence": 0.97, "box": [10, 80, 100, 100]}
    ]


@pytest.fixture
def ocr_target_result():
    """创建OCR目标识别结果"""
    return [
        {"text": "目标: 海盗战舰", "confidence": 0.92, "box": [10, 20, 150, 40]},
        {"text": "类型: 巡洋舰", "confidence": 0.90, "box": [10, 50, 150, 70]},
        {"text": "状态: 敌对", "confidence": 0.94, "box": [10, 80, 150, 100]}
    ]


@pytest.fixture
def ocr_chat_result():
    """创建OCR聊天识别结果"""
    return [
        {"text": "[本地] 玩家1: 你好", "confidence": 0.91, "box": [10, 20, 200, 40]},
        {"text": "[联盟] 玩家2: 紧急救援请求", "confidence": 0.89, "box": [10, 50, 200, 70]},
        {"text": "[公司] 玩家3: 正常对话", "confidence": 0.93, "box": [10, 80, 200, 100]}
    ]


@pytest.fixture
def ocr_system_result():
    """创建OCR星系识别结果"""
    return [
        {"text": "当前星系: 吉他", "confidence": 0.96, "box": [10, 20, 150, 40]},
        {"text": "安全等级: 0.5", "confidence": 0.95, "box": [10, 50, 150, 70]}
    ]


def test_initialization(data_analyzer):
    """测试初始化"""
    assert data_analyzer is not None
    assert hasattr(data_analyzer, 'config_manager')
    assert hasattr(data_analyzer, 'last_status')
    assert hasattr(data_analyzer, 'history')
    assert hasattr(data_analyzer, 'alert_history')


def test_analyze_data(data_analyzer):
    """测试分析数据主函数"""
    # 创建测试任务
    task = {
        "type": "ship_status",
        "emulator": "test_emulator",
        "ocr_result": [{"text": "护盾: 75%", "confidence": 0.95}]
    }
    
    # 使用Mock替代具体分析函数
    with patch.object(data_analyzer, '_analyze_ship_status', return_value={"shield": 75}) as mock_method:
        result = data_analyzer.analyze_data(task)
        
        # 验证调用了正确的分析函数
        mock_method.assert_called_once_with([{"text": "护盾: 75%", "confidence": 0.95}], "test_emulator")
        
        # 验证返回结果
        assert result["type"] == "ship_status"
        assert result["emulator"] == "test_emulator"
        assert result["analysis_result"] == {"shield": 75}


def test_analyze_ship_status(data_analyzer, ocr_ship_status_result):
    """测试分析舰船状态"""
    # 分析舰船状态
    result = data_analyzer._analyze_ship_status(ocr_ship_status_result, "test_emulator")
    
    # 验证结果
    assert "shield" in result
    assert "armor" in result
    assert "structure" in result
    assert result["shield"] == 75
    assert result["armor"] == 90
    assert result["structure"] == 100


def test_analyze_target(data_analyzer, ocr_target_result):
    """测试分析目标"""
    # 分析目标
    result = data_analyzer._analyze_target(ocr_target_result, "test_emulator")
    
    # 验证结果
    assert "name" in result
    assert "type" in result
    assert "status" in result
    assert result["name"] == "海盗战舰"
    assert result["type"] == "巡洋舰"
    assert result["status"] == "敌对"


def test_analyze_chat(data_analyzer, ocr_chat_result):
    """测试分析聊天"""
    # 分析聊天
    result = data_analyzer._analyze_chat(ocr_chat_result, "test_emulator")
    
    # 验证结果
    assert "messages" in result
    assert len(result["messages"]) == 3
    assert "channel" in result["messages"][0]
    assert "sender" in result["messages"][0]
    assert "content" in result["messages"][0]
    assert result["messages"][1]["content"] == "紧急救援请求"


def test_analyze_system(data_analyzer, ocr_system_result):
    """测试分析星系"""
    # 分析星系
    result = data_analyzer._analyze_system(ocr_system_result, "test_emulator")
    
    # 验证结果
    assert "name" in result
    assert "security" in result
    assert result["name"] == "吉他"
    assert result["security"] == 0.5


def test_check_ship_alerts(data_analyzer):
    """测试检查舰船警报"""
    # 创建舰船状态
    ship_status = {
        "shield": 40,  # 低于阈值
        "armor": 80,   # 高于阈值
        "structure": 95 # 高于阈值
    }
    
    # 检查警报
    with patch.object(data_analyzer, '_can_trigger_alert', return_value=True):
        alerts = data_analyzer._check_ship_alerts(ship_status, "test_emulator")
    
    # 验证结果
    assert len(alerts) == 1
    assert alerts[0]["type"] == "shield_low"
    assert alerts[0]["value"] == 40


def test_is_threat_target(data_analyzer):
    """测试判断是否为威胁目标"""
    # 测试不同情况
    assert data_analyzer._is_threat_target("海盗", "巡洋舰", "敌对") is True
    assert data_analyzer._is_threat_target("友好NPC", "战列舰", "友好") is False
    assert data_analyzer._is_threat_target("未知", None, None) is False


def test_contains_keywords(data_analyzer):
    """测试是否包含关键词"""
    # 测试不同情况
    assert data_analyzer._contains_keywords("这是一个紧急情况", ["紧急", "救援"]) is True
    assert data_analyzer._contains_keywords("正常对话内容", ["紧急", "救援"]) is False


def test_extract_text(data_analyzer, ocr_chat_result):
    """测试提取文本"""
    # 提取所有文本
    text = data_analyzer._extract_text(ocr_chat_result)
    
    # 验证结果
    assert "[本地] 玩家1: 你好" in text
    assert "[联盟] 玩家2: 紧急救援请求" in text
    assert "[公司] 玩家3: 正常对话" in text


def test_should_analyze(data_analyzer):
    """测试是否应该进行分析"""
    # 设置上次分析时间
    emulator = "test_emulator"
    data_analyzer.last_status[emulator] = {
        "last_analysis": {
            "ship_status": datetime.now(),
            "target": datetime.now(),
            "chat": datetime.now(),
            "system": datetime.now()
        }
    }
    
    # 验证结果
    assert data_analyzer._should_analyze(emulator, "ship_status") is False
    
    # 修改上次分析时间为较早时间
    from datetime import timedelta
    data_analyzer.last_status[emulator]["last_analysis"]["ship_status"] = \
        datetime.now() - timedelta(seconds=10)
    
    # 验证结果
    assert data_analyzer._should_analyze(emulator, "ship_status") is True


def test_can_trigger_alert(data_analyzer):
    """测试是否可以触发警报"""
    emulator = "test_emulator"
    alert_type = "shield_low"
    
    # 初始状态应该可以触发
    assert data_analyzer._can_trigger_alert(emulator, alert_type) is True
    
    # 记录警报
    data_analyzer.alert_history[emulator] = {
        alert_type: datetime.now()
    }
    
    # 应该不能再次触发
    assert data_analyzer._can_trigger_alert(emulator, alert_type) is False
    
    # 修改上次警报时间为较早时间
    data_analyzer.alert_history[emulator][alert_type] = \
        datetime.now() - timedelta(seconds=100)
    
    # 应该可以再次触发
    assert data_analyzer._can_trigger_alert(emulator, alert_type) is True


def test_get_analysis_history(data_analyzer):
    """测试获取分析历史"""
    # 添加一些历史记录
    data_analyzer.history = {
        "emulator1": {"ship_status": [{"timestamp": time.time(), "data": {"shield": 80}}]},
        "emulator2": {"chat": [{"timestamp": time.time(), "data": {"messages": []}}]}
    }
    
    # 获取所有历史
    history = data_analyzer.get_analysis_history()
    assert "emulator1" in history
    assert "emulator2" in history
    
    # 获取特定模拟器历史
    history = data_analyzer.get_analysis_history("emulator1")
    assert "ship_status" in history
    assert len(history["ship_status"]) == 1


def test_clear_history(data_analyzer):
    """测试清除历史记录"""
    # 添加一些历史记录
    data_analyzer.history = {
        "emulator1": {"ship_status": [{"timestamp": time.time(), "data": {"shield": 80}}]},
        "emulator2": {"chat": [{"timestamp": time.time(), "data": {"messages": []}}]}
    }
    
    # 清除特定模拟器历史
    data_analyzer.clear_history("emulator1")
    assert "emulator1" not in data_analyzer.history
    assert "emulator2" in data_analyzer.history
    
    # 清除所有历史
    data_analyzer.clear_history()
    assert len(data_analyzer.history) == 0 