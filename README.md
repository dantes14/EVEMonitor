# EVE监视器

EVE监视器是一款为《EVE：无烬星河》国服手游设计的多模拟器监控工具。它可以监控屏幕上的多个模拟器，识别星系名称和船只信息，并在检测到舰船时通过多种方式发送通知。

## 主要功能

- **多模拟器支持**：支持监控屏幕上的多个手游模拟器
- **OCR识别**：使用PaddleOCR或Tesseract识别星系名称和舰船信息
- **实时通知**：检测到舰船时通过Webhook或API发送通知
- **可视化配置**：直观的界面配置监控区域、模拟器布局和识别参数
- **热更新配置**：支持在不重启应用的情况下更新配置
- **自定义过滤**：可设置忽略特定星系或舰船类型
- **高性能处理**：使用队列管理确保数据处理不延迟

## 安装说明

### 系统要求

- Python 3.8及以上版本
- 支持的操作系统：Windows 10/11, macOS, Linux

### 安装步骤

1. 克隆项目仓库：
   ```bash
   git clone https://github.com/yourusername/EVEMonitor.git
   cd EVEMonitor
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 根据需要安装OCR引擎：
   - PaddleOCR (推荐):
     ```bash
     # 已在requirements.txt中包含
     ```
   - Tesseract (可选):
     ```bash
     # 安装Tesseract：
     # Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装
     # macOS: brew install tesseract
     # Linux: sudo apt install tesseract-ocr
     ```

## 使用说明

### 启动应用

```bash
cd EVEMONITOR
python src/main.py
```

### 命令行参数

- `--debug`：启用调试模式
- `--config <path>`：指定配置文件路径
- `--log <path>`：指定日志文件路径

示例：
```bash
python src/main.py --debug --config custom_config.yaml
```

### 配置教程

1. **屏幕设置**：
   - 设置监控区域（全屏或自定义区域）
   - 配置模拟器布局（网格布局或自定义位置）

2. **OCR设置**：
   - 选择OCR引擎（PaddleOCR或Tesseract）
   - 配置识别参数（置信度阈值、语言等）
   - 设置识别区域（系统名称区域、船表区域）

3. **通知设置**：
   - 配置通知方式（Webhook或API）
   - 设置消息模板和过滤选项

## 问题排查

常见问题及解决方案：

1. **OCR识别不准确**：
   - 调整OCR配置参数，提高置信度阈值
   - 确保游戏界面可见且文本清晰
   - 尝试不同的OCR引擎

2. **通知未推送**：
   - 检查网络连接
   - 验证API地址和密钥
   - 查看日志文件获取详细错误信息

3. **CPU占用高**：
   - 增加截图间隔时间
   - 减少模拟器数量
   - 关闭调试功能

## 许可证

本项目采用MIT许可证。详情请查看`LICENSE`文件。
