# EVE屏幕监控警报系统 - 测试项目

这个目录包含EVE屏幕监控警报系统的所有测试项目。

## 测试项目结构

- `EVEMonitor.Core.Tests` - 核心服务和模型的测试
- `EVEMonitor.Capture.Tests` - 屏幕捕获服务的测试
- `EVEMonitor.ImageProcessing.Tests` - 图像处理服务的测试
- `EVEMonitor.OCR.Tests` - OCR服务的测试
- `EVEMonitor.Config.Tests` - 配置服务的测试
- `EVEMonitor.Alert.Tests` - 警报服务的测试

## 运行测试

要运行所有测试，请使用以下命令：

```
dotnet test
```

要运行特定项目的测试，请使用以下命令：

```
dotnet test tests/EVEMonitor.Core.Tests
```

## 测试数据

测试项目依赖于以下测试数据：

1. **测试图像**：
   - 位于 `EVEMonitor.ImageProcessing.Tests/TestImages` 和 `EVEMonitor.OCR.Tests/TestImages` 目录
   - 包含游戏截图、系统名称和舰船列表的图像样本

2. **Tesseract数据文件**：
   - 位于 `EVEMonitor.OCR.Tests/tessdata` 目录
   - 需要下载 `eng.traineddata` 和 `chi_sim.traineddata` 文件

3. **测试配置文件**：
   - 位于 `EVEMonitor.Config.Tests/TestConfigs` 目录
   - 包含应用配置、已知星系和危险实体的JSON配置文件

## 测试覆盖率

测试项目旨在覆盖以下方面：

- 单元测试：测试各个服务和组件的独立功能
- 集成测试：测试多个组件之间的交互
- 边界条件测试：测试各种边界情况和异常处理

## 注意事项

- 运行OCR测试前，请确保已下载并放置Tesseract数据文件
- 运行图像处理和OCR测试前，请确保已准备好测试图像
- 某些测试可能依赖于系统环境（如屏幕捕获测试），在不同环境中可能需要调整 