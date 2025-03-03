#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块
提供用户界面来控制和配置EVE监视器
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QStatusBar, QMessageBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QSlider, QFileDialog, QSystemTrayIcon,
    QMenu, QSplitter, QFrame, QScrollArea, QSizePolicy, QGridLayout,
    QToolBar, QToolButton, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QSize, QThreadPool, QUrl, pyqtSlot, QSettings
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor, QFont, QPalette, QDesktopServices

from ..core.monitor_manager import MonitorManager
from .widgets.screen_config_widget import ScreenConfigWidget
from .widgets.monitor_status_widget import MonitorStatusWidget
from .widgets.notification_config_widget import NotificationConfigWidget
from .widgets.ocr_config_widget import OCRConfigWidget


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, config_manager, monitor_manager=None, debug_mode=False):
        """
        初始化主窗口
        
        参数:
            config_manager: 配置管理器实例
            monitor_manager: 监控管理器实例
            debug_mode: 是否为调试模式
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.debug_mode = debug_mode
        
        # 监听配置变更
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # 初始化监控管理器
        self.monitor_manager = monitor_manager or MonitorManager(config_manager)
        self.monitor_manager.monitoring_started.connect(self._on_monitoring_started)
        self.monitor_manager.monitoring_stopped.connect(self._on_monitoring_stopped)
        self.monitor_manager.status_updated.connect(self._on_status_updated)
        self.monitor_manager.error_occurred.connect(self._on_error_occurred)
        
        # 窗口设置
        self.setWindowTitle("EVE监视器")
        self.setMinimumSize(800, 600)
        
        # 加载窗口设置
        self._load_window_settings()
        
        # 设置图标
        # self.setWindowIcon(QIcon("path/to/icon.png"))
        
        # 初始化UI
        self._init_ui()
        
        # 托盘图标
        self._init_tray_icon()
        
        # 状态更新定时器
        self._status_timer = QTimer()
        self._status_timer.setInterval(1000)  # 1秒更新一次
        self._status_timer.timeout.connect(self._update_status_display)
        self._status_timer.start()
        
        # 如果配置了自动启动或最小化启动，执行相应操作
        if self.config.get("ui", {}).get("start_minimized", False):
            self.hide()
            if self.config.get("ui", {}).get("minimize_to_tray", True):
                self.tray_icon.showMessage("EVE监视器", "程序已启动并最小化到托盘", QSystemTrayIcon.MessageIcon.Information, 3000)
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        # 中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 工具栏
        self._init_toolbar()
        
        # 选项卡窗口
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 添加选项卡
        self._init_monitor_tab()
        self._init_config_tab()
        self._init_log_tab()
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态栏组件
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        self.status_bar.addPermanentWidget(QLabel("版本: 1.0.0"))
    
    def _init_toolbar(self):
        """初始化工具栏"""
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setObjectName("mainToolBar")  # 设置对象名称
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)
        
        # 开始监控按钮
        self.start_action = QAction("开始监控", self)
        self.start_action.setObjectName("startAction")  # 设置对象名称
        # self.start_action.setIcon(QIcon("path/to/start_icon.png"))
        self.start_action.triggered.connect(self._on_start_clicked)
        self.toolbar.addAction(self.start_action)
        
        # 停止监控按钮
        self.stop_action = QAction("停止监控", self)
        self.stop_action.setObjectName("stopAction")  # 设置对象名称
        # self.stop_action.setIcon(QIcon("path/to/stop_icon.png"))
        self.stop_action.triggered.connect(self._on_stop_clicked)
        self.stop_action.setEnabled(False)
        self.toolbar.addAction(self.stop_action)
        
        # 暂停/继续监控按钮
        self.pause_action = QAction("暂停监控", self)
        self.pause_action.setObjectName("pauseAction")  # 设置对象名称
        # self.pause_action.setIcon(QIcon("path/to/pause_icon.png"))
        self.pause_action.triggered.connect(self._on_pause_clicked)
        self.pause_action.setEnabled(False)
        self.toolbar.addAction(self.pause_action)
        
        self.toolbar.addSeparator()
        
        # 屏幕配置按钮
        self.screen_config_action = QAction("屏幕配置", self)
        self.screen_config_action.setObjectName("screenConfigAction")  # 设置对象名称
        # self.screen_config_action.setIcon(QIcon("path/to/screen_icon.png"))
        self.screen_config_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.toolbar.addAction(self.screen_config_action)
        
        # 测试推送按钮
        self.test_push_action = QAction("测试推送", self)
        self.test_push_action.setObjectName("testPushAction")  # 设置对象名称
        # self.test_push_action.setIcon(QIcon("path/to/test_icon.png"))
        self.test_push_action.triggered.connect(self._on_test_push_clicked)
        self.toolbar.addAction(self.test_push_action)
        
        self.toolbar.addSeparator()
        
        # 帮助按钮
        self.help_action = QAction("帮助", self)
        self.help_action.setObjectName("helpAction")  # 设置对象名称
        # self.help_action.setIcon(QIcon("path/to/help_icon.png"))
        self.help_action.triggered.connect(self._on_help_clicked)
        self.toolbar.addAction(self.help_action)
        
        # 设置按钮
        self.settings_action = QAction("设置", self)
        self.settings_action.setObjectName("settingsAction")  # 设置对象名称
        # self.settings_action.setIcon(QIcon("path/to/settings_icon.png"))
        self.settings_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.toolbar.addAction(self.settings_action)
    
    def _init_monitor_tab(self):
        """初始化监控选项卡"""
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        
        # 监控状态窗口部件
        self.monitor_status_widget = MonitorStatusWidget(self.config_manager)
        monitor_layout.addWidget(self.monitor_status_widget)
        
        self.tab_widget.addTab(monitor_tab, "监控状态")
    
    def _init_config_tab(self):
        """初始化配置选项卡"""
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        # 配置选项卡窗口
        config_tabs = QTabWidget()
        config_layout.addWidget(config_tabs)
        
        # 屏幕配置选项卡
        self.screen_config_widget = ScreenConfigWidget(self.config_manager)
        config_tabs.addTab(self.screen_config_widget, "屏幕配置")
        
        # OCR配置选项卡
        self.ocr_config_widget = OCRConfigWidget(self.config_manager)
        config_tabs.addTab(self.ocr_config_widget, "OCR配置")
        
        # 通知配置选项卡
        self.notification_config_widget = NotificationConfigWidget(self.config_manager)
        config_tabs.addTab(self.notification_config_widget, "通知配置")
        
        # 高级设置选项卡
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # 定时设置
        timing_group = QGroupBox("定时设置")
        timing_layout = QFormLayout(timing_group)
        
        self.capture_interval_spin = QSpinBox()
        self.capture_interval_spin.setRange(100, 10000)
        self.capture_interval_spin.setSingleStep(100)
        self.capture_interval_spin.setValue(self.config.get("timing", {}).get("capture_interval_ms", 2000))
        self.capture_interval_spin.setSuffix(" 毫秒")
        self.capture_interval_spin.valueChanged.connect(
            lambda value: self.config_manager.set_config("timing.capture_interval_ms", value)
        )
        timing_layout.addRow("截图间隔:", self.capture_interval_spin)
        
        self.processing_timeout_spin = QSpinBox()
        self.processing_timeout_spin.setRange(1000, 30000)
        self.processing_timeout_spin.setSingleStep(500)
        self.processing_timeout_spin.setValue(self.config.get("timing", {}).get("processing_timeout_ms", 5000))
        self.processing_timeout_spin.setSuffix(" 毫秒")
        self.processing_timeout_spin.valueChanged.connect(
            lambda value: self.config_manager.set_config("timing.processing_timeout_ms", value)
        )
        timing_layout.addRow("处理超时:", self.processing_timeout_spin)
        
        self.queue_max_size_spin = QSpinBox()
        self.queue_max_size_spin.setRange(1, 100)
        self.queue_max_size_spin.setValue(self.config.get("timing", {}).get("queue_max_size", 10))
        self.queue_max_size_spin.valueChanged.connect(
            lambda value: self.config_manager.set_config("timing.queue_max_size", value)
        )
        timing_layout.addRow("队列容量:", self.queue_max_size_spin)
        
        advanced_layout.addWidget(timing_group)
        
        # 调试设置
        debug_group = QGroupBox("调试设置")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_enabled_checkbox = QCheckBox("启用调试模式")
        self.debug_enabled_checkbox.setChecked(self.config.get("debug", {}).get("enabled", False))
        self.debug_enabled_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set_config("debug.enabled", state == Qt.CheckState.Checked)
        )
        debug_layout.addRow("", self.debug_enabled_checkbox)
        
        self.save_screenshots_checkbox = QCheckBox("保存截图")
        self.save_screenshots_checkbox.setChecked(self.config.get("debug", {}).get("save_screenshots", False))
        self.save_screenshots_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set_config("debug.save_screenshots", state == Qt.CheckState.Checked)
        )
        debug_layout.addRow("", self.save_screenshots_checkbox)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.config.get("debug", {}).get("log_level", "INFO"))
        self.log_level_combo.currentTextChanged.connect(
            lambda v: self.config_manager.update_config("debug.log_level", v)
        )
        debug_layout.addRow("日志级别:", self.log_level_combo)
        
        advanced_layout.addWidget(debug_group)
        
        # UI设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        
        self.minimize_to_tray_checkbox = QCheckBox("最小化到托盘")
        self.minimize_to_tray_checkbox.setChecked(self.config.get("ui", {}).get("minimize_to_tray", True))
        self.minimize_to_tray_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set_config("ui.minimize_to_tray", state == Qt.CheckState.Checked)
        )
        ui_layout.addRow("", self.minimize_to_tray_checkbox)
        
        self.start_minimized_checkbox = QCheckBox("启动时最小化")
        self.start_minimized_checkbox.setChecked(self.config.get("ui", {}).get("start_minimized", False))
        self.start_minimized_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set_config("ui.start_minimized", state == Qt.CheckState.Checked)
        )
        ui_layout.addRow("", self.start_minimized_checkbox)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        self.language_combo.setCurrentText(self.config.get("ui", {}).get("language", "zh_CN"))
        self.language_combo.currentTextChanged.connect(
            lambda text: self.config_manager.set_config("ui.language", text)
        )
        ui_layout.addRow("界面语言:", self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "system"])
        self.theme_combo.setCurrentText(self.config.get("ui", {}).get("theme", "dark"))
        self.theme_combo.currentTextChanged.connect(
            lambda text: self.config_manager.set_config("ui.theme", text)
        )
        ui_layout.addRow("界面主题:", self.theme_combo)
        
        advanced_layout.addWidget(ui_group)
        
        # 添加弹性空间
        advanced_layout.addStretch()
        
        config_tabs.addTab(advanced_tab, "高级设置")
        
        self.tab_widget.addTab(config_tab, "设置")
    
    def _init_log_tab(self):
        """初始化日志选项卡"""
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_layout.addWidget(self.log_text)
        
        # 日志控制工具栏
        log_controls = QHBoxLayout()
        
        self.log_clear_btn = QPushButton("清空日志")
        self.log_clear_btn.clicked.connect(self.log_text.clear)
        log_controls.addWidget(self.log_clear_btn)
        
        self.log_save_btn = QPushButton("保存日志")
        self.log_save_btn.clicked.connect(self._on_save_log_clicked)
        log_controls.addWidget(self.log_save_btn)
        
        log_controls.addStretch()
        
        self.log_follow_check = QCheckBox("自动滚动")
        self.log_follow_check.setChecked(True)
        log_controls.addWidget(self.log_follow_check)
        
        log_layout.addLayout(log_controls)
        
        self.tab_widget.addTab(log_tab, "日志")
        
        # 连接自定义日志处理器，将日志输出到UI
        self._setup_ui_logger()
    
    def _setup_ui_logger(self):
        """设置UI日志处理器"""
        class QtLogHandler:
            """将日志输出到Qt控件"""
            def __init__(self, text_edit, max_lines=1000):
                self.text_edit = text_edit
                self.max_lines = max_lines
                self.log_lines = []
                
                # 日志级别颜色
                self.colors = {
                    "DEBUG": "gray",
                    "INFO": "black",
                    "SUCCESS": "green",
                    "WARNING": "orange",
                    "ERROR": "red",
                    "CRITICAL": "purple"
                }
            
            def write(self, message):
                """处理日志消息"""
                if not message.strip():
                    return
                    
                try:
                    # 检查text_edit是否还存在
                    if not self.text_edit or not self.text_edit.isVisible():
                        return
                        
                    self.log_lines.append(message)
                    
                    # 保持日志行数在限制内
                    if len(self.log_lines) > self.max_lines:
                        self.log_lines.pop(0)
                    
                    # 根据日志级别设置颜色
                    color = "black"
                    for level, level_color in self.colors.items():
                        if level in message:
                            color = level_color
                            break
                    
                    # 将消息添加到文本编辑器
                    self.text_edit.append(f'<font color="{color}">{message}</font>')
                    
                    # 如果设置了自动滚动，则滚动到底部
                    try:
                        # 检查父组件是否存在
                        parent = self.text_edit.parent()
                        if not parent:
                            return
                            
                        # 查找log_follow_check
                        log_follow_check = parent.findChild(QCheckBox, "log_follow_check")
                        if log_follow_check and log_follow_check.isChecked():
                            scrollbar = self.text_edit.verticalScrollBar()
                            if scrollbar:
                                scrollbar.setValue(scrollbar.maximum())
                    except Exception as e:
                        logger.error(f"更新日志滚动时出错: {e}")
                    
                except Exception as e:
                    logger.error(f"写入日志时出错: {e}")
        
        self.ui_log_handler = QtLogHandler(self.log_text)
        logger.add(self.ui_log_handler.write, level="DEBUG", format="{time:HH:mm:ss} | {level: <8} | {message}")
    
    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        # 只有在配置启用时创建托盘图标
        if self.config.get("ui", {}).get("minimize_to_tray", False):
            self.tray_icon = QSystemTrayIcon(self)
            
            # 设置默认图标
            icon = QIcon()
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#4a4a4a"))
            icon.addPixmap(pixmap)
            self.tray_icon.setIcon(icon)
            
            # 托盘菜单
            tray_menu = QMenu()
            
            show_action = QAction("显示", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            start_monitor_action = QAction("开始监控", self)
            start_monitor_action.triggered.connect(self._on_start_clicked)
            tray_menu.addAction(start_monitor_action)
            
            stop_monitor_action = QAction("停止监控", self)
            stop_monitor_action.triggered.connect(self._on_stop_clicked)
            tray_menu.addAction(stop_monitor_action)
            
            tray_menu.addSeparator()
            
            exit_action = QAction("退出", self)
            exit_action.triggered.connect(self.close)
            tray_menu.addAction(exit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
    
    def _on_tray_activated(self, reason):
        """
        托盘图标激活事件处理
        
        参数:
            reason: 激活原因
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def _on_start_clicked(self):
        """开始监控按钮点击事件"""
        success = self.monitor_manager.start_monitoring()
        
        if success:
            # 更新UI状态
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            self.pause_action.setEnabled(True)
            self.pause_action.setText("暂停监控")
            
            # 更新状态栏
            self.status_label.setText("监控中")
            
            # 记录日志
            logger.info("开始监控")
        else:
            QMessageBox.warning(self, "警告", "启动监控失败，请检查日志获取详细信息。")
    
    def _on_stop_clicked(self):
        """停止监控按钮点击事件"""
        success = self.monitor_manager.stop_monitoring()
        
        if success:
            # 更新UI状态
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.pause_action.setText("暂停监控")
            
            # 更新状态栏
            self.status_label.setText("就绪")
            
            # 记录日志
            logger.info("停止监控")
        else:
            QMessageBox.warning(self, "警告", "停止监控失败，请检查日志获取详细信息。")
    
    def _on_pause_clicked(self):
        """暂停/继续监控按钮点击事件"""
        if self.monitor_manager.is_paused():
            # 当前是暂停状态，继续监控
            success = self.monitor_manager.resume_monitoring()
            
            if success:
                # 更新UI状态
                self.pause_action.setText("暂停监控")
                
                # 更新状态栏
                self.status_label.setText("监控中")
                
                # 记录日志
                logger.info("继续监控")
            else:
                QMessageBox.warning(self, "警告", "继续监控失败，请检查日志获取详细信息。")
        else:
            # 当前是运行状态，暂停监控
            success = self.monitor_manager.pause_monitoring()
            
            if success:
                # 更新UI状态
                self.pause_action.setText("继续监控")
                
                # 更新状态栏
                self.status_label.setText("已暂停")
                
                # 记录日志
                logger.info("暂停监控")
            else:
                QMessageBox.warning(self, "警告", "暂停监控失败，请检查日志获取详细信息。")
    
    def _on_test_push_clicked(self):
        """测试推送按钮点击事件"""
        success = self.monitor_manager.test_notification()
        
        if success:
            QMessageBox.information(self, "通知", "测试推送成功！")
        else:
            QMessageBox.warning(self, "警告", "测试推送失败，请检查日志获取详细信息。")
    
    def _on_help_clicked(self):
        """帮助按钮点击事件"""
        help_text = """
        <h2>EVE监视器使用指南</h2>
        <p>EVE监视器是一款为《EVE：无烬星河》多模拟器监控设计的工具。</p>
        
        <h3>基本操作</h3>
        <ul>
            <li><b>开始监控</b>：启动监控功能</li>
            <li><b>停止监控</b>：停止监控功能</li>
            <li><b>暂停监控</b>：临时暂停监控，可以随时恢复</li>
            <li><b>测试推送</b>：测试通知推送功能</li>
        </ul>
        
        <h3>配置说明</h3>
        <ul>
            <li><b>屏幕配置</b>：设置监控区域和模拟器布局</li>
            <li><b>OCR配置</b>：设置文字识别参数</li>
            <li><b>通知配置</b>：设置通知推送方式和相关参数</li>
            <li><b>高级设置</b>：调整截图间隔、队列大小、界面选项等</li>
        </ul>
        
        <h3>常见问题</h3>
        <ul>
            <li><b>推送不工作</b>：检查网络连接和API设置</li>
            <li><b>识别不准确</b>：调整OCR参数，确保游戏界面可见</li>
            <li><b>CPU占用高</b>：增加截图间隔，减少模拟器数量</li>
        </ul>
        
        <p>更多详细信息，请访问 <a href="https://github.com/yourusername/EVEMonitor">GitHub项目页面</a></p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("帮助")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def _on_save_log_clicked(self):
        """保存日志按钮点击事件"""
        if not self.log_text.toPlainText():
            QMessageBox.information(self, "通知", "当前日志为空，无需保存。")
            return
        
        # 获取当前时间作为文件名
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"EVEMonitor_Log_{now}.txt"
        
        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存日志",
            file_name,
            "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "通知", f"日志已保存至: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"保存日志失败: {str(e)}")
    
    def _on_monitoring_started(self):
        """监控开始事件处理"""
        # 已在_on_start_clicked中处理
        pass
    
    def _on_monitoring_stopped(self):
        """监控停止事件处理"""
        # 已在_on_stop_clicked中处理
        pass
    
    def _on_status_updated(self, status):
        """状态更新事件处理"""
        # 在MonitorStatusWidget中处理
        pass
    
    def _on_error_occurred(self, error_msg):
        """错误发生事件处理"""
        # 在状态栏显示错误
        self.status_label.setText(f"错误: {error_msg}")
        
        # 如果是严重错误，弹出消息框
        if "失败" in error_msg or "错误" in error_msg:
            if self.isVisible():  # 只在窗口可见时显示
                QMessageBox.warning(self, "错误", error_msg)
    
    def _update_status_display(self):
        """更新状态显示"""
        # 获取当前状态
        status = self.monitor_manager.get_status()
        
        # 更新标题栏状态
        if status["running"]:
            if status["paused"]:
                self.setWindowTitle("EVE监视器 - 已暂停")
            else:
                self.setWindowTitle(
                    f"EVE监视器 - 监控中 (FPS: {status['stats']['last_fps']:.1f})"
                )
        else:
            self.setWindowTitle("EVE监视器 - 就绪")
    
    def _on_config_changed(self, config, section):
        """
        配置变更处理
        
        参数:
            config: 更新后的配置
            section: 更新的部分
        """
        # 确保配置是字典类型
        if isinstance(config, str):
            try:
                import json
                self.config = json.loads(config)
            except json.JSONDecodeError:
                logger.error(f"无法解析配置字符串: {config}")
                self.config = {}
        elif isinstance(config, dict):
            self.config = config
        else:
            logger.error(f"不支持的配置类型: {type(config)}")
            self.config = {}
        
        # 根据配置更新UI
        if section in ["ui", "ui.minimize_to_tray"]:
            if self.config.get("ui", {}).get("minimize_to_tray", False) and not hasattr(self, 'tray_icon'):
                self._init_tray_icon()
            elif hasattr(self, 'tray_icon') and not self.config.get("ui", {}).get("minimize_to_tray", False):
                self.tray_icon.hide()
                del self.tray_icon
        
        logger.debug(f"主窗口已更新配置: {section}")
    
    def _load_window_settings(self):
        """加载窗口设置"""
        settings = QSettings("EVEMonitor", "MainWindow")
        
        # 恢复窗口大小和位置
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        
        # 恢复窗口状态（最大化等）
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
    
    def _save_window_settings(self):
        """保存窗口设置"""
        settings = QSettings("EVEMonitor", "MainWindow")
        
        # 保存窗口大小和位置
        settings.setValue("geometry", self.saveGeometry())
        
        # 保存窗口状态（最大化等）
        settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        
        参数:
            event: 关闭事件
        """
        # 确保配置是字典类型
        if not isinstance(self.config, dict):
            logger.error(f"配置类型错误: {type(self.config)}")
            self.config = {}
            
        # 获取最小化到托盘的配置，默认为 False
        minimize_to_tray = self.config.get("ui", {}).get("minimize_to_tray", False)
        
        # 如果配置为最小化到托盘，则最小化而不是关闭
        if hasattr(self, 'tray_icon') and minimize_to_tray:
            # 如果监控正在运行，询问是否关闭
            if self.monitor_manager.is_monitoring():
                reply = QMessageBox.question(
                    self, "确认退出",
                    '监控正在运行中，是否关闭程序？\n选择"否"将最小化到托盘。',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    self.hide()
                    event.ignore()
                    self.tray_icon.showMessage("EVE监视器", "程序已最小化到托盘", QSystemTrayIcon.MessageIcon.Information, 2000)
                    return
        else:
            # 如果监控正在运行，询问是否关闭
            if self.monitor_manager.is_monitoring():
                reply = QMessageBox.question(
                    self, "确认退出",
                    '监控正在运行中，是否关闭程序？\n选择"否"将最小化到托盘。',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
        
        # 停止监控
        if self.monitor_manager.is_monitoring():
            self.monitor_manager.stop_monitoring()
        
        # 保存窗口设置
        self._save_window_settings()
        
        # 关闭托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        # 退出程序
        QApplication.quit()


class QTextEdit(QTextEdit):
    """自定义文本编辑器类"""
    
    def __init__(self, parent=None):
        """
        初始化文本编辑器
        
        Args:
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 5px;
            }
            QTextEdit:focus {
                border: 1px solid #4a4a4a;
            }
        """)
        
        # 设置字体
        font = self.font()
        # 使用系统默认等宽字体
        if sys.platform == "darwin":  # macOS
            font.setFamily("Menlo")
        elif sys.platform == "win32":  # Windows
            font.setFamily("Consolas")
        else:  # Linux 和其他系统
            font.setFamily("DejaVu Sans Mono")
        font.setPointSize(10)
        self.setFont(font)
    
    def append(self, text):
        """添加文本"""
        self.insertPlainText(text + "\n")
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def clear(self):
        """清空文本"""
        self.setPlainText("")
    
    def toPlainText(self):
        """获取纯文本内容"""
        return super().toPlainText() 