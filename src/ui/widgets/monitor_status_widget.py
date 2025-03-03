#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控状态小部件
用于显示监控状态和统计信息
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
from loguru import logger

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGroupBox, QGridLayout, QSizePolicy, QProgressBar,
    QScrollArea, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QColor, QPalette, QFont


class MonitorStatusWidget(QWidget):
    """监控状态小部件类"""
    
    def __init__(self, monitor_manager, parent=None):
        """
        初始化监控状态小部件
        
        参数:
            monitor_manager: 监控管理器实例
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        self.monitor_manager = monitor_manager
        
        # 监听状态更新
        self.monitor_manager.status_updated.connect(self._on_status_updated)
        self.monitor_manager.error_occurred.connect(self._on_error_occurred)
        self.monitor_manager.ship_detected.connect(self._on_ship_detected)
        
        # 当前状态
        self.status = {
            "running": False,
            "paused": False,
            "last_error": "",
            "stats": {
                "started_at": None,
                "last_capture_time": None,
                "captures_count": 0,
                "ship_detections": 0,
                "notifications_sent": 0,
                "last_fps": 0,
                "average_fps": 0,
                "queue_size": 0,
                "max_queue_size": 0,
                "processing_time_ms": 0
            },
            "last_detection": {
                "time": None,
                "system_name": "",
                "ship_count": 0,
                "ships": []
            },
            "simulators": []
        }
        
        # 初始化UI
        self._init_ui()
        
        # 状态更新定时器（每1秒更新一次）
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start()
        
        logger.debug("监控状态小部件初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        
        # 监控状态区域
        status_group = QGroupBox("监控状态")
        status_layout = QGridLayout(status_group)
        
        # 状态指示器
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self._set_status_indicator(False, False)
        status_layout.addWidget(self.status_indicator, 0, 0)
        
        # 状态文本
        self.status_text = QLabel("就绪")
        status_layout.addWidget(self.status_text, 0, 1)
        
        # 运行时间
        self.runtime_label = QLabel("运行时间: 00:00:00")
        status_layout.addWidget(QLabel("运行时间:"), 1, 0)
        status_layout.addWidget(self.runtime_label, 1, 1)
        
        # FPS信息
        self.fps_label = QLabel("0.0")
        status_layout.addWidget(QLabel("当前FPS:"), 2, 0)
        status_layout.addWidget(self.fps_label, 2, 1)
        
        # 平均FPS
        self.avg_fps_label = QLabel("0.0")
        status_layout.addWidget(QLabel("平均FPS:"), 3, 0)
        status_layout.addWidget(self.avg_fps_label, 3, 1)
        
        # 处理队列
        self.queue_bar = QProgressBar()
        self.queue_bar.setRange(0, 100)
        self.queue_bar.setValue(0)
        status_layout.addWidget(QLabel("处理队列:"), 4, 0)
        status_layout.addWidget(self.queue_bar, 4, 1)
        
        # 处理耗时
        self.processing_time_label = QLabel("0 毫秒")
        status_layout.addWidget(QLabel("处理耗时:"), 5, 0)
        status_layout.addWidget(self.processing_time_label, 5, 1)
        
        # 模拟器数量
        self.simulator_count_label = QLabel("0")
        status_layout.addWidget(QLabel("模拟器数量:"), 6, 0)
        status_layout.addWidget(self.simulator_count_label, 6, 1)
        
        # 错误信息
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        status_layout.addWidget(self.error_label, 7, 0, 1, 2)
        
        main_layout.addWidget(status_group)
        
        # 监控统计区域
        stats_group = QGroupBox("监控统计")
        stats_layout = QGridLayout(stats_group)
        
        # 已捕获帧数
        self.captures_count_label = QLabel("0")
        stats_layout.addWidget(QLabel("已捕获帧数:"), 0, 0)
        stats_layout.addWidget(self.captures_count_label, 0, 1)
        
        # 检测到的舰船
        self.ships_count_label = QLabel("0")
        stats_layout.addWidget(QLabel("检测到的舰船:"), 1, 0)
        stats_layout.addWidget(self.ships_count_label, 1, 1)
        
        # 已发送通知
        self.notifications_count_label = QLabel("0")
        stats_layout.addWidget(QLabel("已发送通知:"), 2, 0)
        stats_layout.addWidget(self.notifications_count_label, 2, 1)
        
        # 最近检测时间
        self.last_detection_time_label = QLabel("无")
        stats_layout.addWidget(QLabel("最近检测时间:"), 3, 0)
        stats_layout.addWidget(self.last_detection_time_label, 3, 1)
        
        # 最近检测系统
        self.last_detection_system_label = QLabel("无")
        stats_layout.addWidget(QLabel("最近检测系统:"), 4, 0)
        stats_layout.addWidget(self.last_detection_system_label, 4, 1)
        
        main_layout.addWidget(stats_group)
        
        # 最近检测结果区域
        detection_group = QGroupBox("最近检测结果")
        detection_layout = QVBoxLayout(detection_group)
        
        # 无检测结果提示
        self.no_detection_label = QLabel("暂无检测结果")
        self.no_detection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detection_layout.addWidget(self.no_detection_label)
        
        # 检测结果表格
        self.detection_table = QGridLayout()
        self.detection_table.addWidget(QLabel("舰船"), 0, 0)
        self.detection_table.addWidget(QLabel("驾驶员"), 0, 1)
        self.detection_table.addWidget(QLabel("军团"), 0, 2)
        
        # 添加表格到滚动区域
        detection_scroll = QScrollArea()
        detection_scroll.setWidgetResizable(True)
        detection_container = QWidget()
        detection_container.setLayout(self.detection_table)
        detection_scroll.setWidget(detection_container)
        detection_scroll.setMinimumHeight(150)
        detection_layout.addWidget(detection_scroll)
        
        main_layout.addWidget(detection_group)
        
        # 动态调整各组大小
        main_layout.setStretch(0, 2)  # 状态区域
        main_layout.setStretch(1, 1)  # 统计区域
        main_layout.setStretch(2, 3)  # 检测结果区域
    
    def _set_status_indicator(self, running, paused):
        """
        设置状态指示器
        
        参数:
            running: 是否运行中
            paused: 是否暂停
        """
        palette = self.status_indicator.palette()
        if running:
            if paused:
                # 黄色表示暂停
                color = QColor(255, 165, 0)
            else:
                # 绿色表示运行中
                color = QColor(0, 255, 0)
        else:
            # 灰色表示停止
            color = QColor(150, 150, 150)
        
        palette.setColor(QPalette.ColorRole.Window, color)
        self.status_indicator.setAutoFillBackground(True)
        self.status_indicator.setPalette(palette)
    
    def _on_status_updated(self, status):
        """
        状态更新事件处理
        
        参数:
            status: 新的状态字典
        """
        self.status = status
        self._update_display()
    
    def _on_error_occurred(self, error_msg):
        """
        错误发生事件处理
        
        参数:
            error_msg: 错误消息
        """
        self.status["last_error"] = error_msg
        self.error_label.setText(error_msg)
        self.error_label.show()
    
    def _on_ship_detected(self, detection_data):
        """
        舰船检测事件处理
        
        参数:
            detection_data: 检测数据
        """
        # 更新最近检测数据
        self.status["last_detection"] = detection_data
        
        # 更新检测计数
        self.status["stats"]["ship_detections"] += len(detection_data["ships"])
        
        # 更新显示
        self._update_detection_display()
    
    def _update_display(self):
        """更新显示"""
        try:
            # 更新运行状态
            self.status_text.setText("监控中" if self.status.get("running", False) else "就绪")
            self._set_status_indicator(self.status.get("running", False), self.status.get("paused", False))
            
            # 更新统计信息
            stats = self.status.get("stats", {})
            self.fps_label.setText(f"FPS: {stats.get('last_fps', 0.0):.1f}")
            self.avg_fps_label.setText(f"平均FPS: {stats.get('average_fps', 0.0):.1f}")
            self.captures_count_label.setText(str(stats.get("captures_count", 0)))
            self.ships_count_label.setText(str(stats.get("ship_detections", 0)))
            self.notifications_count_label.setText(str(stats.get("notifications_sent", 0)))
            
            # 更新运行时间
            started_at = stats.get("started_at")
            if started_at:
                elapsed = datetime.now() - started_at
                hours = elapsed.total_seconds() // 3600
                minutes = (elapsed.total_seconds() % 3600) // 60
                seconds = elapsed.total_seconds() % 60
                self.runtime_label.setText(f"运行时间: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            else:
                self.runtime_label.setText("运行时间: 00:00:00")
            
            # 更新队列状态
            max_queue_size = stats.get("max_queue_size", 0)
            if max_queue_size > 0:
                queue_percent = (stats.get("queue_size", 0) / max_queue_size) * 100
            else:
                queue_percent = 0
            
            self.queue_bar.setRange(0, max_queue_size)
            self.queue_bar.setValue(stats.get("queue_size", 0))
            
            # 设置队列进度条颜色
            if queue_percent > 80:
                self.queue_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            elif queue_percent > 50:
                self.queue_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
            else:
                self.queue_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            
            # 更新处理时间
            self.processing_time_label.setText(f"处理耗时: {stats.get('processing_time_ms', 0.0):.1f} 毫秒")
            
            # 更新模拟器数量
            simulator_count = len(self.status.get("simulators", []))
            self.simulator_count_label.setText(str(simulator_count))
            
            # 更新最近检测信息
            last_detection_time = self.status.get("last_detection", {}).get("time")
            if last_detection_time:
                if isinstance(last_detection_time, str):
                    last_detection_time = datetime.fromisoformat(last_detection_time)
                
                time_str = last_detection_time.strftime("%Y-%m-%d %H:%M:%S")
                self.last_detection_time_label.setText(time_str)
            else:
                self.last_detection_time_label.setText("无")
            
            system_name = self.status.get("last_detection", {}).get("system_name")
            if system_name:
                self.last_detection_system_label.setText(system_name)
            else:
                self.last_detection_system_label.setText("无")
            
            # 更新检测结果
            self._update_detection_display()
            
        except Exception as e:
            logger.error(f"更新状态显示时出错: {e}")
    
    def _update_detection_display(self):
        """更新检测结果显示"""
        try:
            # 获取检测数据
            last_detection = self.status.get("last_detection", {})
            ships = last_detection.get("ships", [])
            
            # 清空表格（保留表头）
            for i in reversed(range(1, self.detection_table.rowCount())):
                for j in range(self.detection_table.columnCount()):
                    item = self.detection_table.itemAtPosition(i, j)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            widget.deleteLater()
            
            # 显示或隐藏无检测结果提示
            if not ships:
                self.no_detection_label.show()
                return
            else:
                self.no_detection_label.hide()
            
            # 添加舰船信息
            for i, ship in enumerate(ships):
                row = i + 1
                
                # 舰船类型
                ship_label = QLabel(ship.get("ship_type", "未知"))
                self.detection_table.addWidget(ship_label, row, 0)
                
                # 驾驶员
                pilot_label = QLabel(ship.get("player_name", "未知"))
                self.detection_table.addWidget(pilot_label, row, 1)
                
                # 军团
                corp_label = QLabel(ship.get("corporation", "未知"))
                self.detection_table.addWidget(corp_label, row, 2)
        except Exception as e:
            logger.error(f"更新检测结果显示时出错: {e}")
            self.no_detection_label.show() 