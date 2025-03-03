#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知模块

负责发送各种通知，支持系统通知、钉钉、企业微信等平台。
根据配置的通知级别和频率控制通知发送。
"""

import os
import time
import json
import base64
import threading
import hmac
import hashlib
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import platform

import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np

from src.utils.logger_utils import logger


class NotificationManager:
    """通知管理器，处理各种通知渠道"""
    
    def __init__(self, config_manager):
        """
        初始化通知管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.lock = threading.RLock()
        
        # 加载配置
        self.update_config()
        
        # 通知历史和限流
        self.notification_history = {}
        self.last_cleanup = time.time()
        
        # 统计
        self.stats = {
            "total_sent": 0,
            "throttled": 0,
            "failed": 0,
            "by_channel": {},
            "by_level": {}
        }
        
        logger.debug("通知管理器初始化完成")
    
    def update_config(self) -> None:
        """更新配置"""
        with self.lock:
            # 读取配置
            config = self.config_manager.get_config()
            
            # 通知配置
            self.notification_config = config.get("notification", {})
            
            # 全局设置
            self.enabled = self.notification_config.get("enabled", True)
            self.min_level = self.notification_config.get("min_level", "info")
            self.throttle_seconds = self.notification_config.get("throttle_seconds", 60)
            self.max_per_minute = self.notification_config.get("max_per_minute", 10)
            
            # 通道配置
            self.channels = {}
            
            # 系统通知
            system_config = self.notification_config.get("system", {})
            if system_config.get("enabled", True):
                self.channels["system"] = system_config
            
            # 钉钉
            dingtalk_config = self.notification_config.get("dingtalk", {})
            if dingtalk_config.get("enabled", False) and dingtalk_config.get("webhook_url"):
                self.channels["dingtalk"] = dingtalk_config
            
            # 企业微信
            wechat_config = self.notification_config.get("wechat", {})
            if wechat_config.get("enabled", False) and wechat_config.get("webhook_url"):
                self.channels["wechat"] = wechat_config
            
            # Slack
            slack_config = self.notification_config.get("slack", {})
            if slack_config.get("enabled", False) and slack_config.get("webhook_url"):
                self.channels["slack"] = slack_config
            
            # Discord
            discord_config = self.notification_config.get("discord", {})
            if discord_config.get("enabled", False) and discord_config.get("webhook_url"):
                self.channels["discord"] = discord_config
            
            # 自定义Webhook
            webhook_config = self.notification_config.get("webhook", {})
            if webhook_config.get("enabled", False) and webhook_config.get("url"):
                self.channels["webhook"] = webhook_config
            
            logger.debug(f"已更新通知配置，启用的通道: {list(self.channels.keys())}")
    
    def send_notification(self, title: str, message: str, level: str = "info", 
                         image: Optional[np.ndarray] = None, 
                         data: Optional[Dict[str, Any]] = None) -> bool:
        """
        发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            level: 通知级别 (debug, info, warning, error, critical)
            image: 可选的图像数据
            data: 附加数据
            
        Returns:
            bool: 是否成功发送
        """
        if not self.enabled:
            logger.debug(f"通知已禁用，跳过: {title}")
            return False
        
        # 检查通知级别
        if not self._check_level(level):
            logger.debug(f"通知级别低于最小级别，跳过: {level} < {self.min_level}")
            return False
        
        # 检查限流
        if not self._check_throttle(title, level):
            with self.lock:
                self.stats["throttled"] += 1
            logger.debug(f"通知已限流，跳过: {title}")
            return False
        
        # 准备通知数据
        notification_data = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now(),
            "data": data or {}
        }
        
        # 处理图像
        image_path = None
        if image is not None:
            try:
                image_path = self._save_notification_image(image, title)
                notification_data["image_path"] = image_path
            except Exception as e:
                logger.error(f"保存通知图像失败: {e}")
        
        # 发送到各个通道
        success = False
        for channel_name, channel_config in self.channels.items():
            try:
                if self._send_to_channel(channel_name, notification_data, channel_config):
                    success = True
                    with self.lock:
                        self.stats["by_channel"][channel_name] = self.stats["by_channel"].get(channel_name, 0) + 1
            except Exception as e:
                logger.error(f"通过{channel_name}发送通知失败: {e}")
        
        # 更新统计
        with self.lock:
            if success:
                self.stats["total_sent"] += 1
                self.stats["by_level"][level] = self.stats["by_level"].get(level, 0) + 1
            else:
                self.stats["failed"] += 1
        
        # 定期清理历史记录
        self._cleanup_history()
        
        return success
    
    def _save_notification_image(self, image: np.ndarray, title: str) -> str:
        """
        保存通知图像
        
        Args:
            image: 图像数据
            title: 通知标题
            
        Returns:
            str: 保存的文件路径
        """
        # 创建通知图像目录
        notification_dir = Path("screenshots") / "notifications"
        notification_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in title)[:30]
        file_name = f"{timestamp}_{safe_title}.png"
        file_path = notification_dir / file_name
        
        # 保存图像
        cv2.imwrite(str(file_path), image)
        
        return str(file_path)
    
    def _send_to_channel(self, channel_name: str, notification_data: Dict[str, Any], 
                        channel_config: Dict[str, Any]) -> bool:
        """
        发送到指定通道
        
        Args:
            channel_name: 通道名称
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        # 检查通道特定的级别限制
        channel_min_level = channel_config.get("min_level", self.min_level)
        if not self._check_specific_level(notification_data["level"], channel_min_level):
            return False
        
        # 根据通道类型分发
        if channel_name == "system":
            return self._send_system_notification(notification_data, channel_config)
        elif channel_name == "dingtalk":
            return self._send_dingtalk(notification_data, channel_config)
        elif channel_name == "wechat":
            return self._send_wechat(notification_data, channel_config)
        elif channel_name == "slack":
            return self._send_slack(notification_data, channel_config)
        elif channel_name == "discord":
            return self._send_discord(notification_data, channel_config)
        elif channel_name == "webhook":
            return self._send_webhook(notification_data, channel_config)
        else:
            logger.warning(f"未知的通知通道: {channel_name}")
            return False
    
    def _send_system_notification(self, notification_data: Dict[str, Any], 
                                channel_config: Dict[str, Any]) -> bool:
        """
        发送系统通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        title = notification_data["title"]
        message = notification_data["message"]
        
        try:
            # 根据平台选择不同的通知方式
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # 使用osascript发送通知
                os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
                return True
                
            elif system == "Windows":
                # 使用win10toast发送通知（需要先安装）
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                    return True
                except ImportError:
                    # 回退到简单的Windows通知
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(0, message, title, 0)
                    return True
                    
            elif system == "Linux":
                # 使用notify-send发送通知
                icon_path = ""
                if "image_path" in notification_data:
                    icon_path = f"-i {notification_data['image_path']}"
                    
                os.system(f'notify-send {icon_path} "{title}" "{message}"')
                return True
                
            else:
                logger.warning(f"不支持的系统类型: {system}")
                return False
                
        except Exception as e:
            logger.error(f"发送系统通知失败: {e}")
            return False
    
    def _send_dingtalk(self, notification_data: Dict[str, Any], 
                      channel_config: Dict[str, Any]) -> bool:
        """
        发送钉钉通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        webhook_url = channel_config.get("webhook_url")
        secret = channel_config.get("secret", "")
        
        if not webhook_url:
            logger.error("钉钉Webhook URL未配置")
            return False
        
        # 准备签名
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(secret.encode(), string_to_sign.encode(), digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        
        # 构建消息
        title = notification_data["title"]
        message = notification_data["message"]
        level = notification_data["level"]
        timestamp = notification_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据级别设置颜色
        color = self._get_level_color(level)
        
        # 构建标准的钉钉卡片消息
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n" +
                        f"> {message}\n\n" +
                        f"**级别**: {level.upper()}\n" +
                        f"**时间**: {timestamp}\n"
            },
            "at": {
                "isAtAll": level in ["critical", "error"]
            }
        }
        
        # 添加图片（如果有）
        if "image_path" in notification_data and channel_config.get("send_image", True):
            try:
                image_path = notification_data["image_path"]
                if os.path.exists(image_path):
                    # 钉钉不支持直接在markdown中嵌入本地图片，需要另外发送图片消息
                    # 这里我们只在消息中添加图片路径的提示
                    payload["markdown"]["text"] += f"\n\n> 图片已保存到: {image_path}"
            except Exception as e:
                logger.error(f"处理钉钉通知图片失败: {e}")
        
        # 发送请求
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return True
                else:
                    logger.error(f"钉钉返回错误: {result}")
            else:
                logger.error(f"钉钉请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            return False
    
    def _send_wechat(self, notification_data: Dict[str, Any], 
                    channel_config: Dict[str, Any]) -> bool:
        """
        发送企业微信通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        webhook_url = channel_config.get("webhook_url")
        
        if not webhook_url:
            logger.error("企业微信Webhook URL未配置")
            return False
        
        # 构建消息
        title = notification_data["title"]
        message = notification_data["message"]
        level = notification_data["level"]
        timestamp = notification_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据企业微信的消息格式构建
        content = f"### {title}\n" + \
                 f"> {message}\n\n" + \
                 f"**级别**: {level.upper()}\n" + \
                 f"**时间**: {timestamp}\n"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        # 添加图片（如果有）
        if "image_path" in notification_data and channel_config.get("send_image", True):
            try:
                image_path = notification_data["image_path"]
                if os.path.exists(image_path):
                    # 企业微信不支持直接在markdown中嵌入本地图片，需要另外发送图片消息
                    # 这里我们只在消息中添加图片路径的提示
                    payload["markdown"]["content"] += f"\n\n> 图片已保存到: {image_path}"
            except Exception as e:
                logger.error(f"处理企业微信通知图片失败: {e}")
        
        # 发送请求
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return True
                else:
                    logger.error(f"企业微信返回错误: {result}")
            else:
                logger.error(f"企业微信请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {e}")
            return False
    
    def _send_slack(self, notification_data: Dict[str, Any], 
                   channel_config: Dict[str, Any]) -> bool:
        """
        发送Slack通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        webhook_url = channel_config.get("webhook_url")
        
        if not webhook_url:
            logger.error("Slack Webhook URL未配置")
            return False
        
        # 构建消息
        title = notification_data["title"]
        message = notification_data["message"]
        level = notification_data["level"]
        timestamp = notification_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据级别设置颜色
        color = self._get_slack_color(level)
        
        # 构建Slack消息
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*消息*: {message}\n*级别*: {level.upper()}\n*时间*: {timestamp}"
                    }
                }
            ]
        }
        
        # 添加图片（如果有）
        if "image_path" in notification_data and channel_config.get("send_image", True):
            try:
                image_path = notification_data["image_path"]
                if os.path.exists(image_path):
                    # Slack不支持直接附加本地图片
                    payload["blocks"].append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*图片已保存到*: {image_path}"
                        }
                    })
            except Exception as e:
                logger.error(f"处理Slack通知图片失败: {e}")
        
        # 发送请求
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Slack请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"发送Slack通知失败: {e}")
            return False
    
    def _send_discord(self, notification_data: Dict[str, Any], 
                     channel_config: Dict[str, Any]) -> bool:
        """
        发送Discord通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        webhook_url = channel_config.get("webhook_url")
        
        if not webhook_url:
            logger.error("Discord Webhook URL未配置")
            return False
        
        # 构建消息
        title = notification_data["title"]
        message = notification_data["message"]
        level = notification_data["level"]
        timestamp = notification_data["timestamp"].isoformat()
        
        # 根据级别设置颜色
        color = self._get_discord_color(level)
        
        # 构建Discord Embed消息
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color,
                    "fields": [
                        {
                            "name": "级别",
                            "value": level.upper(),
                            "inline": True
                        }
                    ],
                    "timestamp": timestamp
                }
            ]
        }
        
        # 添加图片（如果有）
        if "image_path" in notification_data and channel_config.get("send_image", True):
            try:
                image_path = notification_data["image_path"]
                if os.path.exists(image_path):
                    # Discord不支持直接附加本地图片，除非通过multipart/form-data方式上传
                    # 这里我们只在消息中添加图片路径的提示
                    payload["embeds"][0]["footer"] = {
                        "text": f"图片已保存到: {image_path}"
                    }
            except Exception as e:
                logger.error(f"处理Discord通知图片失败: {e}")
        
        # 发送请求
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code in [200, 204]:
                return True
            else:
                logger.error(f"Discord请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"发送Discord通知失败: {e}")
            return False
    
    def _send_webhook(self, notification_data: Dict[str, Any], 
                     channel_config: Dict[str, Any]) -> bool:
        """
        发送自定义Webhook通知
        
        Args:
            notification_data: 通知数据
            channel_config: 通道配置
            
        Returns:
            bool: 是否成功发送
        """
        webhook_url = channel_config.get("url")
        method = channel_config.get("method", "POST")
        content_type = channel_config.get("content_type", "application/json")
        headers = channel_config.get("headers", {})
        
        if not webhook_url:
            logger.error("Webhook URL未配置")
            return False
        
        # 构建消息
        title = notification_data["title"]
        message = notification_data["message"]
        level = notification_data["level"]
        timestamp = notification_data["timestamp"].isoformat()
        
        # 构建通用JSON负载
        payload = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": timestamp,
            "data": notification_data.get("data", {})
        }
        
        # 添加图片信息（如果有）
        if "image_path" in notification_data:
            payload["image_path"] = notification_data["image_path"]
        
        # 设置内容类型的头部
        headers["Content-Type"] = content_type
        
        # 发送请求
        try:
            if method.upper() == "GET":
                response = requests.get(webhook_url, params=payload, headers=headers)
            else:
                response = requests.post(webhook_url, json=payload, headers=headers)
            
            if response.status_code in [200, 201, 202, 204]:
                return True
            else:
                logger.error(f"Webhook请求失败，状态码: {response.status_code}")
            
            return False
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
            return False
    
    def _check_level(self, level: str) -> bool:
        """
        检查通知级别是否满足最低要求
        
        Args:
            level: 通知级别
            
        Returns:
            bool: 是否满足要求
        """
        level_priority = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }
        
        current_priority = level_priority.get(level.lower(), 0)
        min_priority = level_priority.get(self.min_level.lower(), 0)
        
        return current_priority >= min_priority
    
    def _check_specific_level(self, level: str, min_level: str) -> bool:
        """
        检查特定通道的通知级别
        
        Args:
            level: 通知级别
            min_level: 最低通知级别
            
        Returns:
            bool: 是否满足要求
        """
        level_priority = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }
        
        current_priority = level_priority.get(level.lower(), 0)
        min_priority = level_priority.get(min_level.lower(), 0)
        
        return current_priority >= min_priority
    
    def _check_throttle(self, title: str, level: str) -> bool:
        """
        检查通知限流
        
        Args:
            title: 通知标题
            level: 通知级别
            
        Returns:
            bool: 是否允许发送
        """
        with self.lock:
            current_time = time.time()
            
            # 检查每分钟最大数量
            minute_start = current_time - 60
            recent_count = sum(1 for t, _ in self.notification_history.values() 
                              if t > minute_start)
            
            if recent_count >= self.max_per_minute and level.lower() not in ["error", "critical"]:
                return False
            
            # 检查相同标题的限流
            key = f"{title}:{level}"
            if key in self.notification_history:
                last_time, count = self.notification_history[key]
                if current_time - last_time < self.throttle_seconds:
                    # 更新计数
                    self.notification_history[key] = (last_time, count + 1)
                    return False
            
            # 更新历史
            self.notification_history[key] = (current_time, 1)
            
            return True
    
    def _cleanup_history(self) -> None:
        """清理过期的通知历史"""
        current_time = time.time()
        
        # 每分钟最多清理一次
        if current_time - self.last_cleanup < 60:
            return
        
        with self.lock:
            # 清理超过限流时间两倍的历史记录
            expiry_time = current_time - (self.throttle_seconds * 2)
            
            # 找出过期的键
            expired_keys = [key for key, (timestamp, _) in self.notification_history.items() 
                          if timestamp < expiry_time]
            
            # 删除过期的键
            for key in expired_keys:
                del self.notification_history[key]
            
            self.last_cleanup = current_time
    
    def _get_level_color(self, level: str) -> str:
        """
        获取级别对应的颜色
        
        Args:
            level: 通知级别
            
        Returns:
            str: 颜色代码
        """
        color_map = {
            "debug": "#808080",  # 灰色
            "info": "#0088FF",   # 蓝色
            "warning": "#FFA500", # 橙色
            "error": "#FF0000",   # 红色
            "critical": "#8B0000"  # 深红色
        }
        
        return color_map.get(level.lower(), "#808080")
    
    def _get_slack_color(self, level: str) -> str:
        """
        获取Slack级别对应的颜色
        
        Args:
            level: 通知级别
            
        Returns:
            str: Slack颜色代码
        """
        color_map = {
            "debug": "#808080",  # 灰色
            "info": "good",      # 绿色
            "warning": "warning", # 黄色
            "error": "danger",    # 红色
            "critical": "#8B0000"  # 深红色
        }
        
        return color_map.get(level.lower(), "good")
    
    def _get_discord_color(self, level: str) -> int:
        """
        获取Discord级别对应的颜色
        
        Args:
            level: 通知级别
            
        Returns:
            int: Discord颜色整数值
        """
        color_map = {
            "debug": 0x808080,   # 灰色
            "info": 0x0088FF,    # 蓝色
            "warning": 0xFFA500,  # 橙色
            "error": 0xFF0000,    # 红色
            "critical": 0x8B0000   # 深红色
        }
        
        return color_map.get(level.lower(), 0x808080)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取通知统计数据
        
        Returns:
            Dict[str, Any]: 统计数据
        """
        with self.lock:
            return self.stats.copy()
    
    def clear_stats(self) -> None:
        """清除统计数据"""
        with self.lock:
            self.stats = {
                "total_sent": 0,
                "throttled": 0,
                "failed": 0,
                "by_channel": {},
                "by_level": {}
            } 