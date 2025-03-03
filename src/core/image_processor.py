#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图像处理模块

负责对截图进行预处理，优化OCR识别结果。
针对不同区域类型提供不同的处理方法。
"""

import cv2
import numpy as np
import threading
from typing import Dict, List, Any, Optional, Union, Tuple

from src.utils.logger_utils import logger


class ImageProcessor:
    """图像处理器，用于预处理截图"""
    
    def __init__(self, config_manager):
        """
        初始化图像处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.lock = threading.RLock()
        
        # 加载配置
        self.update_config()
        
        logger.debug("图像处理器初始化完成")
    
    def update_config(self):
        """
        更新图像处理器配置
        """
        with self.lock:
            # 从配置管理器获取最新配置
            config = self.config_manager.get_config()
            
            # 更新处理器配置
            self.debug_mode = config.get("debug.enabled", False)
            self.save_debug_images = config.get("debug.save_images", False)
            
            # 设置默认阈值
            self.thresholds = {
                "text": float(config.get("processor.threshold.text", 127)),
                "ship": float(config.get("processor.threshold.ship", 150)),
                "target": float(config.get("processor.threshold.target", 140)),
                "system": float(config.get("processor.threshold.system", 130))
            }
            
            logger.debug(f"图像处理器配置已更新: 调试模式={self.debug_mode}, 保存调试图像={self.save_debug_images}")
    
    def process_image(self, image: np.ndarray, region_type: str = "default") -> np.ndarray:
        """
        处理图像
        
        Args:
            image: 原始图像数据
            region_type: 区域类型，如 "ship_status", "chat", "target", "system"
            
        Returns:
            np.ndarray: 处理后的图像
        """
        if image is None or image.size == 0:
            logger.error("无效的图像数据")
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        try:
            # 选择合适的处理方法
            if region_type == "ship_status":
                return self._process_ship_status(image)
            elif region_type == "chat":
                return self._process_chat(image)
            elif region_type == "target":
                return self._process_target(image)
            elif region_type == "system":
                return self._process_system(image)
            else:
                return self._process_default(image)
        
        except Exception as e:
            logger.error(f"处理图像时发生错误: {e}")
            return image  # 出错时返回原始图像
    
    def _process_default(self, image: np.ndarray) -> np.ndarray:
        """
        默认图像处理
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 基本增强
        enhanced = self._enhance_image(gray)
        
        # 二值化
        threshold = self.thresholds.get("text", 127)
        _, binary = cv2.threshold(enhanced, threshold, 255, cv2.THRESH_BINARY)
        
        # 移除噪点
        clean = self._remove_noise(binary)
        
        return clean
    
    def _process_ship_status(self, image: np.ndarray) -> np.ndarray:
        """
        处理舰船状态区域
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 增强对比度
        alpha = 1.2
        beta = 10
        enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        
        # 自适应二值化
        threshold = self.thresholds.get("ship", 150)
        binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 移除噪点
        clean = self._remove_noise(binary)
        
        return clean
    
    def _process_chat(self, image: np.ndarray) -> np.ndarray:
        """
        处理聊天区域
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            # 提取通道，增强文字
            b, g, r = cv2.split(image)
            # 聊天文字通常是白色的，在深色背景上
            # 增强亮度差异
            enhanced_r = cv2.convertScaleAbs(r, alpha=1.5, beta=0)
            enhanced_g = cv2.convertScaleAbs(g, alpha=1.5, beta=0)
            enhanced_b = cv2.convertScaleAbs(b, alpha=1.1, beta=0)
            
            # 合并通道
            enhanced = cv2.merge([enhanced_b, enhanced_g, enhanced_r])
            
            # 转换为灰度
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 高斯模糊去噪
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 二值化
        threshold = self.thresholds.get("target", 140)
        _, binary = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
        
        # 移除噪点
        clean = self._remove_noise(binary)
        
        return clean
    
    def _process_target(self, image: np.ndarray) -> np.ndarray:
        """
        处理目标区域
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 增强对比度
        enhanced = self._enhance_image(gray, alpha=1.3, beta=15)
        
        # 二值化
        threshold = self.thresholds.get("target", 140)
        _, binary = cv2.threshold(enhanced, threshold, 255, cv2.THRESH_BINARY)
        
        # 移除噪点
        clean = self._remove_noise(binary)
        
        return clean
    
    def _process_system(self, image: np.ndarray) -> np.ndarray:
        """
        处理星系信息区域
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 锐化图像
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        
        # 增强对比度
        enhanced = self._enhance_image(sharpened, alpha=1.4, beta=10)
        
        # 二值化
        threshold = self.thresholds.get("system", 130)
        _, binary = cv2.threshold(enhanced, threshold, 255, cv2.THRESH_BINARY)
        
        # 移除噪点
        clean = self._remove_noise(binary)
        
        return clean
    
    def _enhance_image(self, image: np.ndarray, alpha: Optional[float] = None, 
                      beta: Optional[float] = None, gamma: Optional[float] = None) -> np.ndarray:
        """
        增强图像
        
        Args:
            image: 原始图像
            alpha: 对比度
            beta: 亮度
            gamma: 伽马值
            
        Returns:
            np.ndarray: 增强后的图像
        """
        # 使用默认值或传入值
        alpha = alpha or 1.2
        beta = beta or 10
        gamma = gamma or 1.0
        
        # 对比度和亮度调整
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        
        # 伽马校正（如果需要）
        if gamma != 1.0:
            # 构建查找表
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
            # 应用伽马校正
            return cv2.LUT(adjusted, table)
        
        return adjusted
    
    def _remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        移除图像噪点
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 去噪后的图像
        """
        kernel_size = 3
        iterations = 1
        
        # 创建核
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        
        # 开操作（先腐蚀后膨胀）去除小噪点
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=iterations)
        
        return opening
    
    def scale_image(self, image: np.ndarray) -> np.ndarray:
        """
        缩放图像
        
        Args:
            image: 原始图像
            
        Returns:
            np.ndarray: 缩放后的图像
        """
        scale_factor = 1.5
        
        if scale_factor == 1.0:
            return image
        
        # 计算新尺寸
        height, width = image.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # 缩放图像
        scaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return scaled
    
    def extract_regions(self, image: np.ndarray, regions: Dict[str, Dict[str, int]]) -> Dict[str, np.ndarray]:
        """
        从图像中提取指定区域
        
        Args:
            image: 原始图像
            regions: 区域定义，格式为 {"region_name": {"x": x, "y": y, "width": w, "height": h}}
            
        Returns:
            Dict[str, np.ndarray]: 提取的区域
        """
        extracted = {}
        
        for name, coords in regions.items():
            try:
                x = coords.get("x", 0)
                y = coords.get("y", 0)
                width = coords.get("width", 100)
                height = coords.get("height", 100)
                
                # 检查边界
                img_height, img_width = image.shape[:2]
                
                if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
                    logger.warning(f"区域 {name} 超出图像边界，调整坐标")
                    
                    # 调整坐标以适应图像边界
                    x = max(0, min(x, img_width - 1))
                    y = max(0, min(y, img_height - 1))
                    width = min(width, img_width - x)
                    height = min(height, img_height - y)
                
                # 提取区域
                region = image[y:y+height, x:x+width]
                extracted[name] = region
                
            except Exception as e:
                logger.error(f"提取区域 {name} 时发生错误: {e}")
        
        return extracted
    
    def detect_text_regions(self, image: np.ndarray) -> List[Dict[str, int]]:
        """
        检测图像中的文本区域
        
        Args:
            image: 原始图像
            
        Returns:
            List[Dict[str, int]]: 文本区域坐标列表
        """
        # 转换为灰度图
        if len(image.shape) > 2 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 二值化
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # 形态学操作，连接相邻文本
        kernel = np.ones((5, 20), np.uint8)  # 水平方向的核
        connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤和提取文本区域
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 过滤太小的区域
            if w < 40 or h < 10:
                continue
            
            # 添加区域
            text_regions.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h
            })
        
        return text_regions
    
    def create_debug_image(self, image: np.ndarray, detected_regions: List[Dict[str, int]] = None, 
                         regions: Dict[str, Dict[str, int]] = None) -> np.ndarray:
        """
        创建调试图像，标记检测到的区域
        
        Args:
            image: 原始图像
            detected_regions: 检测到的区域列表
            regions: 已定义的区域
            
        Returns:
            np.ndarray: 调试图像
        """
        # 创建彩色图像副本
        if len(image.shape) > 2 and image.shape[2] == 3:
            debug_img = image.copy()
        else:
            debug_img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # 绘制检测到的区域
        if detected_regions:
            for region in detected_regions:
                x = region.get("x", 0)
                y = region.get("y", 0)
                width = region.get("width", 0)
                height = region.get("height", 0)
                
                # 使用绿色矩形标记检测到的区域
                cv2.rectangle(debug_img, (x, y), (x + width, y + height), (0, 255, 0), 2)
        
        # 绘制预定义区域
        if regions:
            for name, coords in regions.items():
                x = coords.get("x", 0)
                y = coords.get("y", 0)
                width = coords.get("width", 0)
                height = coords.get("height", 0)
                
                # 使用蓝色矩形标记预定义区域
                cv2.rectangle(debug_img, (x, y), (x + width, y + height), (255, 0, 0), 2)
                
                # 添加区域名称
                cv2.putText(debug_img, name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        return debug_img 