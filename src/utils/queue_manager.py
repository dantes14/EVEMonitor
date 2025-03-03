#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
队列管理器模块

提供线程安全的队列管理功能，用于多个模块间的数据传递和事件通知。
支持多生产者多消费者模式，可设置队列大小和超时。
"""

import time
import queue
import threading
from typing import Dict, Any, Callable, Optional, List, Tuple, Union

from src.utils.logger_utils import logger


class QueueManager:
    """队列管理器，用于管理多个队列之间的数据传递"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化队列管理器
        
        Args:
            max_size: 队列最大大小，默认为100
        """
        self._queues: Dict[str, queue.Queue] = {}
        self._callbacks: Dict[str, List[Tuple[Callable, Dict[str, Any]]]] = {}
        self._listeners: Dict[str, List[threading.Thread]] = {}
        self._max_size = max_size
        self._running = True
        self._lock = threading.RLock()
        
        # 创建默认队列，为不同队列设置不同的容量
        self.create_queue("default", max_size=100)
        self.create_queue("notification", max_size=50)
        self.create_queue("screenshot", max_size=200)  # 增加截图队列容量
        self.create_queue("ocr", max_size=100)
        self.create_queue("ocr_task", max_size=200)  # 增加OCR任务队列容量
        self.create_queue("ocr_result", max_size=200)  # 增加OCR结果队列容量
        self.create_queue("analysis_result", max_size=100)
        
        logger.debug("队列管理器初始化完成")
    
    def create_queue(self, queue_name: str, max_size: Optional[int] = None) -> bool:
        """
        创建一个新队列
        
        Args:
            queue_name: 队列名称
            max_size: 队列最大大小，默认使用管理器设置的大小
            
        Returns:
            bool: 创建是否成功
        """
        with self._lock:
            if queue_name in self._queues:
                logger.warning(f"队列 '{queue_name}' 已存在")
                return False
            
            size = max_size if max_size is not None else self._max_size
            self._queues[queue_name] = queue.Queue(maxsize=size)
            self._callbacks[queue_name] = []
            self._listeners[queue_name] = []
            logger.debug(f"创建队列: '{queue_name}', 最大大小: {size}")
            return True
    
    def get_queue(self, queue_name: str) -> Optional[queue.Queue]:
        """
        获取指定名称的队列
        
        Args:
            queue_name: 队列名称
            
        Returns:
            Optional[queue.Queue]: 队列对象，不存在则返回None
        """
        return self._queues.get(queue_name)
    
    def put(self, data: Any, queue_name: str = "default", block: bool = True, 
            timeout: Optional[float] = None) -> bool:
        """
        向指定队列添加数据
        
        Args:
            data: 要添加的数据
            queue_name: 队列名称，默认为"default"
            block: 是否阻塞，默认为True
            timeout: 超时时间，默认为None（永不超时）
            
        Returns:
            bool: 添加是否成功
        """
        q = self.get_queue(queue_name)
        if not q:
            logger.error(f"队列 '{queue_name}' 不存在")
            return False
        
        try:
            q.put(data, block=block, timeout=timeout)
            
            # 触发回调函数
            self._trigger_callbacks(queue_name, data)
            
            return True
        except queue.Full:
            logger.warning(f"队列 '{queue_name}' 已满，无法添加数据")
            return False
    
    def get(self, queue_name: str = "default", block: bool = True,
            timeout: Optional[float] = None) -> Tuple[bool, Any]:
        """
        从指定队列获取数据
        
        Args:
            queue_name: 队列名称，默认为"default"
            block: 是否阻塞，默认为True
            timeout: 超时时间，默认为None（永不超时）
            
        Returns:
            Tuple[bool, Any]: (是否成功, 数据)，失败时数据为None
        """
        q = self.get_queue(queue_name)
        if not q:
            logger.error(f"队列 '{queue_name}' 不存在")
            return False, None
        
        try:
            data = q.get(block=block, timeout=timeout)
            q.task_done()
            return True, data
        except queue.Empty:
            if timeout:
                logger.debug(f"从队列 '{queue_name}' 获取数据超时")
            return False, None
    
    def get_queue_size(self, queue_name: str) -> int:
        """
        获取指定队列的大小
        
        Args:
            queue_name: 队列名称
            
        Returns:
            int: 队列中的元素数量
        """
        q = self.get_queue(queue_name)
        if not q:
            logger.error(f"队列 '{queue_name}' 不存在")
            return 0
        
        return q.qsize()
    
    def register_callback(self, queue_name: str, callback: Callable,
                         **kwargs) -> bool:
        """
        为指定队列注册回调函数，当有新数据时自动调用
        
        Args:
            queue_name: 队列名称
            callback: 回调函数，必须接受一个位置参数(数据)
            **kwargs: 传递给回调函数的额外参数
            
        Returns:
            bool: 注册是否成功
        """
        with self._lock:
            if queue_name not in self._callbacks:
                logger.error(f"队列 '{queue_name}' 不存在")
                return False
            
            self._callbacks[queue_name].append((callback, kwargs))
            logger.debug(f"为队列 '{queue_name}' 注册回调函数: {callback.__name__}")
            return True
    
    def _trigger_callbacks(self, queue_name: str, data: Any) -> None:
        """触发指定队列的所有回调函数"""
        callbacks = self._callbacks.get(queue_name, [])
        for callback, kwargs in callbacks:
            try:
                # 在新线程中执行回调以避免阻塞
                threading.Thread(
                    target=callback,
                    args=(data,),
                    kwargs=kwargs,
                    daemon=True
                ).start()
            except Exception as e:
                logger.error(f"执行队列 '{queue_name}' 的回调函数时出错: {e}")
    
    def start_listener(self, queue_name: str, callback: Callable,
                      **kwargs) -> bool:
        """
        启动一个监听线程，持续监听队列并处理数据
        
        Args:
            queue_name: 队列名称
            callback: 回调函数，必须接受一个位置参数(数据)
            **kwargs: 传递给回调函数的额外参数
            
        Returns:
            bool: 启动是否成功
        """
        with self._lock:
            if queue_name not in self._queues:
                logger.error(f"队列 '{queue_name}' 不存在")
                return False
            
            listener_thread = threading.Thread(
                target=self._listener_worker,
                args=(queue_name, callback),
                kwargs=kwargs,
                daemon=True
            )
            listener_thread.start()
            
            self._listeners[queue_name].append(listener_thread)
            logger.debug(f"为队列 '{queue_name}' 启动监听线程")
            return True
    
    def _listener_worker(self, queue_name: str, callback: Callable, **kwargs) -> None:
        """监听工作线程函数"""
        logger.debug(f"队列 '{queue_name}' 的监听线程已启动")
        
        q = self.get_queue(queue_name)
        consecutive_timeouts = 0  # 连续超时计数
        max_consecutive_timeouts = 50  # 增加最大连续超时次数
        timeout_threshold = 20  # 增加超时阈值
        base_timeout = 0.5  # 基础超时时间
        max_timeout = 2.0  # 最大超时时间
        last_success_time = time.time()  # 上次成功处理时间
        last_warning_time = time.time()  # 上次警告时间
        warning_interval = 30.0  # 警告间隔（秒）
        
        while self._running:
            try:
                # 根据连续超时次数动态调整超时时间
                current_timeout = min(base_timeout * (1 + consecutive_timeouts * 0.1), max_timeout)
                
                success, data = self.get(queue_name, timeout=current_timeout)
                if success:
                    consecutive_timeouts = 0  # 重置连续超时计数
                    last_success_time = time.time()  # 更新最后成功时间
                    try:
                        callback(data, **kwargs)
                    except Exception as e:
                        logger.error(f"处理队列 '{queue_name}' 数据时出错: {e}")
                else:
                    consecutive_timeouts += 1
                    current_time = time.time()
                    
                    # 只在连续超时次数超过阈值且程序正在运行时记录日志
                    if consecutive_timeouts >= timeout_threshold and self._running:
                        # 检查是否长时间没有成功处理数据
                        if current_time - last_success_time > 30:  # 30秒无数据
                            if current_time - last_warning_time >= warning_interval:
                                logger.warning(f"队列 '{queue_name}' 已超过30秒未处理数据")
                                last_warning_time = current_time
                        else:
                            logger.debug(f"队列 '{queue_name}' 连续 {consecutive_timeouts} 次获取数据超时")
            except Exception as e:
                logger.error(f"队列 '{queue_name}' 监听线程出错: {e}")
                time.sleep(0.5)  # 防止因错误导致的CPU占用过高
        
        logger.debug(f"队列 '{queue_name}' 的监听线程已停止")
    
    def stop(self) -> None:
        """停止所有队列监听线程"""
        logger.debug("正在停止队列管理器...")
        
        # 首先设置停止标志
        self._running = False
        
        # 清空所有队列，避免处理过期数据
        for queue_name, q in self._queues.items():
            try:
                while not q.empty():
                    try:
                        q.get_nowait()
                        q.task_done()
                    except queue.Empty:
                        break
            except Exception as e:
                logger.error(f"清空队列 '{queue_name}' 时出错: {e}")
        
        # 等待所有线程结束，使用较短的超时时间
        for queue_name, threads in self._listeners.items():
            for thread in threads:
                if thread.is_alive():
                    try:
                        thread.join(timeout=0.1)  # 减少等待时间到0.1秒
                    except Exception as e:
                        logger.error(f"等待队列 '{queue_name}' 的监听线程结束时出错: {e}")
        
        # 清空所有队列和监听器
        self._queues.clear()
        self._callbacks.clear()
        self._listeners.clear()
        
        logger.debug("队列管理器已停止")


# 创建全局队列管理器实例
queue_manager = QueueManager() 