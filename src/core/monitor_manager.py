#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控管理器模块

负责协调屏幕捕获、OCR识别和数据分析等功能。
管理不同模拟器的状态和警报。
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from src.utils.logger_utils import logger
from src.utils.queue_manager import queue_manager
from src.core.screen_capture import ScreenCapture
from src.core.ocr_engine import OCREngine
from src.core.data_analyzer import DataAnalyzer
from src.core.notification import NotificationManager
from PyQt6.QtCore import QObject, pyqtSignal


class MonitorManager(QObject):
    """监控管理器，协调各个模块工作"""
    
    # 定义信号
    monitoring_started = pyqtSignal()  # 监控开始信号
    monitoring_stopped = pyqtSignal()  # 监控停止信号
    status_updated = pyqtSignal(dict)  # 状态更新信号
    error_occurred = pyqtSignal(str)   # 错误发生信号
    ship_detected = pyqtSignal(dict)   # 舰船检测信号
    
    def __init__(self, config_manager):
        """
        初始化监控管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__()
        self.config_manager = config_manager
        self.running = False
        self.paused = False  # 添加暂停状态
        self.monitor_thread = None
        self.lock = threading.RLock()
        
        # 性能统计
        self.last_fps = 0.0
        self.processing_time = 0.0
        
        # 初始化组件
        self.screen_capture = ScreenCapture(config_manager)
        self.ocr_engine = OCREngine(config_manager)
        self.data_analyzer = DataAnalyzer(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        
        # 模拟器状态
        self.emulator_status = {}
        
        # 从配置加载模拟器设置
        config = self.config_manager.get_config()
        self.emulator_configs = config.get("monitor", {}).get("emulators", [])
        
        # 注册队列监听
        queue_manager.start_listener("ocr_result", self._process_ocr_result)
        queue_manager.start_listener("analysis_result", self._process_analysis_result)
        
        logger.debug("监控管理器初始化完成")
    
    def start_monitoring(self) -> bool:
        """启动监控"""
        with self.lock:
            if self.running:
                logger.warning("监控已经在运行中")
                return False
            
            try:
                # 更新模拟器配置
                config = self.config_manager.get_config()
                self.emulator_configs = config.get("monitor", {}).get("emulators", [])
                
                # 启动各组件
                self.ocr_engine.start_ocr()
                self.screen_capture.start_capture(self.emulator_configs)
                
                # 启动监控线程
                self.running = True
                self.paused = False
                self.monitor_thread = threading.Thread(target=self._monitor_loop)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
                
                logger.info("监控已启动")
                self.monitoring_started.emit()
                return True
                
            except Exception as e:
                error_msg = f"启动监控失败: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
    
    def stop_monitoring(self) -> bool:
        """停止监控"""
        with self.lock:
            if not self.running:
                logger.warning("监控已经停止")
                return False
            
            try:
                # 停止标志
                self.running = False
                self.paused = False
                
                # 立即发送停止信号
                self.monitoring_stopped.emit()
                
                # 停止队列监听器
                queue_manager.stop()
                
                # 停止各组件
                try:
                    self.screen_capture.stop_capture()
                except Exception as e:
                    logger.error(f"停止屏幕捕获时出错: {e}")
                
                try:
                    self.ocr_engine.stop_ocr()
                except Exception as e:
                    logger.error(f"停止OCR引擎时出错: {e}")
                
                # 等待监控线程结束，设置较短的超时时间
                if self.monitor_thread and self.monitor_thread.is_alive():
                    try:
                        self.monitor_thread.join(timeout=0.5)  # 减少超时时间到0.5秒
                    except Exception as e:
                        logger.error(f"等待监控线程结束时出错: {e}")
                    finally:
                        self.monitor_thread = None
                
                # 清空状态
                self.emulator_status = {}
                self.last_fps = 0.0
                self.processing_time = 0.0
                
                logger.info("监控已停止")
                return True
                
            except Exception as e:
                error_msg = f"停止监控时出错: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                # 确保状态被重置
                self.running = False
                self.paused = False
                self.monitor_thread = None
                return False
    
    def is_monitoring(self) -> bool:
        """
        检查是否正在监控
        
        Returns:
            bool: 是否正在监控
        """
        with self.lock:
            return self.running
    
    def _monitor_loop(self) -> None:
        """监控线程主循环"""
        logger.debug("监控循环开始")
        
        last_status_update = time.time()
        status_update_interval = 5.0  # 状态更新间隔（秒）
        last_fps_update = time.time()
        fps_update_interval = 1.0  # FPS更新间隔（秒）
        error_count = 0  # 错误计数器
        max_errors = 5  # 最大错误次数
        error_cooldown = 60.0  # 错误冷却时间（秒）
        last_error_time = 0  # 上次错误时间
        
        while self.running:
            try:
                # 如果处于暂停状态，等待一段时间后继续
                if self.paused:
                    time.sleep(0.5)
                    continue
                
                # 定期更新状态
                current_time = time.time()
                if current_time - last_status_update >= status_update_interval:
                    self._update_status()
                    last_status_update = current_time
                
                # 更新FPS
                if current_time - last_fps_update >= fps_update_interval:
                    self.last_fps = self.screen_capture.get_fps()
                    last_fps_update = current_time
                
                # 短暂休眠以降低CPU占用
                time.sleep(0.1)
                
                # 重置错误计数
                error_count = 0
                
            except Exception as e:
                current_time = time.time()
                error_count += 1
                
                # 检查是否需要重置错误计数（冷却时间已过）
                if current_time - last_error_time >= error_cooldown:
                    error_count = 1
                    last_error_time = current_time
                
                logger.error(f"监控循环出错: {e}")
                self.error_occurred.emit(f"监控循环出错: {str(e)}")
                
                # 如果错误次数过多，停止监控
                if error_count >= max_errors:
                    logger.error("监控循环错误次数过多，停止监控")
                    self.error_occurred.emit("监控循环错误次数过多，停止监控")
                    self.running = False
                    break
                
                # 根据错误次数增加等待时间
                wait_time = min(1.0 * error_count, 5.0)  # 最多等待5秒
                time.sleep(wait_time)
        
        logger.debug("监控循环结束")
    
    def _update_status(self) -> None:
        """更新状态"""
        status = {
            "running": self.running,
            "paused": self.paused,
            "stats": {
                "last_fps": self.last_fps,
                "queue_size": queue_manager.get_queue_size("ocr"),
                "processing_time": self.processing_time
            }
        }
        
        self.status_updated.emit(status)
    
    def _process_ocr_result(self, data: Dict[str, Any]) -> None:
        """处理OCR结果"""
        try:
            # 检查数据是否过期（超过3秒）
            timestamp = data.get("timestamp")
            if timestamp and (datetime.now() - timestamp).total_seconds() > 3:
                logger.debug("OCR结果已过期，跳过处理")
                return
            
            # 处理OCR结果
            analysis_result = self.data_analyzer.analyze(data)
            
            # 发送到通知队列
            queue_manager.put({
                "type": "analysis",
                "data": analysis_result,
                "timestamp": datetime.now()
            }, queue_name="notification", timeout=0.5)
            
        except Exception as e:
            error_msg = f"处理OCR结果时出错: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def _process_analysis_result(self, data: Dict[str, Any]) -> None:
        """
        处理分析结果
        
        Args:
            data: 分析结果数据
        """
        if data.get("type") != "analysis_result":
            return
        
        # 检查数据是否过期（超过3秒）
        timestamp = data.get("timestamp")
        if timestamp and (datetime.now() - timestamp).total_seconds() > 3:
            logger.debug("分析结果已过期，跳过处理")
            return
        
        # 提取信息
        emulator = data.get("emulator", "unknown")
        region_type = data.get("region_type", "unknown")
        alerts = data.get("alerts", [])
        
        # 更新状态
        with self.lock:
            if emulator not in self.emulator_status:
                self.emulator_status[emulator] = {}
            
            # 更新模拟器状态
            if region_type == "ship_status":
                ship_status = data.get("ship_status")
                self.emulator_status[emulator]["ship_status"] = ship_status
                # 发送舰船检测信号
                self.ship_detected.emit({
                    "emulator": emulator,
                    "ship_status": ship_status,
                    "timestamp": datetime.now()
                })
            elif region_type == "chat":
                self.emulator_status[emulator]["chat"] = data.get("chat_messages")
            elif region_type == "target":
                self.emulator_status[emulator]["target"] = data.get("target_info")
            
            # 记录最后更新时间
            self.emulator_status[emulator]["last_update"] = datetime.now()
            
            # 处理警报
            if alerts:
                self._handle_alerts(emulator, alerts)
    
    def _handle_alerts(self, emulator: str, alerts: List[Dict[str, Any]]) -> None:
        """
        处理警报
        
        Args:
            emulator: 模拟器名称
            alerts: 警报列表
        """
        try:
            # 获取警报配置
            alert_config = self.config_manager.get_config().get("alerts", {})
            
            # 处理每个警报
            for alert in alerts:
                alert_type = alert.get("type")
                alert_data = alert.get("data", {})
                
                # 检查警报类型是否启用
                if not alert_config.get(alert_type, {}).get("enabled", False):
                    continue
                
                # 发送通知
                self.notification_manager.send_notification(
                    title=f"警报 - {emulator}",
                    message=alert.get("message", ""),
                    alert_type=alert_type,
                    data=alert_data
                )
                
        except Exception as e:
            error_msg = f"处理警报时出错: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def pause_monitoring(self) -> bool:
        """暂停监控"""
        with self.lock:
            if not self.running:
                logger.warning("监控已经停止")
                return False
            
            if self.paused:
                logger.warning("监控已经处于暂停状态")
                return False
            
            self.paused = True
            logger.info("监控已暂停")
            return True
    
    def resume_monitoring(self) -> bool:
        """恢复监控"""
        with self.lock:
            if not self.running:
                logger.warning("监控已经停止")
                return False
            
            if not self.paused:
                logger.warning("监控已经处于运行状态")
                return False
            
            self.paused = False
            logger.info("监控已恢复")
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict[str, Any]: 状态字典
        """
        with self.lock:
            return {
                "running": self.running,
                "paused": self.paused,
                "emulator_status": self.emulator_status,
                "stats": {
                    "last_fps": self.last_fps,
                    "processing_time": self.processing_time
                }
            }
    
    def save_screenshot(self, emulator_name: str, region_name: Optional[str] = None) -> Optional[str]:
        """
        保存指定模拟器/区域的截图
        
        Args:
            emulator_name: 模拟器名称
            region_name: 区域名称，None表示整个模拟器窗口
            
        Returns:
            Optional[str]: 保存的文件路径，如果失败则返回None
        """
        try:
            # 获取最新截图
            if region_name:
                key = f"{emulator_name}_{region_name}"
            else:
                key = emulator_name
            
            capture_data = self.screen_capture.get_last_capture(key)
            if not capture_data:
                logger.warning(f"找不到{key}的截图")
                return None
            
            # 保存截图
            image = capture_data["image"]
            prefix = f"{emulator_name}_{region_name}" if region_name else emulator_name
            file_path = self.screen_capture.save_screenshot(image, prefix=prefix)
            
            logger.info(f"已保存截图: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return None
    
    def get_emulator_status(self, emulator_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模拟器状态
        
        Args:
            emulator_name: 模拟器名称，None表示获取所有模拟器的状态
            
        Returns:
            Dict[str, Any]: 模拟器状态数据
        """
        with self.lock:
            if emulator_name:
                return self.emulator_status.get(emulator_name, {})
            else:
                return self.emulator_status.copy()
    
    def update_config(self) -> None:
        """更新配置"""
        # 更新模拟器配置
        new_emulator_configs = self.config_manager.get_config().get("monitor", {}).get("emulators", [])
        
        # 如果配置变化且正在运行，重启监控
        if new_emulator_configs != self.emulator_configs and self.running:
            logger.info("模拟器配置已更改，重启监控...")
            self.stop_monitoring()
            self.emulator_configs = new_emulator_configs
            self.emulator_status = {}  # 清空状态
            self.start_monitoring()
        else:
            self.emulator_configs = new_emulator_configs
        
        # 更新各组件配置
        self.screen_capture.update_config()
        self.ocr_engine.update_config()
        self.data_analyzer.update_config()
        self.notification_manager.update_config()
        
        logger.debug("监控管理器配置已更新")
    
    def is_paused(self) -> bool:
        """检查是否处于暂停状态"""
        with self.lock:
            return self.paused
    
    def test_notification(self) -> bool:
        """
        发送测试通知
        
        Returns:
            bool: 发送是否成功
        """
        try:
            # 发送测试通知
            self.notification_manager.send_notification(
                title="测试通知",
                message="这是一条测试通知消息",
                level="info",
                data={
                    "timestamp": datetime.now(),
                    "test": True
                }
            )
            logger.info("测试通知发送成功")
            return True
            
        except Exception as e:
            error_msg = f"发送测试通知失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False 