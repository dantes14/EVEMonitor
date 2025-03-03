#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕捕获模块

负责捕获模拟器窗口或指定屏幕区域的截图。
支持多种截图方式和系统平台。
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, Tuple, List, Optional, Union, Any
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab
import cv2
import mss
import mss.tools

# 适配不同平台
if sys.platform == 'darwin':  # macOS
    import Quartz
    import AppKit
    from PyQt6.QtGui import QGuiApplication
elif sys.platform == 'win32':  # Windows
    import win32gui
    import win32ui
    import win32con
    import win32api
    from ctypes import windll
else:  # Linux
    from PyQt6.QtGui import QGuiApplication, QScreen
    from PyQt6.QtCore import QRect

from src.utils.logger_utils import logger
from src.utils.queue_manager import queue_manager

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


class WindowNotFoundError(Exception):
    """窗口未找到异常"""
    pass


class ScreenCapture:
    """屏幕捕获类，用于捕获屏幕图像"""
    
    def __init__(self, config_manager):
        """
        初始化屏幕捕获器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.running = False
        self.capture_thread = None
        
        # 读取配置
        config = self.config_manager.get_config()
        
        # 设置截图路径
        self.screenshot_path = Path(config.get("app", {}).get("paths", {}).get("screenshots", "./screenshots"))
        self.screenshot_path.mkdir(exist_ok=True)
        
        # 读取监控配置
        monitor_config = config.get("monitor", {}).get("capture", {})
        self.capture_interval = monitor_config.get("interval", 2.0)
        self.capture_quality = monitor_config.get("quality", 80)
        self.capture_method = monitor_config.get("method", "window")
        
        # 缓存最近的截图
        self.last_captures = {}
        self.lock = threading.RLock()
        
        # FPS 计算相关
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        self.sct = mss.mss()
        self.last_capture_time = 0
        self.last_capture = None
        
        logger.debug("屏幕捕获器初始化完成")
    
    def start_capture(self, emulator_configs: List[Dict[str, Any]]) -> bool:
        """
        启动屏幕捕获线程
        
        Args:
            emulator_configs: 模拟器配置列表
            
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            logger.warning("屏幕捕获器已在运行")
            return False
        
        self.running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(emulator_configs,),
            daemon=True
        )
        self.capture_thread.start()
        logger.info("屏幕捕获线程已启动")
        return True
    
    def stop_capture(self) -> None:
        """停止屏幕捕获线程"""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        logger.info("屏幕捕获线程已停止")
    
    def get_fps(self) -> float:
        """
        获取当前的 FPS
        
        Returns:
            float: 当前的 FPS
        """
        with self.lock:
            return self.current_fps

    def _update_fps(self) -> None:
        """更新 FPS 计算"""
        with self.lock:
            self.frame_count += 1
            current_time = time.time()
            elapsed = current_time - self.last_fps_time
            
            if elapsed >= 1.0:  # 每秒更新一次
                self.current_fps = self.frame_count / elapsed
                self.frame_count = 0
                self.last_fps_time = current_time

    def _capture_loop(self, emulator_configs: List[Dict[str, Any]]) -> None:
        """
        屏幕捕获线程主循环
        
        Args:
            emulator_configs: 模拟器配置列表
        """
        logger.debug("屏幕捕获循环开始")
        
        while self.running:
            start_time = time.time()
            
            for emulator_config in emulator_configs:
                if not emulator_config.get("enabled", False):
                    continue
                
                try:
                    emulator_name = emulator_config.get("name", "未命名模拟器")
                    window_title = emulator_config.get("window_title", "")
                    
                    # 捕获屏幕
                    if self.capture_method == "window" and window_title:
                        image = self._capture_window(window_title)
                    else:
                        # 使用区域捕获
                        regions = emulator_config.get("regions", [])
                        if not regions:
                            logger.warning(f"模拟器 '{emulator_name}' 未配置监控区域，无法进行区域捕获")
                            continue
                        
                        # 捕获整个屏幕
                        full_screen = self._capture_screen()
                        
                        # 处理每个监控区域
                        for region in regions:
                            region_name = region.get("name", "未命名区域")
                            x, y = region.get("x", 0), region.get("y", 0)
                            width, height = region.get("width", 100), region.get("height", 100)
                            
                            # 从全屏截图中裁剪出区域
                            try:
                                region_image = full_screen[y:y+height, x:x+width]
                                
                                # 如果区域超出屏幕范围，跳过
                                if region_image.size == 0:
                                    logger.warning(f"区域 '{region_name}' 超出屏幕范围，无法捕获")
                                    continue
                                
                                # 保存区域截图到缓存
                                region_key = f"{emulator_name}_{region_name}"
                                self._save_capture(region_key, region_image)
                                
                                # 发送区域截图到队列
                                queue_manager.put({
                                    "type": "screenshot",
                                    "emulator": emulator_name,
                                    "region": region_name,
                                    "region_type": region.get("type", "unknown"),
                                    "image": region_image,
                                    "timestamp": datetime.now()
                                }, queue_name="screenshot")
                                
                                # 更新 FPS
                                self._update_fps()
                            
                            except Exception as e:
                                logger.error(f"处理区域 '{region_name}' 截图时出错: {e}")
                        
                        continue
                    
                    # 保存到缓存
                    self._save_capture(emulator_name, image)
                    
                    # 处理配置的监控区域
                    regions = emulator_config.get("regions", [])
                    for region in regions:
                        region_name = region.get("name", "未命名区域")
                        x, y = region.get("x", 0), region.get("y", 0)
                        width, height = region.get("width", 100), region.get("height", 100)
                        
                        # 从窗口截图中裁剪出区域
                        try:
                            if x + width <= image.shape[1] and y + height <= image.shape[0]:
                                region_image = image[y:y+height, x:x+width]
                                
                                # 保存区域截图到缓存
                                region_key = f"{emulator_name}_{region_name}"
                                self._save_capture(region_key, region_image)
                                
                                # 发送区域截图到队列
                                queue_manager.put({
                                    "type": "screenshot",
                                    "emulator": emulator_name,
                                    "region": region_name,
                                    "region_type": region.get("type", "unknown"),
                                    "image": region_image,
                                    "timestamp": datetime.now()
                                }, queue_name="screenshot")
                                
                                # 更新 FPS
                                self._update_fps()
                            else:
                                logger.warning(f"区域 '{region_name}' 超出窗口范围，无法捕获")
                        
                        except Exception as e:
                            logger.error(f"处理区域 '{region_name}' 截图时出错: {e}")
                    
                    # 发送窗口截图到队列
                    queue_manager.put({
                        "type": "screenshot",
                        "emulator": emulator_name,
                        "region": "full",
                        "image": image,
                        "timestamp": datetime.now()
                    }, queue_name="screenshot")
                    
                    # 更新 FPS
                    self._update_fps()
                
                except WindowNotFoundError:
                    logger.warning(f"未找到窗口: {window_title}")
                
                except Exception as e:
                    logger.error(f"捕获 '{emulator_name}' 屏幕时出错: {e}")
            
            # 控制捕获频率
            elapsed = time.time() - start_time
            if elapsed < self.capture_interval:
                time.sleep(self.capture_interval - elapsed)
    
    def _capture_window(self, window_title: str) -> np.ndarray:
        """
        捕获指定窗口的截图
        
        Args:
            window_title: 窗口标题
            
        Returns:
            np.ndarray: 窗口截图，BGR格式
            
        Raises:
            WindowNotFoundError: 如果找不到指定窗口
        """
        if sys.platform == 'win32':  # Windows
            return self._capture_window_win32(window_title)
        elif sys.platform == 'darwin':  # macOS
            return self._capture_window_macos(window_title)
        else:  # Linux
            return self._capture_window_linux(window_title)
    
    def _capture_window_win32(self, window_title: str) -> np.ndarray:
        """Windows平台下捕获指定窗口的截图"""
        # 查找窗口句柄
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            raise WindowNotFoundError(f"未找到窗口: {window_title}")
        
        # 获取窗口大小
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        # 创建设备上下文
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        # 创建位图对象
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # 复制窗口内容
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        
        # 转换为numpy数组
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        image = np.frombuffer(bmpstr, dtype='uint8')
        image.shape = (height, width, 4)
        
        # 释放资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        # 转换为BGR格式
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
        return image
    
    def _capture_window_macos(self, window_title: str) -> np.ndarray:
        """macOS平台下捕获指定窗口的截图"""
        # 获取所有窗口
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )
        
        # 查找目标窗口
        target_window = None
        for window in windows:
            if window.get(Quartz.kCGWindowName) == window_title:
                target_window = window
                break
        
        if not target_window:
            raise WindowNotFoundError(f"未找到窗口: {window_title}")
        
        # 获取窗口位置和大小
        bounds = target_window.get(Quartz.kCGWindowBounds)
        x = int(bounds.get('X', 0))
        y = int(bounds.get('Y', 0))
        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))
        
        # 创建截图
        image = Quartz.CGWindowListCreateImage(
            Quartz.CGRectMake(x, y, width, height),
            Quartz.kCGWindowListOptionOnScreenOnly,
            target_window.get(Quartz.kCGWindowNumber),
            Quartz.kCGWindowImageDefault
        )
        
        # 转换为PIL图像
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
        mode = "RGBA" if Quartz.CGImageGetAlphaInfo(image) else "RGB"
        
        pil_image = Image.frombytes(mode, (width, height), data)
        
        # 转换为numpy数组
        image = np.array(pil_image)
        
        # 转换为BGR格式
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        
        return image
    
    def _capture_window_linux(self, window_title: str) -> np.ndarray:
        """Linux平台下捕获指定窗口的截图"""
        # 获取所有窗口
        app = QGuiApplication.instance()
        if not app:
            app = QGuiApplication(sys.argv)
        
        # 查找目标窗口
        target_window = None
        for window in app.topLevelWindows():
            if window.windowTitle() == window_title:
                target_window = window
                break
        
        if not target_window:
            raise WindowNotFoundError(f"未找到窗口: {window_title}")
        
        # 获取窗口位置和大小
        geometry = target_window.geometry()
        x = geometry.x()
        y = geometry.y()
        width = geometry.width()
        height = geometry.height()
        
        # 创建截图
        screen = app.primaryScreen()
        if not screen:
            raise RuntimeError("无法获取主屏幕")
        
        pixmap = screen.grabWindow(0, x, y, width, height)
        
        # 转换为numpy数组
        image = pixmap.toImage()
        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(height * width * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        
        # 转换为BGR格式
        image = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        
        return image
    
    def _capture_screen(self) -> np.ndarray:
        """捕获整个屏幕的截图"""
        # 使用PIL的ImageGrab捕获屏幕
        screen = ImageGrab.grab()
        
        # 转换为numpy数组
        image = np.array(screen)
        
        # 转换为BGR格式
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        return image
    
    def _save_capture(self, key: str, image: np.ndarray) -> None:
        """
        保存截图到缓存
        
        Args:
            key: 缓存键
            image: 截图数据
        """
        with self.lock:
            self.last_captures[key] = {
                "image": image,
                "timestamp": datetime.now()
            }
    
    def get_last_capture(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取最近的截图
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Dict[str, Any]]: 截图数据，如果不存在则返回None
        """
        with self.lock:
            return self.last_captures.get(key)
    
    def save_screenshot(self, image: np.ndarray, 
                       prefix: str = "screenshot", save_path: Optional[Path] = None) -> str:
        """
        保存截图到文件
        
        Args:
            image: 截图数据
            prefix: 文件名前缀
            save_path: 保存路径，如果为None则使用默认路径
            
        Returns:
            str: 保存的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        
        # 确定保存路径
        if save_path is None:
            save_path = self.screenshot_path
        
        # 确保保存路径存在
        save_path.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = save_path / filename
        cv2.imwrite(str(file_path), image)
        
        return str(file_path)
    
    def update_config(self):
        """
        更新屏幕捕获配置
        """
        # 从配置管理器获取最新配置
        config = self.config_manager.get_config()
        
        # 更新截图路径
        self.screenshot_path = os.path.join(
            config.get("paths.screenshots", os.path.join(os.getcwd(), "screenshots")),
            datetime.now().strftime("%Y%m%d")
        )
        
        # 更新捕获参数
        self.capture_interval = float(config.get("timing.capture_interval_ms", 2000)) / 1000.0
        self.capture_quality = int(config.get("capture.quality", 80))
        self.capture_method = config.get("capture.method", "window")
        
        # 确保截图目录存在
        os.makedirs(self.screenshot_path, exist_ok=True)
        
        logger.debug(f"屏幕捕获配置已更新: 间隔={self.capture_interval}秒, 质量={self.capture_quality}, 方法={self.capture_method}")
    
    def capture(self, region: Optional[Dict[str, int]] = None) -> Optional[QImage]:
        """
        捕获屏幕或指定区域
        
        参数:
            region: 区域信息，格式为 {"top": y, "left": x, "width": w, "height": h}
                   如果为None，则捕获整个屏幕
            
        返回:
            QImage: 捕获的图像，如果失败则返回None
        """
        try:
            # 检查捕获间隔
            current_time = time.time()
            if current_time - self.last_capture_time < self.capture_interval:
                return self.last_capture
            
            # 获取屏幕信息
            monitor = self.sct.monitors[1]  # 主显示器
            if region:
                # 计算实际捕获区域
                capture_region = {
                    "top": monitor["top"] + region.get("top", 0),
                    "left": monitor["left"] + region.get("left", 0),
                    "width": region.get("width", monitor["width"]),
                    "height": region.get("height", monitor["height"])
                }
            else:
                capture_region = monitor
            
            # 捕获屏幕
            screenshot = self.sct.grab(capture_region)
            
            # 转换为QImage
            img = QImage(
                screenshot.rgb,
                screenshot.width,
                screenshot.height,
                screenshot.width * 3,
                QImage.Format.Format_RGB888
            )
            
            # 更新状态
            self.last_capture_time = current_time
            self.last_capture = img
            
            return img
            
        except Exception as e:
            logger.error(f"屏幕捕获失败: {e}")
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[QImage]:
        """
        捕获指定区域
        
        参数:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            
        返回:
            QImage: 捕获的图像，如果失败则返回None
        """
        region = {
            "top": y,
            "left": x,
            "width": width,
            "height": height
        }
        return self.capture(region)
    
    def get_screen_size(self) -> Dict[str, int]:
        """
        获取屏幕尺寸
        
        返回:
            Dict[str, int]: 屏幕尺寸信息
        """
        try:
            monitor = self.sct.monitors[1]  # 主显示器
            return {
                "width": monitor["width"],
                "height": monitor["height"]
            }
        except Exception as e:
            logger.error(f"获取屏幕尺寸失败: {e}")
            return {"width": 0, "height": 0}
    
    def get_available_monitors(self) -> list:
        """
        获取可用显示器列表
        
        返回:
            list: 显示器信息列表
        """
        try:
            monitors = []
            for i, monitor in enumerate(self.sct.monitors):
                if i == 0:  # 跳过所有显示器的组合
                    continue
                monitors.append({
                    "id": i,
                    "name": f"显示器 {i}",
                    "width": monitor["width"],
                    "height": monitor["height"],
                    "top": monitor["top"],
                    "left": monitor["left"]
                })
            return monitors
        except Exception as e:
            logger.error(f"获取显示器列表失败: {e}")
            return []
    
    def set_capture_interval(self, interval: float):
        """
        设置捕获间隔
        
        参数:
            interval: 捕获间隔（秒）
        """
        self.capture_interval = max(0.1, interval) 