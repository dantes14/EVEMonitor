# EVE屏幕监控警报系统 - 技术方案文档

## 1. 总体架构

### 1.1 架构概述

EVE屏幕监控警报系统采用模块化设计，主要分为以下几个核心模块：

- **UI模块**：用户界面，提供配置管理和可视化监控
- **屏幕捕获模块**：负责截取屏幕内容并进行预处理
- **图像处理模块**：负责图像分割和区域提取
- **OCR识别模块**：负责文字识别和数据提取
- **警报推送模块**：负责根据识别结果发送警报
- **配置管理模块**：负责配置的读取、保存和热加载

系统整体采用C#/.NET技术栈开发，基于Windows平台实现。

### 1.2 系统流程

![系统流程图](示意图-可选)

1. 用户通过UI模块配置监控区域、模拟器布局和警报参数
2. 屏幕捕获模块按照设定间隔对指定区域进行截图
3. 图像处理模块将截图分割为各个模拟器窗口的子图像
4. OCR识别模块对子图像中的星系名称和舰船信息进行识别
5. 如果识别到舰船信息，警报推送模块将信息发送到钉钉
6. 整个过程通过队列管理，确保系统稳定性

## 2. 技术选型

### 2.1 开发环境

- **开发语言**：C# 10.0+
- **开发框架**：.NET 6.0+
- **UI框架**：WPF (Windows Presentation Foundation)
- **开发工具**：Visual Studio 2022

### 2.2 关键技术

| 模块 | 技术选型 | 说明 |
|-----|---------|-----|
| 屏幕捕获 | Windows.Graphics.Capture API 或 BitBlt API | 高性能屏幕捕获，支持多显示器 |
| 图像处理 | System.Drawing.Common 或 OpenCvSharp | 图像分割、裁剪和预处理 |
| OCR识别 | Tesseract OCR 或 Microsoft.ML.OnnxRuntime | 文字识别引擎 |
| 队列管理 | System.Threading.Channels | 高性能异步队列 |
| 配置管理 | JSON.NET 或 YamlDotNet | 配置文件序列化/反序列化 |
| 钉钉推送 | HttpClient | RESTful API 调用 |

### 2.3 性能优化方案

- **并行处理**：使用任务并行库(TPL)实现多核并行处理
- **内存优化**：使用对象池模式减少GC压力
- **CPU优化**：使用SIMD指令加速图像处理
- **队列管理**：采用背压(Backpressure)机制防止内存溢出

## 3. 详细设计

### 3.1 屏幕捕获模块

#### 3.1.1 技术实现

Windows平台下有多种屏幕捕获方式，我们将采用以下方案：

- 主要方案：Windows.Graphics.Capture API (Windows 10 1803+)
  - 优点：高性能、低延迟、支持多显示器
  - 缺点：仅支持Windows 10 1803及以上版本

- 备选方案：BitBlt API
  - 优点：兼容性好，支持所有Windows版本
  - 缺点：性能较低，CPU占用较高

#### 3.1.2 核心类设计

```csharp
public class ScreenCapture : IDisposable
{
    // 捕获区域配置
    public Rectangle CaptureRegion { get; set; }
    
    // 捕获频率(ms)
    public int CaptureInterval { get; set; }
    
    // 开始捕获
    public void Start();
    
    // 停止捕获
    public void Stop();
    
    // 截图事件
    public event EventHandler<ScreenCaptureEventArgs> ScreenCaptured;
    
    // 资源释放
    public void Dispose();
}
```

### 3.2 图像处理模块

#### 3.2.1 技术实现

图像处理模块负责将全屏截图分割为各个模拟器窗口的子图像，并提取感兴趣区域(ROI)。我们将使用以下技术：

- System.Drawing.Common：基础图像处理
- OpenCvSharp：高级图像处理和分析(可选)

#### 3.2.2 核心类设计

```csharp
public class ImageProcessor
{
    // 模拟器布局配置
    public List<Rectangle> EmulatorRegions { get; set; }
    
    // 处理截图，分割为多个模拟器子图像
    public List<EmulatorImage> ProcessScreenshot(Bitmap screenshot);
    
    // 提取感兴趣区域(星系名称、舰船表格)
    public List<RegionOfInterest> ExtractROIs(EmulatorImage emulatorImage);
}

// 模拟器图像类
public class EmulatorImage
{
    // 模拟器索引
    public int Index { get; set; }
    
    // 图像数据
    public Bitmap Image { get; set; }
    
    // 区域信息
    public Rectangle Region { get; set; }
}
```

### 3.3 OCR识别模块

#### 3.3.1 技术实现

OCR模块采用Tesseract OCR引擎，结合自定义训练的模型，提高游戏文字识别准确率。

- Tesseract OCR：开源OCR引擎
- 自定义训练：针对游戏字体的特定训练

#### 3.3.2 核心类设计

```csharp
public class OcrProcessor
{
    // 初始化OCR引擎
    public OcrProcessor(string tessDataPath);
    
    // 识别星系名称
    public string RecognizeSystemName(Bitmap systemNameImage);
    
    // 识别舰船表格
    public List<ShipInfo> RecognizeShipTable(Bitmap shipTableImage);
    
    // 释放资源
    public void Dispose();
}

// 舰船信息类
public class ShipInfo
{
    // 军团归属
    public string Corporation { get; set; }
    
    // 驾驶员名称
    public string PilotName { get; set; }
    
    // 船型信息
    public string ShipType { get; set; }
}
```

### 3.4 警报推送模块

#### 3.4.1 技术实现

警报推送模块采用HttpClient调用钉钉开放平台API，实现消息推送。

#### 3.4.2 核心类设计

```csharp
public class AlertPusher
{
    // 钉钉Webhook URL
    public string WebhookUrl { get; set; }
    
    // 推送舰船警报
    public async Task PushShipAlert(string systemName, List<ShipInfo> shipInfos);
    
    // 推送性能警报
    public async Task PushPerformanceAlert(string message, TimeSpan processingTime);
    
    // 构建消息内容
    private string BuildMessageContent(string title, string content);
}
```

### 3.5 配置管理模块

#### 3.5.1 技术实现

配置管理模块使用JSON.NET实现配置的序列化和反序列化，支持配置的热加载。

#### 3.5.2 核心类设计

```csharp
public class ConfigManager
{
    // 配置文件路径
    public string ConfigFilePath { get; set; }
    
    // 监控区域配置
    public Rectangle MonitorRegion { get; set; }
    
    // 模拟器布局配置
    public List<Rectangle> EmulatorRegions { get; set; }
    
    // 截图间隔(ms)
    public int CaptureInterval { get; set; }
    
    // 处理延迟阈值(ms)
    public int ProcessingThreshold { get; set; }
    
    // 钉钉Webhook URL
    public string WebhookUrl { get; set; }
    
    // 加载配置
    public void LoadConfig();
    
    // 保存配置
    public void SaveConfig();
    
    // 监听配置变更
    public void WatchConfigChanges();
    
    // 配置变更事件
    public event EventHandler<ConfigChangedEventArgs> ConfigChanged;
}
```

### 3.6 UI模块

#### 3.6.1 技术实现

UI模块采用WPF框架，实现直观的配置界面和监控状态展示。

- MVVM架构：分离界面和逻辑
- 自定义控件：实现模拟器布局可视化配置

#### 3.6.2 主要界面

1. **主界面**：显示监控状态和识别结果
2. **配置界面**：设置监控区域和模拟器布局
3. **警报配置**：设置钉钉推送参数
4. **系统设置**：截图频率和处理阈值配置

## 4. 队列管理与性能优化

### 4.1 队列设计

为避免处理延迟导致系统卡顿，采用生产者-消费者模式实现截图数据队列：

```csharp
public class ScreenshotQueue
{
    // 队列容量
    public int Capacity { get; set; }
    
    // 内部Channel
    private Channel<Bitmap> _channel;
    
    // 添加截图到队列
    public async ValueTask EnqueueAsync(Bitmap screenshot, CancellationToken cancellationToken);
    
    // 从队列获取截图
    public async ValueTask<Bitmap> DequeueAsync(CancellationToken cancellationToken);
    
    // 当前队列长度
    public int Count { get; }
}
```

### 4.2 性能监控

实现性能监控机制，当处理时间超过阈值时发送警报：

```csharp
public class PerformanceMonitor
{
    // 处理时间阈值(ms)
    public int ProcessingThreshold { get; set; }
    
    // 开始计时
    public Stopwatch StartTiming();
    
    // 结束计时并检查是否超过阈值
    public bool EndTimingAndCheck(Stopwatch stopwatch);
    
    // 性能警报事件
    public event EventHandler<PerformanceAlertEventArgs> PerformanceAlertTriggered;
}
```

## 5. 数据结构

### 5.1 识别结果数据结构

```csharp
// 模拟器识别结果
public class EmulatorRecognitionResult
{
    // 模拟器索引
    public int EmulatorIndex { get; set; }
    
    // 星系名称
    public string SystemName { get; set; }
    
    // 舰船信息列表
    public List<ShipInfo> Ships { get; set; }
    
    // 识别时间戳
    public DateTime Timestamp { get; set; }
}

// 警报数据
public class AlertData
{
    // 警报类型(舰船/性能)
    public AlertType Type { get; set; }
    
    // 模拟器索引
    public int EmulatorIndex { get; set; }
    
    // 星系名称
    public string SystemName { get; set; }
    
    // 舰船信息
    public List<ShipInfo> Ships { get; set; }
    
    // 处理时间(性能警报)
    public TimeSpan ProcessingTime { get; set; }
    
    // 警报时间戳
    public DateTime Timestamp { get; set; }
}
```

### 5.2 配置数据结构

```csharp
// 应用配置
public class AppConfig
{
    // 监控区域
    public Rectangle MonitorRegion { get; set; }
    
    // 模拟器配置列表
    public List<EmulatorConfig> Emulators { get; set; }
    
    // 截图间隔(ms)
    public int CaptureInterval { get; set; }
    
    // 处理延迟阈值(ms)
    public int ProcessingThreshold { get; set; }
    
    // 钉钉Webhook URL
    public string WebhookUrl { get; set; }
    
    // 是否启用调试模式
    public bool DebugMode { get; set; }
}

// 模拟器配置
public class EmulatorConfig
{
    // 模拟器名称
    public string Name { get; set; }
    
    // 模拟器区域
    public Rectangle Region { get; set; }
    
    // 星系名称区域相对位置
    public Rectangle SystemNameRegion { get; set; }
    
    // 舰船表格区域相对位置
    public Rectangle ShipTableRegion { get; set; }
}
```

## 6. 安装与部署

### 6.1 系统要求

- **操作系统**：Windows 10 1803+ 或 Windows 11
- **处理器**：双核心CPU 2.0GHz以上
- **内存**：4GB RAM以上
- **显卡**：支持DirectX 11
- **.NET运行时**：.NET 6.0 Runtime或更高版本

### 6.2 安装包制作

使用NSIS或WiX Toolset制作安装包，包含以下内容：

- 应用程序主程序
- .NET 6.0 Runtime安装检查
- Tesseract OCR引擎及语言包
- 默认配置文件
- 示例模拟器布局模板

### 6.3 自动更新机制

实现基于GitHub Releases或自定义服务器的自动更新机制：

```csharp
public class AutoUpdater
{
    // 检查更新
    public async Task<UpdateInfo> CheckForUpdatesAsync();
    
    // 下载更新
    public async Task DownloadUpdateAsync(UpdateInfo updateInfo, IProgress<int> progress);
    
    // 应用更新
    public void ApplyUpdate(UpdateInfo updateInfo);
}
```

## 7. 安全与隐私

### 7.1 数据安全

- 所有截图数据仅在内存中处理，不保存原始图像
- 配置文件中的敏感信息（如钉钉Webhook URL）进行加密存储
- 警报数据可选择性本地存储，且可设置自动清理策略

### 7.2 隐私保护

- 仅捕获用户明确设置的屏幕区域
- 不收集任何用户个人信息
- 不发送任何遥测数据到外部服务器（除用户配置的警报推送）

## 8. 开发计划

### 8.1 阶段规划

| 阶段 | 时间周期 | 主要任务 |
|-----|---------|---------|
| 阶段一 | 2周 | 核心架构设计，屏幕捕获模块实现 |
| 阶段二 | 2周 | 图像处理和OCR模块实现 |
| 阶段三 | 1周 | 警报推送模块实现 |
| 阶段四 | 2周 | UI界面实现 |
| 阶段五 | 1周 | 测试与优化 |

### 8.2 优先级排序

1. 核心屏幕捕获与分割功能
2. OCR识别功能
3. 警报推送功能
4. 队列管理与性能优化
5. 用户配置界面
6. 热加载与调试功能

## 9. 测试方案

### 9.1 单元测试

针对各个核心模块编写单元测试：

- 图像处理算法测试
- OCR识别准确率测试
- 配置管理测试
- 警报推送测试

### 9.2 集成测试

- 端到端流程测试
- 性能压力测试
- 多模拟器并发测试
- 长时间稳定性测试

### 9.3 测试数据集

收集不同模拟器、不同游戏场景的截图样本，构建测试数据集：

- 不同星系名称样本
- 不同舰船类型样本
- 不同表格布局样本
- 各种异常场景样本

## 10. 附录

### 10.1 关键技术参考

- [Windows.Graphics.Capture API 文档](https://docs.microsoft.com/en-us/uwp/api/windows.graphics.capture)
- [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
- [钉钉开放平台文档](https://open.dingtalk.com/document/)
- [TPL Dataflow 文档](https://docs.microsoft.com/en-us/dotnet/standard/parallel-programming/dataflow-task-parallel-library)

### 10.2 项目结构

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

### 10.3 第三方依赖

| 依赖项 | 版本 | 用途 |
|-------|-----|------|
| .NET  | 6.0+ | 开发框架 |
| Tesseract | 5.0.0+ | OCR引擎 |
| OpenCvSharp4 | 4.6.0+ | 图像处理 |
| Newtonsoft.Json | 13.0.1+ | JSON处理 |
| System.Drawing.Common | 6.0.0+ | 基础图像处理 |
| MaterialDesignThemes | 4.5.0+ | UI界面主题 |
| Serilog | 2.10.0+ | 日志记录 |
</rewritten_file> 