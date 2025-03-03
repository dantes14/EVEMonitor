#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控状态组件
"""

import psutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from loguru import logger

from src.config.config_manager import ConfigManager


class MonitorStatusWidget(QWidget):
    """监控状态组件"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化监控状态组件
        
        参数:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # 初始化UI
        self._init_ui()
        
        # 创建定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # 每秒更新一次
        
        logger.debug("监控状态组件初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建状态信息区域
        status_layout = QHBoxLayout()
        
        # 添加状态标签
        self.status_label = QLabel("状态：未开始")
        status_layout.addWidget(self.status_label)
        
        # 添加CPU使用率进度条
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.cpu_progress.setFormat("CPU: %p%")
        status_layout.addWidget(self.cpu_progress)
        
        # 添加内存使用率进度条
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.memory_progress.setFormat("内存: %p%")
        status_layout.addWidget(self.memory_progress)
        
        status_layout.addStretch()
        
        # 添加刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._update_status)
        status_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(status_layout)
        
        # 创建监控数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "时间", "区域", "识别文本", "置信度", "状态"
        ])
        
        # 设置表格列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        main_layout.addWidget(self.table)
    
    def _update_status(self):
        """
        更新状态信息
        """
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_progress.setValue(int(cpu_percent))
            
            # 获取内存使用率
            memory = psutil.virtual_memory()
            self.memory_progress.setValue(int(memory.percent))
            
            # 设置进度条颜色
            self._update_progress_bar_color(self.cpu_progress, cpu_percent)
            self._update_progress_bar_color(self.memory_progress, memory.percent)
            
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    def _update_progress_bar_color(self, progress_bar: QProgressBar, value: float):
        """
        根据值更新进度条颜色
        
        参数:
            progress_bar: 进度条组件
            value: 当前值
        """
        if value >= 80:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif value >= 60:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
    
    def start_monitoring(self):
        """开始监控"""
        self.status_label.setText("状态：监控中")
        self.refresh_button.setEnabled(False)
    
    def stop_monitoring(self):
        """停止监控"""
        self.status_label.setText("状态：已停止")
        self.refresh_button.setEnabled(True)
    
    def add_monitor_data(self, time, region, text, confidence, status):
        """
        添加监控数据
        
        参数:
            time: 时间
            region: 区域
            text: 识别文本
            confidence: 置信度
            status: 状态
        """
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 格式化时间
            if isinstance(time, datetime):
                time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = str(time)
            
            # 格式化区域
            if isinstance(region, dict):
                region_str = f"{region.get('x', 0)}, {region.get('y', 0)}"
            else:
                region_str = str(region)
            
            # 格式化置信度
            confidence_str = f"{float(confidence):.2f}%"
            
            # 设置表格项
            self.table.setItem(row, 0, QTableWidgetItem(time_str))
            self.table.setItem(row, 1, QTableWidgetItem(region_str))
            self.table.setItem(row, 2, QTableWidgetItem(text))
            self.table.setItem(row, 3, QTableWidgetItem(confidence_str))
            self.table.setItem(row, 4, QTableWidgetItem(status))
            
            # 设置状态颜色
            status_item = self.table.item(row, 4)
            if status == "成功":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "警告":
                status_item.setForeground(Qt.GlobalColor.yellow)
            elif status == "错误":
                status_item.setForeground(Qt.GlobalColor.red)
            
            # 滚动到最新行
            self.table.scrollToBottom()
            
            # 限制表格行数
            max_rows = self.config.get("monitor", {}).get("max_table_rows", 1000)
            while self.table.rowCount() > max_rows:
                self.table.removeRow(0)
                
        except Exception as e:
            logger.error(f"添加监控数据失败: {e}") 