#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
布局预览小部件
用于预览模拟器布局效果
"""

import sys
import os
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush


class LayoutPreviewWidget(QWidget):
    """布局预览小部件类"""
    
    def __init__(self, config, parent=None):
        """
        初始化布局预览小部件
        
        参数:
            config: 配置字典
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.config = config
        
        # 设置最小尺寸
        self.setMinimumSize(400, 300)
        
        logger.debug("布局预览小部件初始化完成")
    
    def paintEvent(self, event):
        """
        绘制事件处理
        
        参数:
            event: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取预览区域尺寸
        preview_width = self.width()
        preview_height = self.height()
        
        # 绘制背景
        painter.fillRect(0, 0, preview_width, preview_height, QColor(240, 240, 240))
        
        # 绘制边框
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(0, 0, preview_width - 1, preview_height - 1)
        
        # 根据布局模式绘制预览
        layout_mode = self.config.get("screen", {}).get("layout_mode", "grid")
        if layout_mode == "grid":
            self._draw_grid_layout(painter, preview_width, preview_height)
        else:
            self._draw_custom_layout(painter, preview_width, preview_height)
    
    def _draw_grid_layout(self, painter, width, height):
        """
        绘制网格布局预览
        
        参数:
            painter: 画笔
            width: 预览区域宽度
            height: 预览区域高度
        """
        # 获取网格布局参数
        rows = self.config.get("screen", {}).get("grid_layout", {}).get("rows", 2)
        cols = self.config.get("screen", {}).get("grid_layout", {}).get("columns", 2)
        spacing_x = self.config.get("screen", {}).get("grid_layout", {}).get("spacing_x", 10)
        spacing_y = self.config.get("screen", {}).get("grid_layout", {}).get("spacing_y", 10)
        
        # 计算网格尺寸
        grid_width = (width - (cols + 1) * spacing_x) / cols
        grid_height = (height - (rows + 1) * spacing_y) / rows
        
        # 绘制网格
        for row in range(rows):
            for col in range(cols):
                # 计算网格位置
                x = spacing_x + col * (grid_width + spacing_x)
                y = spacing_y + row * (grid_height + spacing_y)
                
                # 绘制网格边框
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawRect(int(x), int(y), int(grid_width), int(grid_height))
                
                # 绘制网格编号
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(
                    int(x + 5),
                    int(y + 20),
                    f"模拟器 {row * cols + col + 1}"
                )
    
    def _draw_custom_layout(self, painter, width, height):
        """
        绘制自定义布局预览
        
        参数:
            painter: 画笔
            width: 预览区域宽度
            height: 预览区域高度
        """
        # 获取模拟器列表
        simulators = self.config.get("screen", {}).get("custom_layout", {}).get("simulators", [])
        
        # 计算缩放比例
        scale_x = width / 1920  # 假设原始分辨率为1920x1080
        scale_y = height / 1080
        
        # 绘制每个模拟器
        for simulator in simulators:
            # 计算缩放后的位置和大小
            x = simulator.get("x", 0) * scale_x
            y = simulator.get("y", 0) * scale_y
            w = simulator.get("width", 400) * scale_x
            h = simulator.get("height", 300) * scale_y
            
            # 绘制模拟器边框
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawRect(int(x), int(y), int(w), int(h))
            
            # 绘制模拟器编号
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                int(x + 5),
                int(y + 20),
                f"模拟器 {simulator.get('id', '?')}"
            ) 