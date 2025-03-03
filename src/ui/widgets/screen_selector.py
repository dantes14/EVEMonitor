#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕选择器小部件
用于可视化选择监控屏幕区域
"""

import sys
import os
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QScreen,
    QMouseEvent, QGuiApplication, QCursor
)


class ScreenSelector(QDialog):
    """屏幕选择器类"""
    
    def __init__(self, parent=None):
        """
        初始化屏幕选择器
        
        参数:
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowTitle("选择屏幕区域")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 选择状态
        self.selecting = False
        self.start_point = QPoint()
        self.current_point = QPoint()
        self.selected_rect = QRect()
        self.initial_rect = None
        
        # 初始化UI
        self._init_ui()
        
        # 全屏显示
        self._set_fullscreen()
        
        logger.debug("屏幕选择器初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 显示选择区域信息的标签
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            color: white;
            padding: 5px;
            border-radius: 3px;
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFixedSize(300, 30)
        self.info_label.hide()
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        
        self.confirm_btn = QPushButton("确认选择")
        self.confirm_btn.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 5px 15px;
            border: none;
            border-radius: 3px;
        """)
        self.confirm_btn.clicked.connect(self.accept)
        self.confirm_btn.hide()
        buttons_layout.addWidget(self.confirm_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            background-color: #F44336;
            color: white;
            padding: 5px 15px;
            border: none;
            border-radius: 3px;
        """)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        main_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # 添加标签到窗口
        self.info_label.setParent(self)
        
        # 设置提示文本
        self.setToolTip("按住鼠标左键拖动以选择区域")
        
        # 使用ESC键关闭窗口
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _set_fullscreen(self):
        """设置全屏显示"""
        # 获取主屏幕
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # 设置窗口大小为全屏
        self.setGeometry(screen_geometry)
    
    def set_initial_rect(self, x, y, width, height):
        """
        设置初始选择矩形
        
        参数:
            x: 矩形左上角X坐标
            y: 矩形左上角Y坐标
            width: 矩形宽度
            height: 矩形高度
        """
        self.initial_rect = QRect(x, y, width, height)
        self.selected_rect = self.initial_rect
        
        # 显示确认按钮
        self.confirm_btn.show()
        
        # 更新信息标签
        self._update_info_label()
    
    def get_selected_rect(self):
        """获取选择的矩形区域"""
        return self.selected_rect
    
    def _update_info_label(self):
        """更新信息标签"""
        if self.selected_rect.isValid():
            # 设置标签文本
            self.info_label.setText(
                f"X: {self.selected_rect.x()}, Y: {self.selected_rect.y()}, "
                f"宽: {self.selected_rect.width()}, 高: {self.selected_rect.height()}"
            )
            
            # 显示信息标签
            self.info_label.show()
            
            # 将标签放置在选择区域上方
            label_pos = QPoint(
                self.selected_rect.x() + (self.selected_rect.width() - self.info_label.width()) // 2,
                self.selected_rect.y() - self.info_label.height() - 10
            )
            
            # 确保标签不超出屏幕边界
            if label_pos.y() < 0:
                label_pos.setY(self.selected_rect.y() + self.selected_rect.height() + 10)
            if label_pos.x() < 0:
                label_pos.setX(0)
            if label_pos.x() + self.info_label.width() > self.width():
                label_pos.setX(self.width() - self.info_label.width())
            
            self.info_label.move(label_pos)
        else:
            self.info_label.hide()
    
    def mousePressEvent(self, event):
        """
        鼠标按下事件
        
        参数:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.start_point = event.pos()
            self.current_point = event.pos()
            self.selected_rect = QRect()
            self.confirm_btn.hide()
            self.update()
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件
        
        参数:
            event: 鼠标事件
        """
        if self.selecting:
            self.current_point = event.pos()
            self.selected_rect = QRect(
                QPoint(
                    min(self.start_point.x(), self.current_point.x()),
                    min(self.start_point.y(), self.current_point.y())
                ),
                QPoint(
                    max(self.start_point.x(), self.current_point.x()),
                    max(self.start_point.y(), self.current_point.y())
                )
            )
            self._update_info_label()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件
        
        参数:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            
            # 确保选择区域有效
            if self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                self.confirm_btn.show()
            else:
                self.selected_rect = QRect()
                self.info_label.hide()
            
            self.update()
    
    def keyPressEvent(self, event):
        """
        键盘按下事件
        
        参数:
            event: 键盘事件
        """
        # 按ESC键取消选择
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        
        # 按回车键确认选择
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selected_rect.isValid() and not self.selecting:
                self.accept()
        
        super().keyPressEvent(event)
    
    def paintEvent(self, event):
        """
        绘制事件
        
        参数:
            event: 绘制事件
        """
        painter = QPainter(self)
        
        # 绘制半透明背景
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # 如果有初始矩形且没有开始新的选择，则绘制初始矩形
        if self.initial_rect and not self.selecting and not self.selected_rect.isValid():
            self.selected_rect = self.initial_rect
            self._update_info_label()
        
        # 如果有选择区域，则绘制选择矩形
        if self.selected_rect.isValid():
            # 清除选择区域的背景遮罩
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.drawRect(self.selected_rect)
            
            # 重置合成模式并绘制边框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.selected_rect)
            
            # 绘制边角标记
            corner_size = 10
            corner_color = QColor(0, 120, 215)
            
            painter.setBrush(corner_color)
            
            # 左上角
            painter.drawRect(
                self.selected_rect.left(),
                self.selected_rect.top(),
                corner_size,
                corner_size
            )
            
            # 右上角
            painter.drawRect(
                self.selected_rect.right() - corner_size,
                self.selected_rect.top(),
                corner_size,
                corner_size
            )
            
            # 左下角
            painter.drawRect(
                self.selected_rect.left(),
                self.selected_rect.bottom() - corner_size,
                corner_size,
                corner_size
            )
            
            # 右下角
            painter.drawRect(
                self.selected_rect.right() - corner_size,
                self.selected_rect.bottom() - corner_size,
                corner_size,
                corner_size
            )
        
        # 绘制十字线跟随鼠标
        if self.selecting:
            # 获取鼠标位置
            cursor_pos = QCursor.pos() - self.mapToGlobal(QPoint(0, 0))
            
            # 设置十字线颜色
            painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine))
            
            # 绘制水平线
            painter.drawLine(
                0,
                cursor_pos.y(),
                self.width(),
                cursor_pos.y()
            )
            
            # 绘制垂直线
            painter.drawLine(
                cursor_pos.x(),
                0,
                cursor_pos.x(),
                self.height()
            ) 