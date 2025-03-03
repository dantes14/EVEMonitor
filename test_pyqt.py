#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt6测试脚本
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

def main():
    print("创建应用...")
    app = QApplication(sys.argv)
    
    print("创建窗口...")
    window = QMainWindow()
    window.setWindowTitle("PyQt6测试")
    window.setGeometry(100, 100, 400, 200)
    
    print("创建中央部件...")
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    print("创建布局...")
    layout = QVBoxLayout(central_widget)
    
    print("添加标签...")
    label = QLabel("PyQt6测试成功！")
    layout.addWidget(label)
    
    print("显示窗口...")
    window.show()
    
    print("启动应用程序主循环...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 