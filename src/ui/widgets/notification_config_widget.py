#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知配置小部件
用于配置通知推送参数
"""

import sys
import os
from pathlib import Path
from loguru import logger
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QSpinBox, QGroupBox, QFormLayout, QCheckBox,
    QComboBox, QTabWidget, QMessageBox, QTextEdit, QListWidget,
    QListWidgetItem, QToolButton, QSizePolicy, QInputDialog,
    QSlider
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon


class NotificationConfigWidget(QWidget):
    """通知配置小部件类"""
    
    def __init__(self, config_manager, parent=None):
        """
        初始化通知配置小部件
        
        参数:
            config_manager: 配置管理器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = self._get_notification_config()
        
        # 监听配置变更
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # 初始化UI
        self._init_ui()
        
        logger.debug("通知配置小部件初始化完成")
    
    def _get_notification_config(self):
        """获取通知配置"""
        config = self.config_manager.get_config()
        return config.get("notification", {})
    
    def _init_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        
        # 通知基本设置
        basic_group = QGroupBox("通知基本设置")
        basic_layout = QFormLayout(basic_group)
        
        # 通知方式
        self.method_combo = QComboBox()
        self.method_combo.addItems(["system", "custom"])
        self.method_combo.setCurrentText(self.config.get("method", "system"))
        self.method_combo.currentTextChanged.connect(
            lambda v: self._update_config("method", v)
        )
        basic_layout.addRow("通知方式:", self.method_combo)
        
        # 声音通知
        self.sound_check = QCheckBox()
        self.sound_check.setChecked(self.config.get("sound", True))
        self.sound_check.toggled.connect(
            lambda v: self._update_config("sound", v)
        )
        basic_layout.addRow("启用声音通知:", self.sound_check)
        
        # 声音音量
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.config.get("volume", 0.7) * 100))
        self.volume_slider.valueChanged.connect(
            lambda v: self._update_config("volume", v / 100.0)
        )
        basic_layout.addRow("声音音量:", self.volume_slider)
        
        # 弹窗通知
        self.popup_check = QCheckBox()
        self.popup_check.setChecked(self.config.get("popup", True))
        self.popup_check.toggled.connect(
            lambda v: self._update_config("popup", v)
        )
        basic_layout.addRow("启用弹窗通知:", self.popup_check)
        
        # 弹窗显示时间
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(self.config.get("duration", 5))
        self.duration_spin.setSuffix(" 秒")
        self.duration_spin.valueChanged.connect(
            lambda v: self._update_config("duration", v)
        )
        basic_layout.addRow("弹窗显示时间:", self.duration_spin)
        
        main_layout.addWidget(basic_group)
        main_layout.addStretch()
    
    def _update_config(self, key: str, value: any):
        """
        更新配置
        
        参数:
            key: 配置键
            value: 配置值
        """
        try:
            # 获取当前配置
            current_config = self._get_notification_config()
            
            # 更新配置
            current_config[key] = value
            self.config_manager.set_config("notification", current_config)
            
            # 保存配置
            self.config_manager.save_config()
            
            logger.debug(f"配置已更新: notification.{key} = {value}")
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            # 恢复UI状态
            self._update_ui_state()
    
    def _on_config_changed(self, key: str, config: dict):
        """配置变更处理
        
        Args:
            key: 配置键路径
            config: 更新后的配置
        """
        try:
            if not isinstance(config, dict):
                logger.error(f"不支持的配置类型: {type(config)}")
                return

            # 更新配置
            self.config = config
            self._update_ui_state()
            logger.debug("通知配置已更新")
        except Exception as e:
            logger.error(f"更新配置时出错: {e}")
            self.config = self._get_default_config()
            self._update_ui_state()
    
    def _update_ui_state(self):
        """更新UI状态"""
        try:
            if not isinstance(self.config, dict):
                logger.error(f"配置类型错误: {type(self.config)}")
                self.config = self._get_default_config()

            notification_config = self.config.get("notification", {})
            if not notification_config:
                logger.error("未找到通知配置")
                notification_config = self._get_default_config()["notification"]

            # 更新UI控件
            self.method_combo.setCurrentText(notification_config.get("method", "system"))
            self.sound_check.setChecked(notification_config.get("sound", True))
            self.volume_slider.setValue(int(notification_config.get("volume", 0.7) * 100))
            self.popup_check.setChecked(notification_config.get("popup", True))
            self.duration_spin.setValue(notification_config.get("duration", 5))

            # 更新控件状态
            self._update_controls_state()
            logger.debug("通知配置UI状态已更新")
        except Exception as e:
            logger.error(f"更新UI状态时出错: {e}")
            self.config = self._get_default_config()
            self._update_controls_state()
    
    def _update_controls_state(self):
        """更新控件状态"""
        try:
            # 根据通知方式更新控件状态
            method = self.method_combo.currentText()
            self.sound_check.setEnabled(method == "custom")
            self.volume_slider.setEnabled(method == "custom")
            self.popup_check.setEnabled(method == "custom")
            self.duration_spin.setEnabled(method == "custom")
        except Exception as e:
            logger.error(f"更新控件状态时出错: {e}")
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "notification": {
                "method": "system",
                "sound": True,
                "volume": 0.7,
                "popup": True,
                "duration": 5
            }
        }
    
    def showEvent(self, event):
        """
        显示事件处理
        
        参数:
            event: 显示事件
        """
        super().showEvent(event)
        
        # 显示窗口时更新UI状态
        self._update_ui_state() 