#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试启动脚本
"""

import sys
import os
import traceback
from pathlib import Path
import logging

# 设置日志
log_file = Path("debug_log.txt")
logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        logging.info("===== 开始调试 =====")
        logging.info(f"Python版本: {sys.version}")
        logging.info(f"当前工作目录: {os.getcwd()}")
        
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        logging.info(f"项目根目录: {project_root}")
        
        # 尝试导入PyQt6
        try:
            import PyQt6
            logging.info(f"PyQt6版本: {PyQt6.QtCore.QT_VERSION_STR}")
        except ImportError as e:
            logging.error(f"PyQt6导入失败: {e}")
            return
        
        # 导入主程序
        from src.main import main as app_main
        logging.info("成功导入主程序")
        
        # 运行主程序
        logging.info("开始运行主程序")
        app_main()
        
    except Exception as e:
        logging.error(f"发生错误: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
    print("调试完成，请查看debug_log.txt文件获取详细信息。") 