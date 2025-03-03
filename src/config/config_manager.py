#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块

负责加载、保存和管理应用程序的配置。
支持热更新和配置变更通知。
"""

import os
import sys
import yaml
import json
import copy
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger


class ConfigManager(QObject):
    """配置管理器类，负责管理应用程序配置"""
    
    # 信号定义
    config_changed = pyqtSignal(str, object)  # 配置项变更信号
    config_reloaded = pyqtSignal()  # 配置重新加载信号
    
    # 默认配置
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "app": {
            "debug": False,
            "first_run": True,
            "screenshot_interval": 2.0,  # 截图间隔，单位秒
            "enable_sound": True,  # 启用声音提示
        },
        "screen": {
            "monitor_mode": "full_screen",  # full_screen 或 custom_region
            "custom_region": {
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080
            },
            "simulators": []  # 模拟器列表将在首次运行时自动配置
        },
        "ocr": {
            "engine": "paddleocr",  # paddleocr 或 tesseract
            "language": "ch",
            "confidence_threshold": 0.6,
            "system_name_region": {  # 星系名称区域相对于模拟器的位置
                "x_ratio": 0.45,
                "y_ratio": 0.05,
                "width_ratio": 0.5,
                "height_ratio": 0.05
            },
            "ship_table_region": {  # 舰船表格区域相对于模拟器的位置
                "x_ratio": 0.1,
                "y_ratio": 0.3,
                "width_ratio": 0.8,
                "height_ratio": 0.5
            },
            "tesseract_path": "",  # Tesseract OCR可执行文件路径
            "paddleocr_use_gpu": False  # 是否使用GPU加速PaddleOCR
        },
        "notification": {
            "enabled": True,
            "cooldown": 60,  # 通知冷却时间，单位秒
            "include_screenshot": True,  # 通知是否包含截图
            "methods": {
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "custom_headers": {},
                    "template": "在星系 {system_name} 发现舰船: {ship_count}艘"
                },
                "api": {
                    "enabled": False,
                    "url": "",
                    "method": "POST",
                    "api_key": "",
                    "custom_headers": {}
                }
            },
            "filters": {
                "ignored_systems": [],  # 忽略的星系名称
                "ignored_ships": []  # 忽略的舰船类型
            }
        },
        "appearance": {
            "theme": "dark",  # dark 或 light
            "font_size": 12,
            "language": "zh_CN"  # 界面语言
        }
    }
    
    def __init__(self, config_path: Union[str, Path]):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        super().__init__()
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._lock = threading.RLock()  # 重入锁，用于线程安全操作
        
        # 确保配置文件目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        if self.config_path.exists():
            self.load_config()
        else:
            logger.info(f"配置文件不存在，创建默认配置: {self.config_path}")
            self.config = copy.deepcopy(self.DEFAULT_CONFIG)
            self.save_config()
    
    def load_config(self) -> None:
        """从文件加载配置"""
        try:
            with self._lock:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                
                # 使用递归方法合并配置，确保新版本中的新配置项也被包含
                self.config = self._merge_config(copy.deepcopy(self.DEFAULT_CONFIG), loaded_config)
                
                logger.info(f"配置已加载: {self.config_path}")
                self.config_reloaded.emit()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.config = copy.deepcopy(self.DEFAULT_CONFIG)
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with self._lock:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                
                logger.debug(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键路径，使用点号分隔，如 "ocr.engine"
            default: 如果配置不存在，返回的默认值
            
        Returns:
            配置值或默认值
        """
        with self._lock:
            if key is None:
                return copy.deepcopy(self.config)
            
            value = self.config
            try:
                for k in key.split('.'):
                    if not isinstance(value, dict):
                        return default
                    value = value.get(k, default)
                    if value is default:
                        return default
                return copy.deepcopy(value)
            except (KeyError, TypeError):
                return default
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键路径，使用点号分隔，如 "ocr.engine"
            value: 要设置的值
        """
        with self._lock:
            if key is None:
                return
            
            keys = key.split('.')
            target = self.config
            
            # 导航到最后一个键的父级
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            # 设置值
            last_key = keys[-1]
            old_value = target.get(last_key)
            
            # 只有当值发生变化时才更新和发出信号
            if old_value != value:
                target[last_key] = value
                # 发送变更的值，而不是完整的配置对象
                self.config_changed.emit(key, value)
                logger.debug(f"配置已更新: {key} = {value}")
                
                # 自动保存配置
                self.save_config()
    
    def update_simulator_config(self, simulators: List[Dict[str, Any]]) -> None:
        """更新模拟器配置
        
        Args:
            simulators: 模拟器配置列表
        """
        self.set_config("screen.simulators", simulators)
    
    def reset_config(self) -> None:
        """重置配置为默认值"""
        with self._lock:
            self.config = copy.deepcopy(self.DEFAULT_CONFIG)
            self.save_config()
            self.config_reloaded.emit()
            logger.info("配置已重置为默认值")
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置，确保默认配置中的所有键都存在
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            合并后的配置
        """
        if user is None:
            return default
        
        result = copy.deepcopy(default)
        
        for key, value in user.items():
            # 如果用户配置中有而默认配置没有的键，保留用户配置
            if key not in result:
                result[key] = value
            # 如果两者都是字典，递归合并
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            # 否则使用用户配置
            else:
                result[key] = value
        
        return result
    
    def export_config(self, export_path: Union[str, Path]) -> bool:
        """导出配置到指定路径
        
        Args:
            export_path: 导出路径
            
        Returns:
            是否成功导出
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已导出: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: Union[str, Path]) -> bool:
        """从指定路径导入配置
        
        Args:
            import_path: 导入路径
            
        Returns:
            是否成功导入
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            self.config = self._merge_config(copy.deepcopy(self.DEFAULT_CONFIG), loaded_config)
            self.save_config()
            self.config_reloaded.emit()
            logger.info(f"配置已导入: {import_path}")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False 