#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR引擎模块

提供文本识别功能，支持多种OCR引擎，包括PaddleOCR和Tesseract。
可以识别图像中的文本，并支持不同的语言和预处理选项。
"""

import os
import sys
import cv2
import time
import threading
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import queue

from src.utils.logger_utils import logger
from src.utils.queue_manager import queue_manager

# 导入OCR引擎
try:
    from paddleocr import PaddleOCR
    paddle_available = True
except ImportError:
    paddle_available = False
    logger.warning("PaddleOCR未安装，将使用Tesseract作为备选OCR引擎")

try:
    import pytesseract
    tesseract_available = True
except ImportError:
    tesseract_available = False
    logger.error("Tesseract未安装，请安装pytesseract和Tesseract-OCR")


class OCREngine:
    """OCR引擎类，用于文本识别"""
    
    def __init__(self, config_manager):
        """
        初始化OCR引擎
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.running = False
        self.ocr_thread = None
        self.lock = threading.RLock()
        
        # 读取配置
        self.engine_type = config_manager.get_config().get("ocr", {}).get("engine", "tesseract")
        self.language = config_manager.get_config().get("ocr", {}).get("language", "zh")
        self.confidence_threshold = config_manager.get_config().get("ocr", {}).get("confidence_threshold", 0.6)
        self.use_gpu = config_manager.get_config().get("ocr", {}).get("use_gpu", False)
        self.num_threads = config_manager.get_config().get("ocr", {}).get("num_threads", 4)
        self.batch_size = config_manager.get_config().get("ocr", {}).get("batch_size", 1)
        
        # OCR引擎实例
        self.paddle_ocr = None
        
        # 初始化引擎
        self._init_engine()
        
        # 注册截图队列监听
        queue_manager.start_listener("screenshot", self._process_screenshot)
        
        logger.debug("OCR引擎初始化完成")
    
    def _init_engine(self) -> None:
        """初始化OCR引擎"""
        if self.engine_type == "paddle":
            if not paddle_available:
                logger.warning("PaddleOCR不可用，自动切换到Tesseract")
                self.engine_type = "tesseract"
                self.config_manager.set_config("ocr.engine", "tesseract")
            else:
                try:
                    # 获取PaddleOCR配置
                    paddle_config = self.config_manager.get_config().get("ocr", {}).get("paddle", {})
                    
                    # 初始化PaddleOCR
                    self.paddle_ocr = PaddleOCR(
                        use_angle_cls=paddle_config.get("use_cls", True),
                        lang=self.language,
                        use_gpu=self.use_gpu,
                        show_log=False,
                        model_dir=paddle_config.get("model_dir", ""),
                        use_det=paddle_config.get("use_det", True),
                        use_server_mode=paddle_config.get("use_server_mode", False)
                    )
                    logger.info("PaddleOCR引擎初始化成功")
                except Exception as e:
                    logger.error(f"PaddleOCR引擎初始化失败: {e}")
                    logger.warning("自动切换到Tesseract")
                    self.engine_type = "tesseract"
                    self.config_manager.set_config("ocr.engine", "tesseract")
        
        if self.engine_type == "tesseract":
            if not tesseract_available:
                logger.error("Tesseract不可用，请安装pytesseract和Tesseract-OCR")
                return
            
            # 获取Tesseract配置
            tesseract_config = self.config_manager.get_config().get("ocr", {}).get("tesseract", {})
            
            # 检查Tesseract路径
            if sys.platform == 'win32':
                # Windows需要设置Tesseract路径
                tesseract_path = tesseract_config.get("executable_path", "")
                if tesseract_path and os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    logger.info(f"已设置Tesseract路径: {tesseract_path}")
                else:
                    # 尝试默认安装路径
                    default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                    if os.path.exists(default_path):
                        pytesseract.pytesseract.tesseract_cmd = default_path
                        logger.info(f"使用默认Tesseract路径: {default_path}")
                        # 更新配置
                        self.config_manager.set_config("ocr.tesseract.executable_path", default_path)
                    else:
                        logger.warning("未找到Tesseract路径，请设置Tesseract路径")
                        # 检查环境变量
                        tesseract_env = os.environ.get("TESSERACT_PATH", "")
                        if tesseract_env and os.path.exists(tesseract_env):
                            pytesseract.pytesseract.tesseract_cmd = tesseract_env
                            logger.info(f"从环境变量设置Tesseract路径: {tesseract_env}")
                            # 更新配置
                            self.config_manager.set_config("ocr.tesseract.executable_path", tesseract_env)
            
            # 设置Tesseract数据目录
            tessdata_dir = tesseract_config.get("tessdata_dir", "")
            if tessdata_dir and os.path.exists(tessdata_dir):
                os.environ['TESSDATA_PREFIX'] = tessdata_dir
                logger.info(f"已设置Tesseract数据目录: {tessdata_dir}")
            
            logger.info("Tesseract OCR引擎已准备就绪")
        
        else:
            logger.error(f"不支持的OCR引擎类型: {self.engine_type}")
            logger.warning("自动切换到Tesseract")
            self.engine_type = "tesseract"
            self.config_manager.set_config("ocr.engine", "tesseract")
            self._init_engine()  # 重新初始化Tesseract
    
    def start_ocr(self) -> bool:
        """
        启动OCR处理线程
        
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            logger.warning("OCR引擎已在运行")
            return False
        
        self.running = True
        self.ocr_thread = threading.Thread(
            target=self._ocr_loop,
            daemon=True
        )
        self.ocr_thread.start()
        logger.info("OCR处理线程已启动")
        return True
    
    def stop_ocr(self) -> None:
        """停止OCR处理线程"""
        self.running = False
        if self.ocr_thread and self.ocr_thread.is_alive():
            self.ocr_thread.join(timeout=2.0)
        logger.info("OCR处理线程已停止")
    
    def _ocr_loop(self) -> None:
        """OCR处理线程主循环"""
        logger.debug("OCR处理循环开始")
        
        batch_size = self.batch_size
        batch_data = []
        last_process_time = time.time()
        max_batch_wait = 0.2  # 最大批处理等待时间（秒）
        error_count = 0  # 错误计数
        max_errors = 5  # 最大错误次数
        error_cooldown = 10.0  # 错误冷却时间（秒）
        last_error_time = 0  # 上次错误时间
        
        while self.running:
            try:
                # 从队列获取数据，增加超时时间
                success, data = queue_manager.get("ocr_task", timeout=0.2)
                if success:
                    batch_data.append(data)
                
                current_time = time.time()
                # 当批次满或等待时间超过阈值时处理
                if len(batch_data) >= batch_size or (current_time - last_process_time >= max_batch_wait and batch_data):
                    for task in batch_data:
                        try:
                            image = task.get("image")
                            task_id = task.get("task_id", "unknown")
                            region_type = task.get("region_type", "unknown")
                            
                            start_time = time.time()
                            ocr_result = self.recognize_text(image, region_type)
                            processing_time = time.time() - start_time
                            
                            # 发送结果到结果队列
                            result_data = {
                                "type": "ocr_result",
                                "task_id": task_id,
                                "region_type": region_type,
                                "result": ocr_result,
                                "processing_time": processing_time,
                                "timestamp": datetime.now()
                            }
                            queue_manager.put(result_data, queue_name="ocr_result", timeout=1.0)
                            
                            logger.debug(f"OCR处理完成，任务ID: {task_id}，耗时: {processing_time:.3f}秒")
                            error_count = 0  # 重置错误计数
                        
                        except Exception as e:
                            error_count += 1
                            current_time = time.time()
                            
                            # 检查是否需要重置错误计数（冷却时间已过）
                            if current_time - last_error_time >= error_cooldown:
                                error_count = 1
                                last_error_time = current_time
                            
                            logger.error(f"OCR处理失败: {e}")
                            # 发送错误结果
                            error_data = {
                                "type": "ocr_error",
                                "task_id": task.get("task_id", "unknown"),
                                "error": str(e),
                                "timestamp": datetime.now()
                            }
                            queue_manager.put(error_data, queue_name="ocr_result", timeout=1.0)
                            
                            # 如果错误次数过多，等待一段时间
                            if error_count >= max_errors:
                                wait_time = min(1.0 * error_count, 5.0)  # 最多等待5秒
                                time.sleep(wait_time)
                    
                    batch_data = []
                    last_process_time = current_time
            
            except Exception as e:
                logger.error(f"OCR循环发生错误: {e}")
                time.sleep(0.5)  # 防止因错误导致的CPU占用过高
        
        logger.debug("OCR处理循环结束")
    
    def _process_screenshot(self, data: Dict[str, Any]) -> None:
        """
        处理截图数据
        
        Args:
            data: 截图数据
        """
        if not self.running:
            return
        
        # 只处理区域类型为特定类型的截图
        region_type = data.get("region_type", "unknown")
        if region_type not in ["ship_status", "chat", "target"]:
            return
        
        # 创建OCR任务
        ocr_task = {
            "type": "ocr_task",
            "task_id": f"{data.get('emulator', 'unknown')}_{data.get('region', 'unknown')}_{time.time()}",
            "image": data.get("image"),
            "region_type": region_type,
            "timestamp": data.get("timestamp")
        }
        
        # 提交到OCR任务队列，设置超时
        try:
            queue_manager.put(ocr_task, queue_name="ocr_task", timeout=2.0)
        except queue.Full:
            logger.warning("OCR任务队列已满，丢弃任务")
    
    def recognize_text(self, image: np.ndarray, 
                      region_type: str = "unknown") -> List[Dict[str, Any]]:
        """
        识别图像中的文本
        
        Args:
            image: 图像数据，BGR格式
            region_type: 区域类型，用于选择不同的预处理方法
            
        Returns:
            List[Dict[str, Any]]: OCR结果列表，每项包含文本和位置信息
        """
        if image is None or image.size == 0:
            logger.warning("OCR输入图像为空")
            return []
        
        # 根据区域类型进行图像预处理
        processed_image = self._preprocess_image(image, region_type)
        
        # 使用选择的OCR引擎进行识别
        if self.engine_type == "paddle" and self.paddle_ocr:
            return self._recognize_with_paddle(processed_image)
        elif self.engine_type == "tesseract" and tesseract_available:
            return self._recognize_with_tesseract(processed_image)
        else:
            logger.error(f"OCR引擎 {self.engine_type} 不可用")
            return []
    
    def _preprocess_image(self, image: np.ndarray, region_type: str) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像
            region_type: 区域类型
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        # 获取预处理配置
        preprocess_config = self.config_manager.get_config().get("ocr", {}).get("preprocess", {})
        
        # 根据区域类型选择预处理方法
        if region_type == "ship_status":
            # 舰船状态区域预处理
            # 1. 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 3. 降噪
            denoised = cv2.fastNlMeansDenoising(binary)
            
            return denoised
            
        elif region_type == "chat":
            # 聊天区域预处理
            # 1. 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. 高斯模糊
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 3. 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return binary
            
        elif region_type == "target":
            # 目标信息区域预处理
            # 1. 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. 直方图均衡化
            equalized = cv2.equalizeHist(gray)
            
            # 3. 高斯模糊
            blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
            
            # 4. 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return binary
            
        else:
            # 默认预处理
            # 1. 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. 高斯模糊
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 3. 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return binary
    
    def _recognize_with_paddle(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        使用PaddleOCR识别文本
        
        Args:
            image: 预处理后的图像
            
        Returns:
            List[Dict[str, Any]]: OCR结果列表
        """
        try:
            # 使用PaddleOCR识别
            result = self.paddle_ocr.ocr(image, cls=True)
            
            # 处理识别结果
            ocr_results = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 识别的文本
                    confidence = item[1][1]  # 置信度
                    
                    # 过滤低置信度的结果
                    if confidence < self.confidence_threshold:
                        continue
                    
                    # 获取文本框坐标
                    points = item[0]
                    x1, y1 = points[0]
                    x2, y2 = points[1]
                    x3, y3 = points[2]
                    x4, y4 = points[3]
                    
                    # 计算边界框
                    bbox = {
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2),
                        "x3": int(x3),
                        "y3": int(y3),
                        "x4": int(x4),
                        "y4": int(y4)
                    }
                    
                    ocr_results.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox
                    })
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"PaddleOCR识别失败: {e}")
            return []
    
    def _recognize_with_tesseract(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        使用Tesseract识别文本
        
        Args:
            image: 预处理后的图像
            
        Returns:
            List[Dict[str, Any]]: OCR结果列表
        """
        try:
            # 获取Tesseract配置
            tesseract_config = self.config_manager.get_config().get("ocr", {}).get("tesseract", {})
            
            # 使用Tesseract识别
            result = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=tesseract_config.get("config", ""),
                output_type=pytesseract.Output.DICT
            )
            
            # 处理识别结果
            ocr_results = []
            n_boxes = len(result['text'])
            for i in range(n_boxes):
                # 过滤空文本和低置信度的结果
                if not result['text'][i].strip() or result['conf'][i] < self.confidence_threshold * 100:
                    continue
                
                # 获取文本框坐标
                x = result['left'][i]
                y = result['top'][i]
                w = result['width'][i]
                h = result['height'][i]
                
                # 计算边界框
                bbox = {
                    "x1": x,
                    "y1": y,
                    "x2": x + w,
                    "y2": y,
                    "x3": x + w,
                    "y3": y + h,
                    "x4": x,
                    "y4": y + h
                }
                
                ocr_results.append({
                    "text": result['text'][i].strip(),
                    "confidence": result['conf'][i] / 100.0,
                    "bbox": bbox
                })
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"Tesseract识别失败: {e}")
            return []
    
    def update_config(self):
        """
        更新OCR引擎配置
        """
        logger.debug("更新OCR引擎配置")
        
        # 从配置管理器获取最新配置
        config = self.config_manager.get_config()
        
        # 更新OCR引擎配置
        self.engine_type = config.get("ocr.engine", "paddle")
        self.language = config.get("ocr.language", "ch")
        self.confidence_threshold = float(config.get("ocr.confidence_threshold", 0.6))
        
        # 获取引擎特定配置
        if self.engine_type == "paddle":
            paddle_config = config.get("ocr.paddle", {})
            self.use_gpu = paddle_config.get("use_gpu", False)
            # 其他PaddleOCR特定配置...
        elif self.engine_type == "tesseract":
            # Tesseract特定配置...
            pass
        
        # 重新初始化引擎
        self._init_engine()
        
        logger.debug(f"OCR引擎配置已更新: {self.engine_type}, {self.language}, {self.confidence_threshold}") 