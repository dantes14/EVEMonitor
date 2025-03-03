#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析模块

负责分析OCR识别结果，检测游戏内状态，包括：
- 舰船状态(护盾、装甲、结构)
- 舰船目标
- 聊天消息
- 警报触发
等功能。
"""

import re
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from src.utils.logger_utils import logger


class DataAnalyzer:
    """数据分析器，分析OCR识别的结果"""
    
    def __init__(self, config_manager):
        """
        初始化数据分析器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.lock = threading.RLock()
        
        # 加载配置
        self.update_config()
        
        # 状态记录
        self.last_status = {}
        self.history = {}
        self.alert_history = {}
        
        logger.debug("数据分析器初始化完成")
    
    def update_config(self) -> None:
        """更新配置"""
        with self.lock:
            config = self.config_manager.get_config()
            
            # 分析配置
            self.analyzer_config = config.get("analyzer", {})
            
            # 阈值配置
            self.thresholds = self.analyzer_config.get("thresholds", {
                "shield": 30,
                "armor": 30,
                "structure": 30,
                "capacitor": 20
            })
            
            # 敏感词配置
            self.chat_keywords = self.analyzer_config.get("chat_keywords", [])
            
            # 聊天模式
            self.chat_patterns = self.analyzer_config.get("chat_patterns", {
                "local": r"\[本地\]\s*(.+?):\s*(.+)",
                "alliance": r"\[联盟\]\s*(.+?):\s*(.+)",
                "corporation": r"\[军团\]\s*(.+?):\s*(.+)"
            })
            
            # 分析间隔
            self.min_analysis_interval = self.analyzer_config.get("min_analysis_interval_ms", 500) / 1000.0
            
            # 警报冷却时间
            self.alert_cooldown = self.analyzer_config.get("alert_cooldown_sec", 60)
            
            # 特殊字符修正配置
            self.text_corrections = self.analyzer_config.get("text_corrections", {
                "％": "%",
                "：": ":",
                "，": ",",
                "。": "."
            })
            
            logger.debug("数据分析器配置已更新")
    
    def analyze_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析数据
        
        Args:
            task: 分析任务，包含OCR结果等数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if task.get("type") != "analysis_task":
            logger.warning(f"无效的分析任务类型: {task.get('type')}")
            return {"type": "analysis_error", "error": "无效的任务类型"}
        
        # 提取基本信息
        task_id = task.get("task_id", "unknown")
        region_type = task.get("region_type", "unknown")
        emulator = task_id.split("_")[0] if "_" in task_id else task_id
        ocr_result = task.get("ocr_result", [])
        timestamp = task.get("timestamp", datetime.now())
        
        # 检查是否需要跳过分析（同一区域分析过于频繁）
        if not self._should_analyze(emulator, region_type):
            return {"type": "analysis_skipped", "emulator": emulator, "region_type": region_type}
        
        # 根据区域类型进行不同的分析
        analysis_result = {"type": "analysis_result", "emulator": emulator, "region_type": region_type, "timestamp": timestamp}
        
        try:
            if region_type == "ship_status":
                analysis_result.update(self._analyze_ship_status(ocr_result, emulator))
            elif region_type == "target":
                analysis_result.update(self._analyze_target(ocr_result, emulator))
            elif region_type == "chat":
                analysis_result.update(self._analyze_chat(ocr_result, emulator))
            elif region_type == "system":
                analysis_result.update(self._analyze_system(ocr_result, emulator))
            else:
                logger.warning(f"未知的区域类型: {region_type}")
                analysis_result.update({"status": "unknown", "text": self._extract_text(ocr_result)})
        
        except Exception as e:
            logger.error(f"分析数据时发生错误: {e}")
            analysis_result.update({
                "error": str(e),
                "status": "error"
            })
        
        # 更新最后分析时间
        self._update_last_analysis(emulator, region_type)
        
        return analysis_result
    
    def _analyze_ship_status(self, ocr_result: List[Dict[str, Any]], emulator: str) -> Dict[str, Any]:
        """
        分析舰船状态
        
        Args:
            ocr_result: OCR识别结果
            emulator: 模拟器名称
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        ship_status = {}
        alerts = []
        
        # 提取文本
        text_lines = self._extract_text(ocr_result)
        
        # 查找护盾、装甲、结构数值
        shield_pattern = r"护盾.*?(\d+)[%％]"
        armor_pattern = r"装甲.*?(\d+)[%％]"
        structure_pattern = r"结构.*?(\d+)[%％]"
        capacitor_pattern = r"电容.*?(\d+)[%％]"
        
        # 尝试匹配模式
        shield_match = re.search(shield_pattern, text_lines, re.IGNORECASE)
        armor_match = re.search(armor_pattern, text_lines, re.IGNORECASE)
        structure_match = re.search(structure_pattern, text_lines, re.IGNORECASE)
        capacitor_match = re.search(capacitor_pattern, text_lines, re.IGNORECASE)
        
        # 提取数值
        shield_value = int(shield_match.group(1)) if shield_match else None
        armor_value = int(armor_match.group(1)) if armor_match else None
        structure_value = int(structure_match.group(1)) if structure_match else None
        capacitor_value = int(capacitor_match.group(1)) if capacitor_match else None
        
        # 构建状态
        ship_status["shield"] = shield_value
        ship_status["armor"] = armor_value
        ship_status["structure"] = structure_value
        ship_status["capacitor"] = capacitor_value
        
        # 检查是否需要触发警报
        alerts.extend(self._check_ship_alerts(ship_status, emulator))
        
        return {
            "ship_status": ship_status,
            "alerts": alerts,
            "raw_text": text_lines
        }
    
    def _analyze_target(self, ocr_result: List[Dict[str, Any]], emulator: str) -> Dict[str, Any]:
        """
        分析目标信息
        
        Args:
            ocr_result: OCR识别结果
            emulator: 模拟器名称
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        target_info = {}
        alerts = []
        
        # 提取文本
        text_lines = self._extract_text(ocr_result)
        
        # 尝试提取目标名称、类型、距离和状态
        name_pattern = r"名称[:：]\s*(.+?)(?:\n|$)"
        type_pattern = r"类型[:：]\s*(.+?)(?:\n|$)"
        distance_pattern = r"(\d+(?:\.\d+)?)\s*(?:km|米)"
        status_pattern = r"状态[:：]\s*(.+?)(?:\n|$)"
        
        # 尝试匹配
        name_match = re.search(name_pattern, text_lines)
        type_match = re.search(type_pattern, text_lines)
        distance_match = re.search(distance_pattern, text_lines)
        status_match = re.search(status_pattern, text_lines)
        
        # 提取信息
        target_name = name_match.group(1).strip() if name_match else None
        target_type = type_match.group(1).strip() if type_match else None
        distance = distance_match.group(1) if distance_match else None
        status = status_match.group(1).strip() if status_match else None
        
        # 构建目标信息
        if target_name:
            target_info["name"] = target_name
        if target_type:
            target_info["type"] = target_type
        if distance:
            target_info["distance"] = float(distance)
        if status:
            target_info["status"] = status
        
        # 检查是否有威胁目标
        if target_name and self._is_threat_target(target_name, target_type, status):
            alerts.append({
                "type": "threat_target",
                "message": f"发现威胁目标: {target_name} ({target_type}), 距离: {distance} km",
                "level": "warning",
                "target": target_info
            })
        
        return {
            "target_info": target_info,
            "has_target": bool(target_name),
            "alerts": alerts,
            "raw_text": text_lines
        }
    
    def _analyze_chat(self, ocr_result: List[Dict[str, Any]], emulator: str) -> Dict[str, Any]:
        """
        分析聊天消息
        
        Args:
            ocr_result: OCR识别结果
            emulator: 模拟器名称
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        chat_messages = []
        alerts = []
        
        # 提取文本
        text_lines = self._extract_text(ocr_result)
        
        # 尝试提取聊天消息
        # 格式通常为: [频道] 玩家名称: 消息内容
        chat_pattern = r"\[(.*?)\]\s*(.*?)[:：](.*?)(?:\n|$)"
        
        # 查找所有聊天消息
        matches = re.finditer(chat_pattern, text_lines)
        
        for match in matches:
            channel = match.group(1).strip()
            player = match.group(2).strip()
            message = match.group(3).strip()
            
            # 忽略太短的消息或系统消息
            if len(message) < 2 or player in ["系统", "System"]:
                continue
            
            # 添加到消息列表
            chat_message = {
                "channel": channel,
                "player": player,
                "message": message,
                "timestamp": datetime.now()
            }
            
            chat_messages.append(chat_message)
            
            # 检查敏感词
            if self._contains_keywords(message, self.chat_keywords):
                alerts.append({
                    "type": "sensitive_chat",
                    "message": f"检测到敏感聊天: [{channel}] {player}: {message}",
                    "level": "warning",
                    "chat": chat_message
                })
        
        return {
            "chat_messages": chat_messages,
            "message_count": len(chat_messages),
            "alerts": alerts,
            "raw_text": text_lines
        }
    
    def _analyze_system(self, ocr_result: List[Dict[str, Any]], emulator: str) -> Dict[str, Any]:
        """
        分析系统信息
        
        Args:
            ocr_result: OCR识别结果
            emulator: 模拟器名称
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        system_info = {}
        alerts = []
        
        # 提取文本
        text_lines = self._extract_text(ocr_result)
        
        # 尝试提取星系名称和安全等级
        system_pattern = r"星系[:：]\s*(.+?)(?:\n|$)"
        security_pattern = r"([-+]?\d+\.\d+)"
        
        system_match = re.search(system_pattern, text_lines)
        security_match = re.search(security_pattern, text_lines)
        
        # 提取信息
        system_name = system_match.group(1).strip() if system_match else None
        security = security_match.group(1) if security_match else None
        
        # 构建系统信息
        if system_name:
            system_info["name"] = system_name
        if security:
            security_value = float(security)
            system_info["security"] = security_value
            
            # 检查是否为低安或零安
            if security_value <= 0.0:
                sec_type = "零安"
                level = "warning"
            elif security_value < 0.5:
                sec_type = "低安"
                level = "info"
            else:
                sec_type = "高安"
                level = "info"
                
            system_info["sec_type"] = sec_type
            
            # 添加警报
            if sec_type in ["零安", "低安"]:
                alerts.append({
                    "type": "low_security",
                    "message": f"进入{sec_type}星系: {system_name} ({security_value})",
                    "level": level,
                    "system": system_info
                })
        
        return {
            "system_info": system_info,
            "alerts": alerts,
            "raw_text": text_lines
        }
    
    def _check_ship_alerts(self, ship_status: Dict[str, Any], emulator: str) -> List[Dict[str, Any]]:
        """
        检查舰船状态警报
        
        Args:
            ship_status: 舰船状态信息
            emulator: 模拟器名称
            
        Returns:
            List[Dict[str, Any]]: 警报列表
        """
        alerts = []
        
        # 获取阈值配置
        shield_threshold = self.thresholds.get("shield", 30)
        armor_threshold = self.thresholds.get("armor", 50)
        structure_threshold = self.thresholds.get("structure", 80)
        capacitor_threshold = self.thresholds.get("capacitor", 20)
        
        # 检查护盾
        shield = ship_status.get("shield")
        if shield is not None and shield < shield_threshold:
            # 检查是否可以触发警报(冷却时间)
            if self._can_trigger_alert(emulator, "low_shield"):
                alerts.append({
                    "type": "low_shield",
                    "message": f"护盾低于阈值: {shield}% (阈值: {shield_threshold}%)",
                    "level": "warning" if shield < 15 else "info",
                    "value": shield,
                    "threshold": shield_threshold
                })
        
        # 检查装甲
        armor = ship_status.get("armor")
        if armor is not None and armor < armor_threshold:
            if self._can_trigger_alert(emulator, "low_armor"):
                alerts.append({
                    "type": "low_armor",
                    "message": f"装甲低于阈值: {armor}% (阈值: {armor_threshold}%)",
                    "level": "warning" if armor < 25 else "info",
                    "value": armor,
                    "threshold": armor_threshold
                })
        
        # 检查结构
        structure = ship_status.get("structure")
        if structure is not None and structure < structure_threshold:
            if self._can_trigger_alert(emulator, "low_structure"):
                alerts.append({
                    "type": "low_structure",
                    "message": f"结构低于阈值: {structure}% (阈值: {structure_threshold}%)",
                    "level": "critical" if structure < 40 else "error",
                    "value": structure,
                    "threshold": structure_threshold
                })
        
        # 检查电容
        capacitor = ship_status.get("capacitor")
        if capacitor is not None and capacitor < capacitor_threshold:
            if self._can_trigger_alert(emulator, "low_capacitor"):
                alerts.append({
                    "type": "low_capacitor",
                    "message": f"电容低于阈值: {capacitor}% (阈值: {capacitor_threshold}%)",
                    "level": "warning" if capacitor < 10 else "info",
                    "value": capacitor,
                    "threshold": capacitor_threshold
                })
        
        return alerts
    
    def _is_threat_target(self, target_name: str, target_type: Optional[str], 
                          status: Optional[str]) -> bool:
        """
        检查是否为威胁目标
        
        Args:
            target_name: 目标名称
            target_type: 目标类型
            status: 目标状态
            
        Returns:
            bool: 是否为威胁
        """
        # 检查是否是NPC
        npc_patterns = [r'血袭者', r'天使', r'古尔模', r'九头蛇', r'辛迪加']
        is_npc = any(re.search(pattern, target_name, re.IGNORECASE) for pattern in npc_patterns)
        
        # 检查是否是特殊状态
        threatening_states = ['攻击中', '战斗', '红色']
        has_threat_status = status and any(state in status for state in threatening_states)
        
        # 检查是否是战斗舰船
        combat_ships = ['战列舰', '巡洋舰', '驱逐舰', '战斗巡洋舰']
        is_combat_ship = target_type and any(ship_type in target_type for ship_type in combat_ships)
        
        # 如果是NPC且是战斗舰船，可能是威胁
        if is_npc and is_combat_ship:
            return True
        
        # 如果处于攻击状态，是威胁
        if has_threat_status:
            return True
        
        return False
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        检查文本是否包含关键词
        
        Args:
            text: 待检查文本
            keywords: 关键词列表
            
        Returns:
            bool: 是否包含关键词
        """
        if not text or not keywords:
            return False
            
        # 查找关键词
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return True
                
        return False
    
    def _extract_text(self, ocr_result: List[Dict[str, Any]]) -> str:
        """
        从OCR结果中提取文本
        
        Args:
            ocr_result: OCR识别结果
            
        Returns:
            str: 提取的文本
        """
        text_lines = []
        
        # 处理PaddleOCR格式的结果
        if ocr_result and isinstance(ocr_result, list):
            for item in ocr_result:
                if isinstance(item, list) and len(item) >= 2:
                    text = item[1][0]  # PaddleOCR格式
                    text = self._correct_text(text)
                    text_lines.append(text)
                elif isinstance(item, dict) and "text" in item:
                    text = item["text"]  # 通用格式
                    text = self._correct_text(text)
                    text_lines.append(text)
        
        return "\n".join(text_lines)
    
    def _correct_text(self, text: str) -> str:
        """
        修正OCR识别的文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 修正后的文本
        """
        if not text:
            return ""
            
        # 替换特殊字符
        for original, replacement in self.text_corrections.items():
            text = text.replace(original, replacement)
            
        # 修正常见的OCR错误
        text = text.replace("％", "%")
        text = text.replace("，", ",")
        text = text.replace("：", ":")
        
        return text
    
    def _should_analyze(self, emulator: str, region_type: str) -> bool:
        """
        检查是否应该分析该区域
        
        Args:
            emulator: 模拟器名称
            region_type: 区域类型
            
        Returns:
            bool: 是否应该分析
        """
        with self.lock:
            key = f"{emulator}_{region_type}"
            if key not in self.last_status:
                return True
                
            last_time = self.last_status.get(key, {}).get("last_analysis_time", 0)
            current_time = time.time()
            
            # 检查是否超过最小分析间隔
            return (current_time - last_time) >= self.min_analysis_interval
    
    def _update_last_analysis(self, emulator: str, region_type: str) -> None:
        """
        更新最后分析时间
        
        Args:
            emulator: 模拟器名称
            region_type: 区域类型
        """
        with self.lock:
            key = f"{emulator}_{region_type}"
            
            if key not in self.last_status:
                self.last_status[key] = {}
                
            self.last_status[key]["last_analysis_time"] = time.time()
    
    def _can_trigger_alert(self, emulator: str, alert_type: str) -> bool:
        """
        检查是否可以触发警报
        
        Args:
            emulator: 模拟器名称
            alert_type: 警报类型
            
        Returns:
            bool: 是否可以触发
        """
        with self.lock:
            key = f"{emulator}_{alert_type}"
            
            if key not in self.alert_history:
                self.alert_history[key] = time.time()
                return True
                
            last_alert_time = self.alert_history[key]
            current_time = time.time()
            
            # 检查是否超过冷却时间
            if (current_time - last_alert_time) >= self.alert_cooldown:
                self.alert_history[key] = current_time
                return True
                
            return False
    
    def get_analysis_history(self, emulator: Optional[str] = None) -> Dict[str, Any]:
        """
        获取分析历史
        
        Args:
            emulator: 模拟器名称，None表示获取所有历史
            
        Returns:
            Dict[str, Any]: 分析历史
        """
        with self.lock:
            if emulator:
                return {k: v for k, v in self.history.items() if k.startswith(emulator)}
            else:
                return dict(self.history)
    
    def clear_history(self, emulator: Optional[str] = None) -> None:
        """
        清除分析历史
        
        Args:
            emulator: 模拟器名称，None表示清除所有历史
        """
        with self.lock:
            if emulator:
                # 清除指定模拟器的历史
                keys_to_remove = [k for k in self.history if k.startswith(emulator)]
                for key in keys_to_remove:
                    self.history.pop(key, None)
                    
                # 清除警报历史
                alert_keys = [k for k in self.alert_history if k.startswith(emulator)]
                for key in alert_keys:
                    self.alert_history.pop(key, None)
            else:
                # 清除所有历史
                self.history.clear()
                self.alert_history.clear() 