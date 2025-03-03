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
    config_changed = pyqtSignal(dict)  # 配置项变更信号
    config_reloaded = pyqtSignal(dict)  # 配置重新加载信号
    
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
    
    def __init__(self, config_path: str = None, default_config: Dict[str, Any] = None):
        """
        初始化配置管理器
        
        参数:
            config_path: 配置文件路径，如果为None则使用默认路径
            default_config: 默认配置字典，如果为None则使用内置默认配置
        """
        super().__init__()
        
        # 设置配置文件路径
        if config_path is None:
            config_dir = Path.home() / ".evemonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        # 设置默认配置
        if default_config is None:
            self.default_config = {
                "notification": {
                    "enabled": True,
                    "title": "EVEMonitor",
                    "min_interval": 60,
                    "system_notify": True,
                    "sound_notify": True,
                    "sound_file": ""
                },
                "screen": {
                    "monitor_mode": "full",
                    "custom_region": {
                        "enabled": False,
                        "x": 0,
                        "y": 0,
                        "width": 800,
                        "height": 600
                    },
                    "grid_layout": {
                        "enabled": False,
                        "rows": 2,
                        "columns": 2,
                        "spacing": 10
                    }
                },
                "ocr": {
                    "engine": "tesseract",
                    "language": "chi_sim",
                    "confidence": 0.8,
                    "use_gpu": False,
                    "num_threads": 4,
                    "batch_size": 1
                }
            }
        else:
            self.default_config = default_config
        
        # 加载配置
        self.config = self._load_config()
        
        logger.debug("配置管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        返回:
            Dict[str, Any]: 配置字典
        """
        try:
            # 如果配置文件存在，则加载
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
            else:
                user_config = {}
            
            # 合并默认配置和用户配置
            config = self._merge_config(self.default_config, user_config)
            
            # 保存合并后的配置
            self._save_config(config)
            
            return config
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return self.default_config.copy()
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并默认配置和用户配置
        
        参数:
            default: 默认配置
            user: 用户配置
            
        返回:
            Dict[str, Any]: 合并后的配置
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        保存配置
        
        参数:
            config: 要保存的配置
        """
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            logger.debug("配置已保存")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置
        
        返回:
            Dict[str, Any]: 配置字典
        """
        return self.config.copy()
    
    def set_config(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        参数:
            key: 配置键
            value: 配置值
        """
        try:
            # 更新配置
            keys = key.split(".")
            current = self.config
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = value
            
            # 保存配置
            self._save_config(self.config)
            
            # 发送配置变更信号
            self.config_changed.emit({key: value})
            
            logger.debug(f"配置已更新: {key} = {value}")
            
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
            raise
    
    def reload_config(self) -> None:
        """重新加载配置"""
        try:
            # 加载配置
            self.config = self._load_config()
            
            # 发送配置重载信号
            self.config_reloaded.emit(self.config)
            
            logger.debug("配置已重载")
            
        except Exception as e:
            logger.error(f"重载配置失败: {e}")
            raise
    
    def reset_config(self) -> None:
        """重置配置为默认值"""
        try:
            # 重置配置
            self.config = self.default_config.copy()
            
            # 保存配置
            self._save_config(self.config)
            
            # 发送配置重载信号
            self.config_reloaded.emit(self.config)
            
            logger.debug("配置已重置")
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            raise
    
    def update_simulator_config(self, simulators: List[Dict[str, Any]]) -> None:
        """更新模拟器配置
        
        Args:
            simulators: 模拟器配置列表
        """
        self.set_config("screen.simulators", simulators)
    
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
            self.config_reloaded.emit(self.config)
            logger.info(f"配置已导入: {import_path}")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False 