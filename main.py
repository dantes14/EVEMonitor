#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE监视器主程序入口

负责初始化应用程序、加载配置、启动主窗口，
并确保依赖模块正确加载和初始化。
"""

import os
import sys
import argparse
import traceback
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir, Qt, QSettings
import qdarkstyle

# 设置项目根目录
current_dir = Path(__file__).parent
project_root = current_dir

from src.core.monitor_manager import MonitorManager
from src.ui.main_window import MainWindow
from src.config.config_manager import ConfigManager
from src.utils.logger_utils import setup_logger, logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='EVE监视器 - 舰船监控与通知系统')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', type=str, help='指定配置文件路径')
    parser.add_argument('--log', type=str, help='指定日志文件路径')
    parser.add_argument('--no-dark', action='store_true', help='禁用暗色主题')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    return parser.parse_args()


def setup_exception_hook():
    """设置全局异常处理钩子"""
    def exception_hook(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"未捕获的异常: {error_msg}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_hook


def main():
    """主程序入口函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 显示版本信息并退出
    if args.version:
        print("EVE监视器 v1.0.0")
        return 0
    
    # 设置日志
    log_path = args.log if args.log else os.path.join(project_root, "logs")
    setup_logger(log_path, debug=args.debug)
    
    # 设置全局异常处理钩子
    setup_exception_hook()
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName("EVE监视器")
    app.setOrganizationName("EVE监视器")
    app.setOrganizationDomain("evemonitor.org")
    
    # 应用暗色主题
    if not args.no_dark:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    
    # 加载配置
    config_path = args.config if args.config else os.path.join(project_root, "config", "config.yaml")
    config_manager = ConfigManager(config_path)
    
    # 创建监控管理器
    monitor_manager = MonitorManager(config_manager)
    
    # 创建并显示主窗口
    main_window = MainWindow(config_manager, monitor_manager)
    main_window.show()
    
    # 启动应用程序主循环
    exit_code = app.exec()
    
    # 程序退出前的清理工作
    logger.info("应用程序关闭，正在执行清理...")
    monitor_manager.stop_monitoring()
    config_manager.save_config()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 