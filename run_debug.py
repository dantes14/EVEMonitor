#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试启动脚本 - 使用Python调试器
"""

import sys
import os
import pdb
import traceback
from pathlib import Path

# 保存调试信息到文件
debug_file = Path("debug_pdb.txt")
with open(debug_file, "w", encoding="utf-8") as f:
    f.write("===== 调试启动 =====\n")
    f.write(f"Python版本: {sys.version}\n")
    f.write(f"当前目录: {os.getcwd()}\n")

def main():
    """
    调试入口函数
    """
    try:
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"项目根目录: {project_root}\n")
            f.write("开始导入主程序模块...\n")
        
        # 导入主模块
        from src.main import main as app_main
        
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write("主程序模块导入成功，开始调试...\n")
        
        # 启动调试器
        print("开始调试，调试信息将记录到debug_pdb.txt文件中")
        print("您可以在调试器中使用以下命令：")
        print("  c: 继续执行")
        print("  n: 执行下一行")
        print("  s: 步入函数")
        print("  q: 退出调试")
        pdb.set_trace()
        
        # 运行主程序
        app_main()
        
    except Exception as e:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"出现错误: {e}\n")
            f.write(traceback.format_exc())
        print(f"调试出错: {e}")
        print(f"详细信息已保存到 {debug_file} 文件")

if __name__ == "__main__":
    main()

 