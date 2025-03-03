#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试配置文件
"""

import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["TESTING"] = "true"

# 配置 pytest
def pytest_configure(config):
    """配置 pytest"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers",
        "qt: 标记为 Qt 相关测试"
    ) 