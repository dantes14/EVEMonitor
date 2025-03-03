#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVEMonitor主程序入口
"""

import sys
import os
from pathlib import Path
from loguru import logger

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config.config_manager import ConfigManager


def setup_logger():
    """配置日志"""
    # 创建日志目录
    log_dir = Path.home() / ".evemonitor" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    logger.add(
        log_dir / "evemonitor.log",
        rotation="500 MB",
        retention="10 days",
        level="INFO",
        encoding="utf-8"
    )


def main():
    """主程序入口"""
    # 设置日志
    setup_logger()
    logger.info("启动EVEMonitor...")
    
    # 创建配置管理器
    config_dir = Path.home() / ".evemonitor"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_manager = ConfigManager(config_path)
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow(config_manager)
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 