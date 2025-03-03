# EVEMonitor

[![Python Tests](https://github.com/dantes14/EVEMonitor/actions/workflows/test.yml/badge.svg)](https://github.com/dantes14/EVEMonitor/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/dantes14/EVEMonitor/branch/main/graph/badge.svg)](https://codecov.io/gh/dantes14/EVEMonitor)
[![PyPI version](https://badge.fury.io/py/evemonitor.svg)](https://badge.fury.io/py/evemonitor)
[![Python Versions](https://img.shields.io/pypi/pyversions/evemonitor.svg)](https://pypi.org/project/evemonitor/)
[![License](https://img.shields.io/github/license/dantes14/EVEMonitor.svg)](https://github.com/dantes14/EVEMonitor/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

EVE游戏监控工具 - 一个基于Python的EVE Online游戏监控工具，用于实时监控游戏画面并识别关键信息。

## 功能特性

- 🎮 支持多种监控模式
  - 全屏监控
  - 自定义区域监控
  - 网格布局监控
- 🔍 强大的OCR识别
  - 支持PaddleOCR和Tesseract两种引擎
  - 可配置的识别区域
  - 多语言支持
- 📊 数据分析和统计
  - 实时数据采集
  - 数据可视化
  - 历史记录查询
- 🔔 灵活的通知系统
  - 支持多种通知方式
  - 可自定义通知规则
  - 通知优先级管理
- 🎨 美观的用户界面
  - 现代化的UI设计
  - 深色/浅色主题
  - 布局预览功能

## 项目截图

### 主界面
![主界面](screenshots/main_window.png)

### OCR配置
![OCR配置](screenshots/ocr_config.png)

### 屏幕配置
![屏幕配置](screenshots/screen_config.png)

### 通知配置
![通知配置](screenshots/notification_config.png)

## 系统要求

- Python 3.8+
- Windows/macOS/Linux
- 支持OpenGL的显卡（用于屏幕捕获）

## 安装说明

1. 克隆仓库
```bash
git clone https://github.com/dantes14/EVEMonitor.git
cd EVEMonitor
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 安装开发依赖（可选）
```bash
pip install -r requirements-dev.txt
```

## 使用方法

1. 启动程序
```bash
python main.py
```

2. 配置监控设置
   - 选择监控模式
   - 配置OCR参数
   - 设置通知规则

3. 开始监控
   - 点击"开始监控"按钮
   - 程序会自动捕获屏幕并识别信息

## 配置说明

### OCR配置
- 支持PaddleOCR和Tesseract两种引擎
- 可配置识别区域和参数
- 支持多语言识别

### 通知配置
- 支持多种通知方式
- 可自定义通知规则
- 支持通知优先级

### 界面配置
- 支持深色/浅色主题
- 可自定义布局
- 支持布局预览

## 开发计划

- [ ] 添加更多OCR引擎支持
- [ ] 优化识别准确率
- [ ] 添加数据分析功能
- [ ] 支持更多通知方式
- [ ] 添加插件系统

## 贡献指南

欢迎提交Issue和Pull Request！详见[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: dantes14
- 项目链接: [https://github.com/dantes14/EVEMonitor](https://github.com/dantes14/EVEMonitor)
- 邮箱: [你的邮箱]
