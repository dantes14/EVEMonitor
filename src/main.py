#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVEMonitor主程序入口
"""

import sys
import os
import traceback
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 添加文件日志
debug_log = project_root / "debug_main.txt"
with open(debug_log, "a", encoding="utf-8") as f:
    f.write(f"===== 程序启动 =====\n")
    f.write(f"Python版本: {sys.version}\n")
    f.write(f"当前工作目录: {os.getcwd()}\n")
    f.write(f"Python路径: {sys.path}\n\n")

try:
    from PyQt6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow
    from src.config.config_manager import ConfigManager
    
    with open(debug_log, "a", encoding="utf-8") as f:
        f.write("所有模块导入成功\n")
except Exception as e:
    with open(debug_log, "a", encoding="utf-8") as f:
        f.write(f"模块导入失败: {e}\n")
        f.write(traceback.format_exc())
    raise


def setup_logger():
    """配置日志"""
    try:
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
        
        # 添加文件日志
        logger.add(
            project_root / "debug_main.txt",
            rotation="1 MB",
            level="DEBUG",
            encoding="utf-8"
        )
        
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("日志设置成功\n")
    except Exception as e:
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"日志设置失败: {e}\n")
            f.write(traceback.format_exc())


def main():
    """主程序入口"""
    try:
        # 设置日志
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("正在设置日志...\n")
        setup_logger()
        logger.info("启动EVEMonitor...")
        
        # 创建配置管理器
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("正在创建配置管理器...\n")
        config_dir = Path.home() / ".evemonitor"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.yaml"
        config_manager = ConfigManager(config_path)
        
        # 检查ConfigManager中是否有这些方法:
        # - set_config()
        # - update()
        # - set_value()
        # - modify_config()
        
        # 创建Qt应用
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("正在创建Qt应用...\n")
        app = QApplication(sys.argv)
        
        # 创建主窗口
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("正在创建主窗口...\n")
        window = MainWindow(config_manager)
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("显示主窗口...\n")
        window.show()
        
        # 运行应用
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write("启动应用程序主循环...\n")
        sys.exit(app.exec())
    
    except Exception as e:
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"程序执行出错: {e}\n")
            f.write(traceback.format_exc())
        logger.error(f"程序执行出错: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"主程序异常: {e}\n")
            f.write(traceback.format_exc())
        print(f"程序执行出错: {e}")
        print("详细信息已记录到 debug_main.txt 文件中。")
        sys.exit(1) 