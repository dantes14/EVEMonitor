#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR配置小部件
用于配置OCR引擎参数
"""

import sys
import os
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QCheckBox,
    QComboBox, QTabWidget, QFileDialog, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPixmap, QIcon


class OCRConfigWidget(QWidget):
    """OCR配置小部件类"""
    
    def __init__(self, config_manager, parent=None):
        """
        初始化OCR配置小部件
        
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
        
        logger.debug("OCR配置小部件初始化完成")
    
    def _init_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        
        # OCR引擎选择
        engine_group = QGroupBox("OCR引擎设置")
        engine_layout = QFormLayout(engine_group)
        
        # 引擎选择下拉框
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["PaddleOCR", "Tesseract"])
        current_engine = self.config.get("ocr", {}).get("engine", "Tesseract")
        self.engine_combo.setCurrentText(current_engine)
        self.engine_combo.currentTextChanged.connect(
            lambda v: self.config_manager.set_config("ocr.engine", v)
        )
        engine_layout.addRow("OCR引擎:", self.engine_combo)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["ch", "en", "chinese_cht", "japan", "korean"])
        current_language = self.config.get("ocr", {}).get("language", "ch")
        self.language_combo.setCurrentText(current_language)
        self.language_combo.currentTextChanged.connect(
            lambda v: self.config_manager.set_config("ocr.language", v)
        )
        engine_layout.addRow("识别语言:", self.language_combo)
        
        main_layout.addWidget(engine_group)
        
        # 识别参数设置
        params_group = QGroupBox("识别参数设置")
        params_layout = QFormLayout(params_group)
        
        # 置信度阈值
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setDecimals(2)
        self.confidence_spin.setValue(self.config.get("ocr", {}).get("confidence_threshold", 0.5))
        self.confidence_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.confidence_threshold", v)
        )
        params_layout.addRow("置信度阈值:", self.confidence_spin)
        
        # 使用GPU
        self.use_gpu_check = QCheckBox()
        self.use_gpu_check.setChecked(self.config.get("ocr", {}).get("use_gpu", False))
        self.use_gpu_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.use_gpu", v)
        )
        params_layout.addRow("使用GPU:", self.use_gpu_check)
        
        # 并行处理线程数
        self.num_threads_spin = QSpinBox()
        self.num_threads_spin.setRange(1, 16)
        self.num_threads_spin.setValue(self.config.get("ocr", {}).get("num_threads", 4))
        self.num_threads_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.num_threads", v)
        )
        params_layout.addRow("处理线程数:", self.num_threads_spin)
        
        # 批量处理大小
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(self.config.get("ocr", {}).get("batch_size", 1))
        self.batch_size_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.batch_size", v)
        )
        params_layout.addRow("批量处理大小:", self.batch_size_spin)
        
        main_layout.addWidget(params_group)
        
        # PaddleOCR特有设置
        self.paddle_group = QGroupBox("PaddleOCR设置")
        paddle_layout = QFormLayout(self.paddle_group)
        
        # 模型目录
        model_path_layout = QHBoxLayout()
        
        self.model_dir_edit = QLineEdit()
        self.model_dir_edit.setText(self.config.get("ocr", {}).get("paddle", {}).get("model_dir", ""))
        self.model_dir_edit.textChanged.connect(
            lambda v: self.config_manager.set_config("ocr.paddle.model_dir", v)
        )
        model_path_layout.addWidget(self.model_dir_edit)
        
        self.browse_model_btn = QPushButton("浏览...")
        self.browse_model_btn.clicked.connect(self._on_browse_model_clicked)
        model_path_layout.addWidget(self.browse_model_btn)
        
        paddle_layout.addRow("模型目录:", model_path_layout)
        
        # 使用检测器
        self.use_det_check = QCheckBox()
        self.use_det_check.setChecked(self.config.get("ocr", {}).get("paddle", {}).get("use_det", True))
        self.use_det_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.paddle.use_det", v)
        )
        paddle_layout.addRow("使用文本检测:", self.use_det_check)
        
        # 使用分类器
        self.use_cls_check = QCheckBox()
        self.use_cls_check.setChecked(self.config.get("ocr", {}).get("paddle", {}).get("use_cls", True))
        self.use_cls_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.paddle.use_cls", v)
        )
        paddle_layout.addRow("使用方向分类:", self.use_cls_check)
        
        # 使用server模式
        self.use_server_check = QCheckBox()
        self.use_server_check.setChecked(self.config.get("ocr", {}).get("paddle", {}).get("use_server_mode", False))
        self.use_server_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.paddle.use_server_mode", v)
        )
        paddle_layout.addRow("使用Server模式:", self.use_server_check)
        
        main_layout.addWidget(self.paddle_group)
        
        # Tesseract特有设置
        self.tesseract_group = QGroupBox("Tesseract设置")
        tesseract_layout = QFormLayout(self.tesseract_group)
        
        # Tesseract可执行文件路径
        tesseract_path_layout = QHBoxLayout()
        
        self.tesseract_path_edit = QLineEdit()
        self.tesseract_path_edit.setText(self.config.get("ocr", {}).get("tesseract", {}).get("executable_path", ""))
        self.tesseract_path_edit.textChanged.connect(
            lambda v: self.config_manager.set_config("ocr.tesseract.executable_path", v)
        )
        tesseract_path_layout.addWidget(self.tesseract_path_edit)
        
        self.browse_tesseract_btn = QPushButton("浏览...")
        self.browse_tesseract_btn.clicked.connect(self._on_browse_tesseract_clicked)
        tesseract_path_layout.addWidget(self.browse_tesseract_btn)
        
        tesseract_layout.addRow("可执行文件路径:", tesseract_path_layout)
        
        # 数据目录
        tessdata_path_layout = QHBoxLayout()
        
        self.tessdata_dir_edit = QLineEdit()
        self.tessdata_dir_edit.setText(self.config.get("ocr", {}).get("tesseract", {}).get("tessdata_dir", ""))
        self.tessdata_dir_edit.textChanged.connect(
            lambda v: self.config_manager.set_config("ocr.tesseract.tessdata_dir", v)
        )
        tessdata_path_layout.addWidget(self.tessdata_dir_edit)
        
        self.browse_tessdata_btn = QPushButton("浏览...")
        self.browse_tessdata_btn.clicked.connect(self._on_browse_tessdata_clicked)
        tessdata_path_layout.addWidget(self.browse_tessdata_btn)
        
        tesseract_layout.addRow("语言数据目录:", tessdata_path_layout)
        
        # 配置参数
        self.tesseract_config_edit = QLineEdit()
        self.tesseract_config_edit.setText(self.config.get("ocr", {}).get("tesseract", {}).get("config", ""))
        self.tesseract_config_edit.textChanged.connect(
            lambda v: self.config_manager.set_config("ocr.tesseract.config", v)
        )
        tesseract_layout.addRow("配置参数:", self.tesseract_config_edit)
        
        main_layout.addWidget(self.tesseract_group)
        
        # 区域设置
        roi_group = QGroupBox("识别区域设置")
        roi_layout = QFormLayout(roi_group)
        
        # 系统名称区域
        self.system_name_enabled_check = QCheckBox("启用")
        self.system_name_enabled_check.setChecked(self.config.get("ocr", {}).get("roi", {}).get("system_name", {}).get("enabled", True))
        self.system_name_enabled_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.roi.system_name.enabled", v)
        )
        roi_layout.addRow("系统名称区域:", self.system_name_enabled_check)
        
        # 系统名称区域坐标设置
        system_coord_layout = QHBoxLayout()
        
        self.system_x_spin = QSpinBox()
        self.system_x_spin.setRange(0, 9999)
        self.system_x_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("system_name", {}).get("x", 0))
        self.system_x_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.system_name.x", v)
        )
        system_coord_layout.addWidget(QLabel("X:"))
        system_coord_layout.addWidget(self.system_x_spin)
        
        self.system_y_spin = QSpinBox()
        self.system_y_spin.setRange(0, 9999)
        self.system_y_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("system_name", {}).get("y", 0))
        self.system_y_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.system_name.y", v)
        )
        system_coord_layout.addWidget(QLabel("Y:"))
        system_coord_layout.addWidget(self.system_y_spin)
        
        self.system_width_spin = QSpinBox()
        self.system_width_spin.setRange(1, 9999)
        self.system_width_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("system_name", {}).get("width", 200))
        self.system_width_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.system_name.width", v)
        )
        system_coord_layout.addWidget(QLabel("宽度:"))
        system_coord_layout.addWidget(self.system_width_spin)
        
        self.system_height_spin = QSpinBox()
        self.system_height_spin.setRange(1, 9999)
        self.system_height_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("system_name", {}).get("height", 30))
        self.system_height_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.system_name.height", v)
        )
        system_coord_layout.addWidget(QLabel("高度:"))
        system_coord_layout.addWidget(self.system_height_spin)
        
        roi_layout.addRow("", system_coord_layout)
        
        # 舰船表格区域
        self.ship_table_enabled_check = QCheckBox("启用")
        self.ship_table_enabled_check.setChecked(self.config.get("ocr", {}).get("roi", {}).get("ship_table", {}).get("enabled", True))
        self.ship_table_enabled_check.toggled.connect(
            lambda v: self.config_manager.set_config("ocr.roi.ship_table.enabled", v)
        )
        roi_layout.addRow("舰船表格区域:", self.ship_table_enabled_check)
        
        # 舰船表格区域坐标设置
        ship_table_coord_layout = QHBoxLayout()
        
        self.ship_table_x_spin = QSpinBox()
        self.ship_table_x_spin.setRange(0, 9999)
        self.ship_table_x_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("ship_table", {}).get("x", 0))
        self.ship_table_x_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.ship_table.x", v)
        )
        ship_table_coord_layout.addWidget(QLabel("X:"))
        ship_table_coord_layout.addWidget(self.ship_table_x_spin)
        
        self.ship_table_y_spin = QSpinBox()
        self.ship_table_y_spin.setRange(0, 9999)
        self.ship_table_y_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("ship_table", {}).get("y", 0))
        self.ship_table_y_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.ship_table.y", v)
        )
        ship_table_coord_layout.addWidget(QLabel("Y:"))
        ship_table_coord_layout.addWidget(self.ship_table_y_spin)
        
        self.ship_table_width_spin = QSpinBox()
        self.ship_table_width_spin.setRange(1, 9999)
        self.ship_table_width_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("ship_table", {}).get("width", 400))
        self.ship_table_width_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.ship_table.width", v)
        )
        ship_table_coord_layout.addWidget(QLabel("宽度:"))
        ship_table_coord_layout.addWidget(self.ship_table_width_spin)
        
        self.ship_table_height_spin = QSpinBox()
        self.ship_table_height_spin.setRange(1, 9999)
        self.ship_table_height_spin.setValue(self.config.get("ocr", {}).get("roi", {}).get("ship_table", {}).get("height", 200))
        self.ship_table_height_spin.valueChanged.connect(
            lambda v: self.config_manager.set_config("ocr.roi.ship_table.height", v)
        )
        ship_table_coord_layout.addWidget(QLabel("高度:"))
        ship_table_coord_layout.addWidget(self.ship_table_height_spin)
        
        roi_layout.addRow("", ship_table_coord_layout)
        
        main_layout.addWidget(roi_group)
        
        # 测试和应用按钮
        buttons_layout = QHBoxLayout()
        
        self.test_ocr_btn = QPushButton("测试OCR")
        self.test_ocr_btn.clicked.connect(self._on_test_ocr_clicked)
        buttons_layout.addWidget(self.test_ocr_btn)
        
        self.detect_roi_btn = QPushButton("从截图检测区域")
        self.detect_roi_btn.clicked.connect(self._on_detect_roi_clicked)
        buttons_layout.addWidget(self.detect_roi_btn)
        
        buttons_layout.addStretch()
        
        self.reset_defaults_btn = QPushButton("重置为默认值")
        self.reset_defaults_btn.clicked.connect(self._on_reset_defaults_clicked)
        buttons_layout.addWidget(self.reset_defaults_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        # 设置UI状态
        self._update_ui_state()
    
    def _update_ui_state(self):
        """更新UI状态"""
        # 根据选择的引擎显示/隐藏相应设置
        current_engine = self.engine_combo.currentText()
        
        self.paddle_group.setVisible(current_engine == "PaddleOCR")
        self.tesseract_group.setVisible(current_engine == "Tesseract")
        
        # 启用/禁用区域设置
        self.system_x_spin.setEnabled(self.system_name_enabled_check.isChecked())
        self.system_y_spin.setEnabled(self.system_name_enabled_check.isChecked())
        self.system_width_spin.setEnabled(self.system_name_enabled_check.isChecked())
        self.system_height_spin.setEnabled(self.system_name_enabled_check.isChecked())
        
        self.ship_table_x_spin.setEnabled(self.ship_table_enabled_check.isChecked())
        self.ship_table_y_spin.setEnabled(self.ship_table_enabled_check.isChecked())
        self.ship_table_width_spin.setEnabled(self.ship_table_enabled_check.isChecked())
        self.ship_table_height_spin.setEnabled(self.ship_table_enabled_check.isChecked())
    
    def _on_browse_model_clicked(self):
        """浏览模型目录按钮点击事件"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择模型目录",
            self.model_dir_edit.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.model_dir_edit.setText(dir_path)
    
    def _on_browse_tesseract_clicked(self):
        """浏览Tesseract可执行文件按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Tesseract可执行文件",
            self.tesseract_path_edit.text(),
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self.tesseract_path_edit.setText(file_path)
    
    def _on_browse_tessdata_clicked(self):
        """浏览语言数据目录按钮点击事件"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择语言数据目录",
            self.tessdata_dir_edit.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.tessdata_dir_edit.setText(dir_path)
    
    def _on_test_ocr_clicked(self):
        """测试OCR按钮点击事件"""
        QMessageBox.information(
            self,
            "测试OCR",
            "OCR测试功能需要与监控管理器集成，将在后续实现。\n"
            "请先保存配置，然后在主界面使用测试功能。"
        )
    
    def _on_detect_roi_clicked(self):
        """从截图检测区域按钮点击事件"""
        QMessageBox.information(
            self,
            "检测区域",
            "区域检测功能需要与监控管理器集成，将在后续实现。\n"
            "请先保存配置，然后在主界面使用测试功能。"
        )
    
    def _on_reset_defaults_clicked(self):
        """重置为默认值按钮点击事件"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "是否确定将OCR设置重置为默认值？\n这将丢失所有自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 重置OCR配置
            default_ocr_config = self.config_manager._get_default_config()["ocr"]
            self.config_manager.set_config("ocr", default_ocr_config)
            
            # 刷新UI
            self._update_ui_from_config()
            
            QMessageBox.information(self, "重置完成", "OCR设置已重置为默认值。")
    
    def _update_ui_from_config(self):
        """从配置更新UI"""
        # 引擎设置
        self.engine_combo.setCurrentText(self.config["ocr"]["engine"])
        self.language_combo.setCurrentText(self.config["ocr"]["language"])
        
        # 参数设置
        self.confidence_spin.setValue(self.config["ocr"]["confidence_threshold"])
        self.use_gpu_check.setChecked(self.config["ocr"]["use_gpu"])
        self.num_threads_spin.setValue(self.config["ocr"]["num_threads"])
        self.batch_size_spin.setValue(self.config["ocr"]["batch_size"])
        
        # PaddleOCR设置
        self.model_dir_edit.setText(self.config["ocr"]["paddle"]["model_dir"])
        self.use_det_check.setChecked(self.config["ocr"]["paddle"]["use_det"])
        self.use_cls_check.setChecked(self.config["ocr"]["paddle"]["use_cls"])
        self.use_server_check.setChecked(self.config["ocr"]["paddle"]["use_server_mode"])
        
        # Tesseract设置
        self.tesseract_path_edit.setText(self.config["ocr"]["tesseract"]["executable_path"])
        self.tessdata_dir_edit.setText(self.config["ocr"]["tesseract"]["tessdata_dir"])
        self.tesseract_config_edit.setText(self.config["ocr"]["tesseract"]["config"])
        
        # 区域设置
        self.system_name_enabled_check.setChecked(self.config["ocr"]["roi"]["system_name"]["enabled"])
        self.system_x_spin.setValue(self.config["ocr"]["roi"]["system_name"]["x"])
        self.system_y_spin.setValue(self.config["ocr"]["roi"]["system_name"]["y"])
        self.system_width_spin.setValue(self.config["ocr"]["roi"]["system_name"]["width"])
        self.system_height_spin.setValue(self.config["ocr"]["roi"]["system_name"]["height"])
        
        self.ship_table_enabled_check.setChecked(self.config["ocr"]["roi"]["ship_table"]["enabled"])
        self.ship_table_x_spin.setValue(self.config["ocr"]["roi"]["ship_table"]["x"])
        self.ship_table_y_spin.setValue(self.config["ocr"]["roi"]["ship_table"]["y"])
        self.ship_table_width_spin.setValue(self.config["ocr"]["roi"]["ship_table"]["width"])
        self.ship_table_height_spin.setValue(self.config["ocr"]["roi"]["ship_table"]["height"])
        
        # 更新UI状态
        self._update_ui_state()
    
    def _on_config_changed(self, key, value):
        """
        配置变更事件处理
        
        参数:
            key: 配置键
            value: 配置值
        """
        # 更新UI状态
        if key == "ocr.engine":
            self.engine_combo.setCurrentText(value)
            self._update_engine_settings(value)
        elif key == "ocr.language":
            self.language_combo.setCurrentText(value)
        elif key == "ocr.confidence_threshold":
            self.confidence_spin.setValue(value)
        elif key == "ocr.use_gpu":
            self.use_gpu_check.setChecked(value)
        elif key == "ocr.num_threads":
            self.num_threads_spin.setValue(value)
        elif key == "ocr.batch_size":
            self.batch_size_spin.setValue(value)
        elif key == "ocr.paddle.model_dir":
            self.model_dir_edit.setText(value)
        elif key == "ocr.paddle.use_det":
            self.use_det_check.setChecked(value)
        elif key == "ocr.paddle.use_cls":
            self.use_cls_check.setChecked(value)
        elif key == "ocr.paddle.use_server_mode":
            self.use_server_check.setChecked(value)
        elif key == "ocr.tesseract.executable_path":
            self.tesseract_path_edit.setText(value)
        elif key == "ocr.tesseract.tessdata_dir":
            self.tessdata_dir_edit.setText(value)
        elif key == "ocr.tesseract.config":
            self.tesseract_config_edit.setText(value)
        elif key == "ocr.roi.system_name.enabled":
            self.system_name_enabled_check.setChecked(value)
        elif key == "ocr.roi.system_name.x":
            self.system_x_spin.setValue(value)
        elif key == "ocr.roi.system_name.y":
            self.system_y_spin.setValue(value)
        elif key == "ocr.roi.system_name.width":
            self.system_width_spin.setValue(value)
        elif key == "ocr.roi.system_name.height":
            self.system_height_spin.setValue(value)
        elif key == "ocr.roi.ship_table.enabled":
            self.ship_table_enabled_check.setChecked(value)
        elif key == "ocr.roi.ship_table.x":
            self.ship_table_x_spin.setValue(value)
        elif key == "ocr.roi.ship_table.y":
            self.ship_table_y_spin.setValue(value)
        elif key == "ocr.roi.ship_table.width":
            self.ship_table_width_spin.setValue(value)
        elif key == "ocr.roi.ship_table.height":
            self.ship_table_height_spin.setValue(value)
    
    def _update_engine_settings(self, engine):
        """
        更新引擎设置UI状态
        
        参数:
            engine: 当前选择的引擎
        """
        if engine == "PaddleOCR":
            self.paddle_group.setEnabled(True)
            self.tesseract_group.setEnabled(False)
        else:
            self.paddle_group.setEnabled(False)
            self.tesseract_group.setEnabled(True)
    
    def showEvent(self, event):
        """
        显示事件处理
        
        参数:
            event: 显示事件
        """
        super().showEvent(event)
        
        # 显示窗口时更新UI状态
        self._update_ui_state() 