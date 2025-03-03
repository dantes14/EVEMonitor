#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知配置组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QSpinBox, QComboBox,
    QLineEdit, QPushButton, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.config.config_manager import ConfigManager


class NotificationConfigWidget(QWidget):
    """通知配置组件"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化通知配置组件
        
        参数:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # 初始化UI
        self._init_ui()
        
        logger.debug("通知配置组件初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建通知方式组
        method_group = QGroupBox("通知方式")
        method_layout = QFormLayout(method_group)
        
        # 系统通知
        self.system_notify_check = QCheckBox("启用系统通知")
        self.system_notify_check.setChecked(
            self.config.get("notification", {}).get("system_notify", True)
        )
        self.system_notify_check.stateChanged.connect(
            lambda state: self.config_manager.set_config(
                "notification.system_notify",
                bool(state)
            )
        )
        method_layout.addRow("系统通知:", self.system_notify_check)
        
        # 声音提醒
        self.sound_notify_check = QCheckBox("启用声音提醒")
        self.sound_notify_check.setChecked(
            self.config.get("notification", {}).get("sound_notify", True)
        )
        self.sound_notify_check.stateChanged.connect(
            lambda state: self.config_manager.set_config(
                "notification.sound_notify",
                bool(state)
            )
        )
        method_layout.addRow("声音提醒:", self.sound_notify_check)
        
        # 声音文件选择
        self.sound_file_edit = QLineEdit(
            self.config.get("notification", {}).get("sound_file", "")
        )
        self.sound_file_edit.textChanged.connect(
            lambda text: self.config_manager.set_config(
                "notification.sound_file",
                text
            )
        )
        method_layout.addRow("声音文件:", self.sound_file_edit)
        
        # 选择声音文件按钮
        self.select_sound_button = QPushButton("选择文件")
        self.select_sound_button.clicked.connect(self._select_sound_file)
        method_layout.addRow("", self.select_sound_button)
        
        main_layout.addWidget(method_group)
        
        # 创建通知内容组
        content_group = QGroupBox("通知内容")
        content_layout = QFormLayout(content_group)
        
        # 通知标题
        self.title_edit = QLineEdit(
            self.config.get("notification", {}).get("title", "EVEMonitor")
        )
        self.title_edit.textChanged.connect(
            lambda text: self.config_manager.set_config(
                "notification.title",
                text
            )
        )
        content_layout.addRow("通知标题:", self.title_edit)
        
        # 通知内容模板
        self.content_template_edit = QLineEdit(
            self.config.get("notification", {}).get("content_template", "")
        )
        self.content_template_edit.textChanged.connect(
            lambda text: self.config_manager.set_config(
                "notification.content_template",
                text
            )
        )
        content_layout.addRow("内容模板:", self.content_template_edit)
        
        main_layout.addWidget(content_group)
        
        # 创建通知频率组
        frequency_group = QGroupBox("通知频率")
        frequency_layout = QFormLayout(frequency_group)
        
        # 最小通知间隔
        self.min_interval_spin = QSpinBox()
        self.min_interval_spin.setRange(0, 3600)
        self.min_interval_spin.setValue(
            self.config.get("notification", {}).get("min_interval", 60)
        )
        self.min_interval_spin.valueChanged.connect(
            lambda value: self.config_manager.set_config(
                "notification.min_interval",
                value
            )
        )
        frequency_layout.addRow("最小通知间隔(秒):", self.min_interval_spin)
        
        # 通知级别
        self.level_combo = QComboBox()
        self.level_combo.addItems(["低", "中", "高"])
        level_map = {"低": "low", "中": "medium", "高": "high"}
        current_level = self.config.get("notification", {}).get("level", "medium")
        self.level_combo.setCurrentText(
            {v: k for k, v in level_map.items()}[current_level]
        )
        self.level_combo.currentTextChanged.connect(
            lambda text: self.config_manager.set_config(
                "notification.level",
                level_map[text]
            )
        )
        frequency_layout.addRow("通知级别:", self.level_combo)
        
        main_layout.addWidget(frequency_group)
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def _select_sound_file(self):
        """选择声音文件"""
        try:
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择声音文件",
                "",
                "音频文件 (*.wav *.mp3 *.ogg);;所有文件 (*.*)"
            )
            
            if file_path:
                # 更新配置
                self.config_manager.set_config(
                    "notification.sound_file",
                    file_path
                )
                
                # 更新UI
                self.sound_file_edit.setText(file_path)
                
                logger.debug(f"已选择声音文件: {file_path}")
                
                # 显示成功消息
                QMessageBox.information(
                    self,
                    "成功",
                    "声音文件已更新"
                )
                
        except Exception as e:
            logger.error(f"选择声音文件时出错: {e}")
            QMessageBox.warning(
                self,
                "错误",
                f"选择声音文件失败: {str(e)}"
            ) 