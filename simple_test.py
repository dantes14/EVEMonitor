#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试脚本
"""

import sys
import os

def main():
    print("这是一个简单的测试脚本")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path}")
    
    try:
        import PyQt6
        print(f"PyQt6版本: {PyQt6.QtCore.QT_VERSION_STR}")
        print("PyQt6导入成功")
    except ImportError as e:
        print(f"PyQt6导入失败: {e}")
    
    input("按回车键继续...")

if __name__ == "__main__":
    main() 