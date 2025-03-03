#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕配置小部件
用于配置监控屏幕区域和模拟器布局
"""

import sys
import os
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QGroupBox, QFormLayout, QCheckBox, QComboBox,
    QTabWidget, QScrollArea, QSizePolicy, QGridLayout,
    QSlider, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon, QAction, QPainterPath


class ScreenConfigWidget(QWidget):
    """屏幕配置小部件类"""
    
    def __init__(self, config_manager, parent=None):
        """
        初始化屏幕配置小部件
        
        参数:
            config_manager: 配置管理器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # 监听配置变更
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # 初始化UI
        self._init_ui()
        
        logger.debug("屏幕配置小部件初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 监控区域设置
        monitor_group = QGroupBox("监控区域设置")
        monitor_layout = QFormLayout(monitor_group)
        
        # 监控模式选择
        self.monitor_mode_combo = QComboBox()
        self.monitor_mode_combo.addItems(["全屏", "自定义区域", "网格布局"])
        self.monitor_mode_combo.setCurrentText(self.config.get("screen", {}).get("monitor_mode", "全屏"))
        self.monitor_mode_combo.currentTextChanged.connect(self._on_monitor_mode_changed)
        monitor_layout.addRow("监控模式:", self.monitor_mode_combo)
        
        # 自定义区域设置
        self.custom_region_group = QGroupBox("自定义区域")
        custom_region_layout = QFormLayout(self.custom_region_group)
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.setValue(self.config.get("screen", {}).get("custom_region", {}).get("x", 0))
        self.x_spin.valueChanged.connect(self._on_custom_region_changed)
        custom_region_layout.addRow("X坐标:", self.x_spin)
        
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.setValue(self.config.get("screen", {}).get("custom_region", {}).get("y", 0))
        self.y_spin.valueChanged.connect(self._on_custom_region_changed)
        custom_region_layout.addRow("Y坐标:", self.y_spin)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 9999)
        self.width_spin.setValue(self.config.get("screen", {}).get("custom_region", {}).get("width", 1920))
        self.width_spin.valueChanged.connect(self._on_custom_region_changed)
        custom_region_layout.addRow("宽度:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 9999)
        self.height_spin.setValue(self.config.get("screen", {}).get("custom_region", {}).get("height", 1080))
        self.height_spin.valueChanged.connect(self._on_custom_region_changed)
        custom_region_layout.addRow("高度:", self.height_spin)
        
        monitor_layout.addRow(self.custom_region_group)
        
        # 网格布局设置
        self.grid_layout_group = QGroupBox("网格布局")
        grid_layout = QFormLayout(self.grid_layout_group)
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 10)
        self.rows_spin.setValue(self.config.get("screen", {}).get("grid_layout", {}).get("rows", 2))
        self.rows_spin.valueChanged.connect(self._on_grid_layout_changed)
        grid_layout.addRow("行数:", self.rows_spin)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(self.config.get("screen", {}).get("grid_layout", {}).get("columns", 2))
        self.cols_spin.valueChanged.connect(self._on_grid_layout_changed)
        grid_layout.addRow("列数:", self.cols_spin)
        
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 100)
        self.spacing_spin.setValue(self.config.get("screen", {}).get("grid_layout", {}).get("spacing", 10))
        self.spacing_spin.valueChanged.connect(self._on_grid_layout_changed)
        grid_layout.addRow("间距:", self.spacing_spin)
        
        monitor_layout.addRow(self.grid_layout_group)
        
        layout.addWidget(monitor_group)
        layout.addStretch()
        
        # 初始化UI状态
        self._update_ui_state()
    
    def _update_ui_state(self):
        """更新UI状态"""
        try:
            # 更新监控模式
            mode = self.config_manager.get_config("screen.monitor_mode")
            if isinstance(mode, str):
                self.monitor_mode_combo.setCurrentText(mode)
                
                # 更新自定义区域和网格布局的启用状态
                self.custom_region_group.setEnabled(mode == "自定义区域")
                self.grid_layout_group.setEnabled(mode == "网格布局")
                
                # 更新自定义区域的值
                custom_region = self.config_manager.get_config("screen.custom_region")
                if isinstance(custom_region, dict):
                    self.x_spin.setValue(custom_region.get("x", 0))
                    self.y_spin.setValue(custom_region.get("y", 0))
                    self.width_spin.setValue(custom_region.get("width", 1920))
                    self.height_spin.setValue(custom_region.get("height", 1080))
                
                # 更新网格布局的值
                grid_layout = self.config_manager.get_config("screen.grid_layout")
                if isinstance(grid_layout, dict):
                    self.rows_spin.setValue(grid_layout.get("rows", 2))
                    self.cols_spin.setValue(grid_layout.get("columns", 2))
                    self.spacing_spin.setValue(grid_layout.get("spacing", 10))
        except Exception as e:
            logger.error(f"更新UI状态失败: {str(e)}")
    
    def _on_monitor_mode_changed(self, mode):
        """监控模式变更处理"""
        try:
            # 更新配置
            self.config_manager.set_config("screen.monitor_mode", mode)
            
            # 更新UI状态
            self._update_ui_state()
            
            logger.debug(f"监控模式已更改为: {mode}")
        except Exception as e:
            logger.error(f"更新监控模式失败: {str(e)}")
    
    def _on_custom_region_changed(self):
        """自定义区域变更处理"""
        try:
            # 更新配置
            custom_region = {
                "x": self.x_spin.value(),
                "y": self.y_spin.value(),
                "width": self.width_spin.value(),
                "height": self.height_spin.value()
            }
            self.config_manager.set_config("screen.custom_region", custom_region)
            
            logger.debug("自定义区域已更新")
        except Exception as e:
            logger.error(f"更新自定义区域失败: {str(e)}")
    
    def _on_grid_layout_changed(self):
        """网格布局变更处理"""
        try:
            # 更新配置
            grid_layout = {
                "rows": self.rows_spin.value(),
                "columns": self.cols_spin.value(),
                "spacing": self.spacing_spin.value()
            }
            self.config_manager.set_config("screen.grid_layout", grid_layout)
            
            logger.debug("网格布局已更新")
        except Exception as e:
            logger.error(f"更新网格布局失败: {str(e)}")
    
    def _on_config_changed(self, key, value):
        """配置变更处理"""
        try:
            if key == "screen.monitor_mode":
                # 更新监控模式
                if isinstance(value, str):
                    self.monitor_mode_combo.setCurrentText(value)
                    self.custom_region_group.setEnabled(value == "自定义区域")
                    self.grid_layout_group.setEnabled(value == "网格布局")
            elif key == "screen.custom_region":
                # 更新自定义区域
                if isinstance(value, dict):
                    self.x_spin.setValue(value.get("x", 0))
                    self.y_spin.setValue(value.get("y", 0))
                    self.width_spin.setValue(value.get("width", 1920))
                    self.height_spin.setValue(value.get("height", 1080))
            elif key == "screen.grid_layout":
                # 更新网格布局
                if isinstance(value, dict):
                    self.rows_spin.setValue(value.get("rows", 2))
                    self.cols_spin.setValue(value.get("columns", 2))
                    self.spacing_spin.setValue(value.get("spacing", 10))
            elif key == "screen.grid_layout.rows":
                # 更新行数
                if isinstance(value, (int, float)):
                    self.rows_spin.setValue(int(value))
            elif key == "screen.grid_layout.columns":
                # 更新列数
                if isinstance(value, (int, float)):
                    self.cols_spin.setValue(int(value))
            elif key == "screen.grid_layout.spacing":
                # 更新间距
                if isinstance(value, (int, float)):
                    self.spacing_spin.setValue(int(value))
            
            logger.debug(f"配置已更新: {key}")
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")


class LayoutPreviewWidget(QWidget):
    """布局预览小部件"""
    
    def __init__(self, config, parent=None):
        """
        初始化布局预览小部件
        
        参数:
            config: 配置字典
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.config = self._process_config(config)
        self.setMinimumSize(300, 200)
        
        # 设置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(palette)
    
    def _process_config(self, config):
        """
        处理配置数据
        
        参数:
            config: 配置数据
            
        返回:
            dict: 处理后的配置字典
        """
        if isinstance(config, str):
            try:
                import json
                return json.loads(config)
            except json.JSONDecodeError:
                logger.error(f"无法解析配置字符串: {config}")
                return {}
        elif isinstance(config, dict):
            return config
        else:
            logger.error(f"不支持的配置类型: {type(config)}")
            return {}
    
    def update_config(self, config):
        """
        更新配置
        
        参数:
            config: 新的配置数据
        """
        self.config = self._process_config(config)
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """
        绘制事件
        
        参数:
            event: 绘制事件
        """
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 确保配置是字典类型
        if not isinstance(self.config, dict):
            logger.error(f"配置类型错误: {type(self.config)}")
            return
            
        # 获取屏幕配置
        screen_config = self.config.get("screen", {})
        if not screen_config:
            logger.error("未找到屏幕配置")
            return
            
        # 绘制监控区域边框
        monitor_area = screen_config.get("monitor_area", {})
        if not monitor_area:
            logger.error("未找到监控区域配置")
            return
        
        # 计算缩放比例
        scale_x = self.width() / monitor_area["width"]
        scale_y = self.height() / monitor_area["height"]
        scale = min(scale_x, scale_y) * 0.9  # 留出一些边距
        
        # 计算偏移量使图像居中
        offset_x = (self.width() - monitor_area["width"] * scale) / 2
        offset_y = (self.height() - monitor_area["height"] * scale) / 2
        
        # 绘制监控区域
        monitor_rect = QRect(
            int(offset_x),
            int(offset_y),
            int(monitor_area["width"] * scale),
            int(monitor_area["height"] * scale)
        )
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(monitor_rect)
        
        # 绘制模拟器
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        
        layout_mode = screen_config.get("layout_mode", "grid")
        if layout_mode == "grid":
            # 网格布局
            grid_layout = screen_config.get("grid_layout", {})
            if not grid_layout:
                logger.error("未找到网格布局配置")
                return
                
            rows = grid_layout.get("rows", 2)
            columns = grid_layout.get("columns", 2)
            spacing_x = grid_layout.get("spacing_x", 10)
            spacing_y = grid_layout.get("spacing_y", 10)
            
            # 计算单个模拟器的大小
            cell_width = (monitor_area["width"] - spacing_x * (columns - 1)) / columns
            cell_height = (monitor_area["height"] - spacing_y * (rows - 1)) / rows
            
            # 绘制网格
            for row in range(rows):
                for col in range(columns):
                    x = monitor_area["x"] + col * (cell_width + spacing_x)
                    y = monitor_area["y"] + row * (cell_height + spacing_y)
                    
                    # 缩放到预览大小
                    preview_x = offset_x + x * scale
                    preview_y = offset_y + y * scale
                    preview_width = cell_width * scale
                    preview_height = cell_height * scale
                    
                    # 绘制模拟器矩形
                    sim_rect = QRect(
                        int(preview_x),
                        int(preview_y),
                        int(preview_width),
                        int(preview_height)
                    )
                    
                    painter.drawRect(sim_rect)
                    
                    # 绘制编号
                    painter.drawText(
                        sim_rect,
                        Qt.AlignmentFlag.AlignCenter,
                        str(row * columns + col + 1)
                    )
        else:
            # 自定义布局
            custom_layout = screen_config.get("custom_layout", {})
            if not custom_layout:
                logger.error("未找到自定义布局配置")
                return
                
            simulators = custom_layout.get("simulators", [])
            if not simulators:
                logger.error("未找到模拟器配置")
                return
                
            for sim in simulators:
                # 缩放到预览大小
                preview_x = offset_x + sim["x"] * scale
                preview_y = offset_y + sim["y"] * scale
                preview_width = sim["width"] * scale
                preview_height = sim["height"] * scale
                
                # 绘制模拟器矩形
                sim_rect = QRect(
                    int(preview_x),
                    int(preview_y),
                    int(preview_width),
                    int(preview_height)
                )
                
                painter.drawRect(sim_rect)
                
                # 绘制编号
                painter.drawText(
                    sim_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    str(sim["id"])
                ) 