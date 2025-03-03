#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控管理器
负责管理屏幕捕获、OCR识别和通知推送
"""

import os
import sys
import time
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import traceback

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from src.config.config_manager import ConfigManager
from src.core.screen_capture import ScreenCapture
from src.core.ocr_engine import OCREngine
from src.core.notification import NotificationManager


class MonitorManager(QObject):
    """监控管理器类"""
    
    # 定义信号
    monitoring_started = pyqtSignal()  # 监控开始信号
    monitoring_stopped = pyqtSignal()  # 监控停止信号
    monitoring_paused = pyqtSignal()   # 监控暂停信号
    monitoring_resumed = pyqtSignal()  # 监控恢复信号
    status_updated = pyqtSignal(dict)  # 状态更新信号
    error_occurred = pyqtSignal(str)   # 错误发生信号
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化监控管理器
        
        参数:
            config_manager: 配置管理器实例
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # 初始化组件
        self.screen_capture = ScreenCapture(config_manager)
        self.ocr_engine = OCREngine(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        
        # 监控状态
        self.running = False
        self.paused = False
        self.capture_thread = None
        self.processing_thread = None
        self.capture_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # 统计信息
        self.stats = {
            "started_at": None,
            "last_capture_time": None,
            "captures_count": 0,
            "processing_time_ms": 0,
            "queue_size": 0,
            "max_queue_size": 0
        }
        
        # 监听配置变更
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        logger.debug("监控管理器初始化完成")
    
    def start_monitoring(self) -> bool:
        """
        开始监控
        
        返回:
            bool: 是否成功启动
        """
        try:
            if self.running:
                logger.warning("监控已在运行中")
                return False
            
            # 重置状态
            self.running = True
            self.paused = False
            self.stats["started_at"] = datetime.now()
            self.stats["captures_count"] = 0
            self.stats["max_queue_size"] = 0
            
            # 启动捕获线程
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            # 启动处理线程
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            # 发送信号
            self.monitoring_started.emit()
            
            logger.info("监控已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动监控失败: {e}")
            self.error_occurred.emit(f"启动监控失败: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """
        停止监控
        
        返回:
            bool: 是否成功停止
        """
        try:
            if not self.running:
                logger.warning("监控未在运行")
                return False
            
            # 停止线程
            self.running = False
            if self.capture_thread:
                self.capture_thread.join(timeout=1)
            if self.processing_thread:
                self.processing_thread.join(timeout=1)
            
            # 清空队列
            while not self.capture_queue.empty():
                try:
                    self.capture_queue.get_nowait()
                except queue.Empty:
                    break
            
            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 发送信号
            self.monitoring_stopped.emit()
            
            logger.info("监控已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止监控失败: {e}")
            self.error_occurred.emit(f"停止监控失败: {str(e)}")
            return False
    
    def pause_monitoring(self) -> bool:
        """
        暂停监控
        
        返回:
            bool: 是否成功暂停
        """
        try:
            if not self.running or self.paused:
                return False
            
            self.paused = True
            self.monitoring_paused.emit()
            
            logger.info("监控已暂停")
            return True
            
        except Exception as e:
            logger.error(f"暂停监控失败: {e}")
            self.error_occurred.emit(f"暂停监控失败: {str(e)}")
            return False
    
    def resume_monitoring(self) -> bool:
        """
        恢复监控
        
        返回:
            bool: 是否成功恢复
        """
        try:
            if not self.running or not self.paused:
                return False
            
            self.paused = False
            self.monitoring_resumed.emit()
            
            logger.info("监控已恢复")
            return True
            
        except Exception as e:
            logger.error(f"恢复监控失败: {e}")
            self.error_occurred.emit(f"恢复监控失败: {str(e)}")
            return False
    
    def is_monitoring(self) -> bool:
        """
        是否正在监控
        
        返回:
            bool: 是否正在监控
        """
        return self.running
    
    def is_paused(self) -> bool:
        """
        是否已暂停
        
        返回:
            bool: 是否已暂停
        """
        return self.paused
    
    def get_status(self) -> dict:
        """
        获取当前状态
        
        返回:
            dict: 状态信息
        """
        return {
            "running": self.running,
            "paused": self.paused,
            "stats": self.stats.copy(),
            "queue_size": self.capture_queue.qsize(),
            "max_queue_size": self.stats["max_queue_size"]
        }
    
    def test_notification(self) -> bool:
        """
        测试通知
        
        返回:
            bool: 是否成功发送
        """
        try:
            return self.notification_manager.send_test_notification()
        except Exception as e:
            logger.error(f"测试通知失败: {e}")
            self.error_occurred.emit(f"测试通知失败: {str(e)}")
            return False
    
    def _capture_loop(self):
        """屏幕捕获循环"""
        try:
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # 获取截图间隔
                interval = self.config.get("timing", {}).get("capture_interval_ms", 2000) / 1000
                
                # 捕获屏幕
                start_time = time.time()
                image = self.screen_capture.capture()
                
                if image:
                    # 更新统计信息
                    self.stats["last_capture_time"] = datetime.now()
                    self.stats["captures_count"] += 1
                    
                    # 添加到队列
                    self.capture_queue.put(image)
                    
                    # 更新队列统计
                    queue_size = self.capture_queue.qsize()
                    self.stats["queue_size"] = queue_size
                    self.stats["max_queue_size"] = max(
                        self.stats["max_queue_size"],
                        queue_size
                    )
                
                # 等待下一次捕获
                elapsed = time.time() - start_time
                if elapsed < interval:
                    time.sleep(interval - elapsed)
                
        except Exception as e:
            logger.error(f"屏幕捕获循环出错: {e}")
            self.error_occurred.emit(f"屏幕捕获出错: {str(e)}")
    
    def _processing_loop(self):
        """图像处理循环"""
        try:
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                try:
                    # 从队列获取图像
                    image = self.capture_queue.get(timeout=0.1)
                    
                    # 处理图像
                    start_time = time.time()
                    results = self.ocr_engine.recognize(image)
                    
                    # 更新处理时间
                    self.stats["processing_time_ms"] = (
                        time.time() - start_time
                    ) * 1000
                    
                    # 处理结果
                    for result in results:
                        # 添加到结果队列
                        self.result_queue.put(result)
                        
                        # 发送通知
                        if self._should_send_notification(result):
                            self.notification_manager.send_notification(
                                result["text"],
                                result["confidence"]
                            )
                    
                except queue.Empty:
                    continue
                    
        except Exception as e:
            logger.error(f"图像处理循环出错: {e}")
            self.error_occurred.emit(f"图像处理出错: {str(e)}")
    
    def _should_send_notification(self, result: dict) -> bool:
        """
        判断是否应该发送通知
        
        参数:
            result: OCR识别结果
            
        返回:
            bool: 是否应该发送通知
        """
        try:
            # 获取通知配置
            notification_config = self.config.get("notification", {})
            
            # 检查是否启用通知
            if not notification_config.get("enabled", True):
                return False
            
            # 检查置信度
            confidence_threshold = notification_config.get(
                "confidence_threshold",
                0.6
            )
            if result["confidence"] < confidence_threshold:
                return False
            
            # 检查通知间隔
            min_interval = notification_config.get("min_interval", 60)
            last_notification = getattr(
                self.notification_manager,
                "last_notification_time",
                None
            )
            
            if last_notification:
                elapsed = (
                    datetime.now() - last_notification
                ).total_seconds()
                if elapsed < min_interval:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查通知条件时出错: {e}")
            return False
    
    def _on_config_changed(self, key: str, value: Any) -> None:
        """
        配置变更回调函数
        
        参数:
            key: 变更的配置键
            value: 变更的配置值
        """
        try:
            logger.debug(f"监控管理器接收到配置变更: {key}={value}")
            
            # 更新各组件配置
            if key.startswith("ocr."):
                self.ocr_engine.update_config()
            elif key.startswith("notification."):
                self.notification_manager.update_config()
            elif key.startswith("capture.") or key.startswith("timing.capture"):
                self.screen_capture.update_config()
            elif key.startswith("processor.") or key.startswith("debug."):
                self.image_processor.update_config()
            elif key.startswith("analyzer.") or key.startswith("timing.analysis"):
                self.data_analyzer.update_config()
            
            logger.debug("监控管理器配置更新完成")
        except Exception as e:
            logger.error(f"更新监控管理器配置失败: {e}")
            traceback.print_exc() 