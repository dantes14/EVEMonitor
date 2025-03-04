# EVE屏幕监控警报系统

EVE屏幕监控警报系统是一个专为EVE Online玩家设计的工具，能够实时监控游戏中的危险情况并发送警报。系统通过截取游戏屏幕，使用OCR技术识别屏幕上的信息，分析是否存在危险情况，并在必要时触发警报。

## 主要功能

- **实时截图分析**：定期捕获游戏屏幕，并进行分析
- **多模拟器支持**：同时监控多个游戏窗口或模拟器
- **危险舰船检测**：识别Local列表中的危险玩家
- **系统名称识别**：识别当前所在星系
- **钉钉警报推送**：当检测到危险情况时，通过钉钉机器人发送警报
- **灵活配置管理**：提供界面化的配置管理，可调整监控参数

## 系统架构

项目采用模块化设计，主要包含以下模块：

- **EVEMonitor.Core**：核心模块，定义接口和模型
- **EVEMonitor.Capture**：屏幕捕获模块，负责获取屏幕截图
- **EVEMonitor.ImageProcessing**：图像处理模块，处理和分析截图
- **EVEMonitor.OCR**：OCR识别模块，识别图像中的文本
- **EVEMonitor.Alert**：警报模块，发送警报通知
- **EVEMonitor.UI**：用户界面模块，提供交互界面

## 项目结构

```
EVEMonitor/
├── src/
│   ├── EVEMonitor.Alert/           # 警报服务实现
│   ├── EVEMonitor.Capture/         # 屏幕捕获实现
│   ├── EVEMonitor.Core/            # 核心接口与模型
│   │   ├── Interfaces/             # 定义服务接口
│   │   ├── Models/                 # 定义数据模型
│   │   └── Services/               # 核心服务实现
│   ├── EVEMonitor.ImageProcessing/ # 图像处理实现
│   ├── EVEMonitor.OCR/             # OCR识别实现
│   └── EVEMonitor.UI/              # 用户界面实现
└── Doc/                            # 文档
```

## 关键服务

- **ScreenCaptureService**：屏幕捕获服务，负责截取游戏窗口
- **ImageProcessingService**：图像处理服务，负责处理和分割图像
- **OcrService**：OCR服务，负责识别图像中的文本
- **ConfigService**：配置服务，管理应用程序配置
- **DingTalkAlertService**：钉钉警报服务，发送警报通知
- **ScreenshotService**：截图服务，协调各个服务，管理整个监控流程

## 使用指南

1. 启动应用程序
2. 在设置中配置要监控的模拟器和窗口
3. 设置截图间隔和其他参数
4. 配置钉钉机器人（可选）
5. 点击"开始监控"按钮启动监控
6. 系统将自动捕获屏幕并分析，在检测到危险时发送警报

## 配置说明

通过"设置"按钮可以打开设置窗口，配置以下内容：

- **一般设置**：截图间隔、截图保存路径、危险阈值等
- **模拟器设置**：添加、删除和配置模拟器
- **警报服务**：钉钉机器人配置等

## 技术栈

- **.NET Framework**：应用程序框架
- **WPF**：用户界面
- **Material Design**：UI组件和样式
- **Tesseract OCR**：文字识别
- **OpenCV**：图像处理

## 注意事项

- 本工具仅用于辅助游戏，不得用于任何违反游戏规则的行为
- OCR识别准确率受游戏界面和分辨率影响，可能需要调整参数以获得最佳效果
- 建议在使用前先进行测试，确保工具能正确识别游戏界面

## 系统要求

- **操作系统**：Windows 10 1803+ 或 Windows 11
- **处理器**：双核心CPU 2.0GHz以上
- **内存**：4GB RAM以上
- **显卡**：支持DirectX 11
- **.NET运行时**：.NET 6.0 Runtime或更高版本

## 安装指南

1. 确保您的系统满足上述系统要求
2. 下载最新的发布版本
3. 运行安装程序，按照向导完成安装
4. 首次启动时，系统将引导您完成初始配置

## 开发指南

### 项目结构

```
EVEMonitor/
├── src/
│   ├── EVEMonitor.Core/            # 核心功能库
│   ├── EVEMonitor.Capture/         # 屏幕捕获模块
│   ├── EVEMonitor.ImageProcessing/ # 图像处理模块
│   ├── EVEMonitor.OCR/             # OCR识别模块
│   ├── EVEMonitor.Alert/           # 警报推送模块
│   ├── EVEMonitor.Config/          # 配置管理模块
│   └── EVEMonitor.UI/              # WPF用户界面
├── tests/                          # 测试项目
├── tools/                          # 辅助工具
└── docs/                           # 文档
```

### 开发环境

- Visual Studio 2022
- .NET 6.0 SDK
- Windows 10/11

### 构建步骤

1. 克隆仓库
2. 使用Visual Studio打开`EVEMonitor.sln`
3. 恢复NuGet包
4. 构建解决方案

## 许可证

本项目采用MIT许可证 