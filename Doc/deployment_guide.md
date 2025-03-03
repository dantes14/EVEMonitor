# EVE监视器部署使用教程

本教程将指导您在Mac和Windows环境下分别如何部署和使用EVE监视器。

## 目录
1. [系统要求](#系统要求)
2. [Mac环境部署](#mac环境部署)
3. [Windows环境部署](#windows环境部署)
4. [配置说明](#配置说明)
5. [使用指南](#使用指南)
6. [常见问题](#常见问题)

## 系统要求

- **Mac**: macOS 10.14或更高版本
- **Windows**: Windows 10或更高版本
- **Python**: 3.8或更高版本
- **内存**: 至少4GB RAM（推荐8GB以上）
- **存储空间**: 至少2GB可用空间

## Mac环境部署

### 1. 准备基础环境

```bash
# 安装Homebrew（如果尚未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python
brew install python

# 安装Tesseract OCR引擎（推荐使用）
brew install tesseract

# 安装OpenCV
brew install opencv

# 安装XCode命令行工具（如果尚未安装）
xcode-select --install
```

### 2. 下载EVE监视器

```bash
# 克隆仓库
git clone https://github.com/your-username/EVEMonitor.git
cd EVEMonitor

# 或者下载ZIP包并解压
# 然后在终端中进入解压目录
```

### 3. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 4. 启动应用程序

```bash
# 确保在EVEMonitor目录下
python main.py

# 启用调试模式
python main.py --debug

# 指定配置文件
python main.py --config /path/to/your/config.yaml
```

### 5. Mac特定权限设置

应用首次运行时，您可能需要授予屏幕录制权限：

1. 当看到权限请求提示时，点击"系统偏好设置"
2. 进入"安全性与隐私" > "隐私" > "屏幕录制"
3. 确保勾选了Python或EVE监视器程序
4. 重启应用程序

## Windows环境部署

### 1. 安装Python

1. 从[Python官网](https://www.python.org/downloads/windows/)下载最新版Python安装程序（推荐3.8或更高版本）
2. 运行安装程序，**务必勾选"Add Python to PATH"选项**
3. 完成安装并验证：
   ```cmd
   python --version
   ```

### 2. 安装OCR引擎（两种选择）

#### 选项A：使用程序自动安装（推荐）

EVE监视器现在支持在首次启动时自动安装Tesseract OCR。您只需：

1. 安装Python和项目依赖
2. 启动EVE监视器
3. 当看到"未找到Tesseract OCR引擎"提示时，选择"是"自动下载安装

#### 选项B：手动安装Tesseract

如果您希望手动安装Tesseract OCR：

1. 从[GitHub](https://github.com/UB-Mannheim/tesseract/wiki)下载Tesseract安装程序
2. 运行安装程序，推荐安装到默认路径（如`C:\Program Files\Tesseract-OCR`）
3. 安装过程中确保选择安装中文语言包（在"Additional language data"中选择"Chinese (Simplified)"）
4. 安装完成后，EVE监视器会自动检测默认路径下的Tesseract

（可选）手动设置环境变量：
- 右键"此电脑" > "属性" > "高级系统设置" > "环境变量"
- 在"系统变量"中点击"新建"
- 变量名输入`TESSERACT_PATH`
- 变量值输入Tesseract可执行文件路径（如`C:\Program Files\Tesseract-OCR\tesseract.exe`）
- 点击"确定"保存

### 3. 安装PaddleOCR（可选，推荐）

EVE监视器在Windows上支持PaddleOCR，它比Tesseract提供更好的中文识别效果：

1. 确保已安装CUDA（如需GPU加速）
2. 安装项目依赖时，确保取消注释requirements.txt中的PaddleOCR相关依赖
3. EVE监视器会自动检测并优先使用PaddleOCR

### 4. 下载EVE监视器

```cmd
# 克隆仓库（需要安装Git）
git clone https://github.com/your-username/EVEMonitor.git
cd EVEMonitor

# 或者下载ZIP包并解压
# 然后在命令提示符中进入解压目录
```

### 5. 创建虚拟环境并安装依赖

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 升级pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 6. 启动应用程序

```cmd
# 确保在EVEMonitor目录下
python main.py

# 启用调试模式
python main.py --debug

# 指定配置文件
python main.py --config D:\path\to\your\config.yaml
```

## 配置说明

EVE监视器使用JSON格式的配置文件，默认位于`config/config.json`。您可以通过以下方式修改配置：

1. **直接编辑配置文件**：使用文本编辑器修改`config.json`
2. **通过应用程序界面**：在应用程序中修改设置，修改会自动保存

### 主要配置项

#### OCR引擎配置

EVE监视器支持两种OCR引擎：

```json
"ocr": {
    "engine": "paddle",  // 可选值："paddle" 或 "tesseract"
    "language": "ch",    // 语言：ch（中文）, eng（英文）等
    "confidence_threshold": 0.6,
    "tesseract": {
        "executable_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        "tessdata_dir": "C:\\Program Files\\Tesseract-OCR\\tessdata"
    },
    "paddle": {
        "use_gpu": false,
        "use_cls": true,
        "use_det": true,
        "use_server_mode": false,
        "model_dir": ""
    }
}
```

#### 模拟器设置

配置EVE Online客户端窗口标题和监控区域：

```json
"screen": {
    "monitor_mode": "window",  // window：窗口模式，screen：全屏模式
    "capture_method": "window",  // window：窗口截图，screen：屏幕截图
    "simulators": [
        {
            "title": "EVE Online",   // 模拟器窗口标题
            "enabled": true,         // 是否启用
            "regions": {
                "ship_status": {     // 舰船状态区域
                    "x": 10,
                    "y": 10,
                    "width": 200,
                    "height": 50
                },
                "target": {          // 目标区域
                    "x": 300,
                    "y": 10,
                    "width": 200,
                    "height": 300
                },
                "chat": {            // 聊天区域
                    "x": 10,
                    "y": 400,
                    "width": 300,
                    "height": 200
                },
                "system": {          // 系统信息区域
                    "x": 800,
                    "y": 10,
                    "width": 200,
                    "height": 30
                }
            }
        }
    ]
}
```

#### 调试配置

```json
"debug": {
    "enabled": false,            // 是否启用调试模式
    "save_screenshots": false,   // 是否保存截图
    "save_images": false,        // 是否保存处理后的图像
    "log_level": "info"          // 日志级别：debug, info, warning, error
}
```

#### 通知配置

```json
"notification": {
    "enabled": true,
    "cooldown": 60,  // 通知冷却时间（秒）
    "sound_enabled": true,
    "desktop_enabled": true,
    "tray_enabled": true,
    "sound_file": "path/to/sound.wav"
}
```

- **模拟器设置**：设置EVE Online客户端窗口标题和监控区域
- **OCR设置**：确保OCR引擎设置为Tesseract并配置语言
  ```yaml
  monitor:
    ocr:
      engine: "tesseract"  # 使用Tesseract OCR引擎
      language: "eng"      # 识别英文（可选：chi_sim中文简体，chi_tra中文繁体）
  ```
- **警报设置**：配置不同类型的警报和触发条件
- **通知设置**：配置通知方式（系统通知、钉钉、微信等）

## 使用指南

### 基本使用流程

1. **启动程序**：运行`python main.py`启动EVE监视器
2. **配置模拟器**：
   - 点击"屏幕配置"选项卡
   - 添加新模拟器配置或编辑现有配置
   - 设置窗口标题和游戏区域
3. **设置监控区域**：
   - 点击"添加区域"按钮
   - 使用区域选择器选择要监控的屏幕区域
   - 设置区域类型（舰船状态、聊天窗口、目标信息等）
4. **启动监控**：
   - 点击主界面上的"开始监控"按钮
   - 监控状态会在状态面板中显示

### 关键功能

- **实时监控**：自动截图并分析EVE游戏中的关键信息
- **多区域检测**：可以同时监控多个游戏区域
- **自定义警报**：根据护盾、装甲、结构等状态触发警报
- **多渠道通知**：支持系统通知、钉钉、微信等多种通知方式
- **截图保存**：自动保存触发警报的截图，方便后续分析

## 常见问题

### Windows环境常见问题

#### 1. "未找到Tesseract路径"错误

**问题描述**: 程序启动时提示"未找到Tesseract路径，请设置Tesseract路径"

**解决方案**:
- 选择"是"让程序自动下载并安装Tesseract
- 或手动安装Tesseract，确保安装到默认路径 `C:\Program Files\Tesseract-OCR\`
- 或在OCR设置界面中手动设置Tesseract可执行文件路径

#### 2. 无法识别游戏中的文字

**问题描述**: OCR功能无法正确识别游戏中的文字

**解决方案**:
- 确保安装了正确的语言包（中文游戏需要安装简体中文语言包）
- 调整OCR设置中的置信度阈值（较低的值可能识别出更多文字，但准确性降低）
- 尝试使用PaddleOCR引擎，它通常对中文的识别效果更好
- 调整监控区域，确保只包含需要识别的文字区域

#### 3. PaddleOCR安装问题

**问题描述**: 无法成功安装PaddleOCR

**解决方案**:
- 确保使用Python 3.8或3.9版本（PaddleOCR对Python版本有特定要求）
- 如果安装过程中出现CUDA相关错误，可以尝试安装CPU版本：
  ```
  pip install paddlepaddle
  ```
- 如果安装后仍无法使用，程序会自动降级到Tesseract引擎

#### 4. 截图功能无法正常工作

**问题描述**: 无法正确捕获游戏窗口或截图黑屏

**解决方案**:
- 确保游戏运行在窗口模式而非全屏模式
- 尝试以管理员身份运行EVE监视器
- 在设置中尝试不同的截图方法（窗口截图vs屏幕截图）
- 如果使用多显示器，确保游戏窗口在主显示器上

#### 5. 程序崩溃或无响应

**问题描述**: 程序意外退出或界面无响应

**解决方案**:
- 检查日志文件（默认在logs目录下）了解错误详情
- 降低截图频率（在设置中增加捕获间隔）
- 减少监控的区域数量
- 关闭不必要的功能，如调试模式或保存截图功能

### Mac环境常见问题

#### 1. OCR识别不准确

**解决方案**：
- 调整监控区域，确保只包含需要识别的文本
- 调整图像处理参数，增强对比度或降低噪点
- 在配置中调整Tesseract的参数：
  ```yaml
  monitor:
    ocr:
      engine: "tesseract"
      tesseract_config: "--psm 6"  # 调整页面分割模式
  ```

#### 2. 找不到窗口

**解决方案**：
- 确保配置的窗口标题与EVE客户端窗口标题完全匹配
- 尝试使用部分匹配模式（在设置中启用"窗口标题部分匹配"）
- 确保EVE客户端处于前台或可见状态

#### 3. Mac权限问题

**解决方案**：
- 确保已授予屏幕录制权限
- 重启应用程序和/或重新登录系统
- 在"系统偏好设置"中检查是否已为Python或应用程序授予必要权限

### 依赖项问题

#### PaddleOCR在Windows上的配置

Windows环境中，EVE监视器默认使用PaddleOCR引擎，它提供比Tesseract更好的中文识别效果。如果您在安装PaddleOCR时遇到问题：

1. 可以使用预编译的wheel包安装：
   ```
   pip install paddlepaddle-gpu -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html
   ```

2. 或者安装CPU版本（性能稍低但兼容性更好）：
   ```
   pip install paddlepaddle
   ```

3. 如果仍无法安装，程序会自动降级使用Tesseract OCR引擎

---

如有任何疑问或遇到未列出的问题，请查看项目文档或在GitHub仓库中提交问题。

## 附录：依赖管理优化

### requirements.txt中的paddlepaddle依赖问题

既然我们推荐使用Tesseract OCR作为默认OCR引擎，建议从requirements.txt中移除paddlepaddle和paddleocr相关依赖。这样做有以下几个好处：

1. **简化安装过程**：避免用户遇到与PaddleOCR相关的安装错误
2. **减少依赖冲突**：特别是在macOS环境下，PaddlePaddle经常会与其他库产生冲突
3. **减小虚拟环境体积**：PaddlePaddle及其依赖非常庞大（几GB）

### 推荐处理方案

#### 方案一：完全移除PaddleOCR相关依赖（推荐）

从requirements.txt中移除：
```
paddlepaddle
paddleocr
```

#### 方案二：创建两个requirements文件

1. `requirements.txt`：基础依赖，不含PaddleOCR
2. `requirements-paddle.txt`：包含PaddleOCR的可选依赖

#### 方案三：在requirements.txt中标记为可选依赖

在requirements.txt中添加注释：
```
# 以下是可选OCR引擎，安装可能在某些系统上出现困难
# paddlepaddle==2.3.2; sys_platform != "darwin"  # 不推荐在macOS上安装
# paddleocr==2.5.0; sys_platform != "darwin"     # 不推荐在macOS上安装
```

### 程序代码调整建议

如果需要在代码中保留PaddleOCR选项，建议添加错误处理机制：

```python
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    
# 然后在初始化OCR引擎时检查
if engine == "paddle" and not PADDLE_AVAILABLE:
    logger.warning("PaddleOCR不可用，将使用Tesseract作为备选")
    engine = "tesseract"
```

这样即使用户没有安装PaddleOCR，程序也能自动降级为使用Tesseract，提高程序的稳定性和用户体验。

---

如有任何疑问或遇到未列出的问题，请查看项目文档或在GitHub仓库中提交问题。