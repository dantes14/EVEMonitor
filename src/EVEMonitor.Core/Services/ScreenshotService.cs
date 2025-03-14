using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Runtime.Versioning;
using System.Linq;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.Core.Utils;
using Microsoft.Extensions.Logging;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 截图服务实现
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class ScreenshotService : IScreenshotService, IDisposable
    {
        private readonly ILogger<ScreenshotService> _logger;
        private readonly IConfigService _configService;
        private readonly IImageProcessingService _imageProcessingService;
        private readonly IScreenCaptureService _screenCaptureService;
        private readonly IOcrService _ocrService;
        private readonly IAlertService _alertService;
        private readonly ScreenshotQueue _screenshotQueue;
        private CancellationTokenSource _cancellationTokenSource;
        private Task _processingTask;
        private bool _isRunning;
        private int _currentInterval;
        private bool _disposed;

        /// <summary>
        /// 截图分析完成事件
        /// </summary>
        public event EventHandler<ScreenshotAnalysisEventArgs>? ScreenshotAnalysisCompleted;

        /// <summary>
        /// 截图服务状态
        /// </summary>
        public bool IsRunning => _isRunning;

        /// <summary>
        /// 当前截图间隔（毫秒）
        /// </summary>
        public int CurrentInterval => _currentInterval;

        /// <summary>
        /// 初始化截图服务
        /// </summary>
        /// <param name="logger">日志记录器</param>
        /// <param name="configService">配置服务</param>
        /// <param name="imageProcessingService">图像处理服务</param>
        /// <param name="screenCaptureService">屏幕捕获服务</param>
        /// <param name="ocrService">OCR服务</param>
        /// <param name="alertService">警报服务</param>
        public ScreenshotService(
            ILogger<ScreenshotService> logger,
            IConfigService configService,
            IImageProcessingService imageProcessingService,
            IScreenCaptureService screenCaptureService,
            IOcrService ocrService,
            IAlertService alertService)
        {
            _logger = logger;
            _configService = configService;
            _imageProcessingService = imageProcessingService;
            _screenCaptureService = screenCaptureService;
            _ocrService = ocrService;
            _alertService = alertService;
            _screenshotQueue = new ScreenshotQueue();
            _cancellationTokenSource = new CancellationTokenSource();
            _processingTask = Task.CompletedTask;
            _isRunning = false;
            _currentInterval = 1000;
            _disposed = false;

            // 订阅屏幕捕获事件
            _screenCaptureService.ScreenCaptured += CaptureService_ScreenCaptured;
            _configService.ConfigChanged += ConfigService_ConfigChanged;
        }

        /// <summary>
        /// 异步截取指定模拟器的屏幕
        /// </summary>
        /// <param name="emulatorName">模拟器名称</param>
        /// <returns>截图</returns>
        public async Task<Bitmap?> TakeScreenshotAsync(string emulatorName)
        {
            try
            {
                var emulator = _configService.CurrentConfig.Emulators.FirstOrDefault(e => e.Name == emulatorName);
                if (emulator == null || !emulator.Enabled)
                    return null;

                var screenshot = await _screenCaptureService.CaptureWindowAsync(emulator.WindowTitle);
                if (screenshot == null)
                    return null;

                return _imageProcessingService.ProcessImage(screenshot, emulatorName);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "截取屏幕时发生错误");
                return null;
            }
        }

        /// <summary>
        /// 异步提取系统名称区域
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>系统名称区域</returns>
        public async Task<RegionOfInterest> ExtractSystemNameRegionAsync(int emulatorIndex)
        {
            try
            {
                var emulator = _configService.CurrentConfig.Emulators.FirstOrDefault(e => e.Index == emulatorIndex);
                if (emulator == null || !emulator.Enabled)
                    return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };

                var screenshot = await _screenCaptureService.CaptureWindowAsync(emulator.WindowTitle);
                if (screenshot == null)
                    return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };

                return _imageProcessingService.ExtractSystemNameRegion(screenshot, emulatorIndex);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "提取系统名称区域时发生错误");
                return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };
            }
        }

        /// <summary>
        /// 获取指定模拟器的截图
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>截图</returns>
        public async Task<Bitmap> CaptureScreenshotAsync(int emulatorIndex)
        {
            if (emulatorIndex < 0 || emulatorIndex >= _configService.CurrentConfig.Emulators.Count)
                return new Bitmap(1, 1);

            var emulator = _configService.CurrentConfig.Emulators[emulatorIndex];
            if (!emulator.Enabled)
                return new Bitmap(1, 1);

            try
            {
                var screenshot = await _screenCaptureService.CaptureWindowAsync(emulator.WindowTitle);
                if (screenshot == null)
                    return new Bitmap(1, 1);

                return _imageProcessingService.ProcessImage(screenshot, emulator.Name) ?? new Bitmap(1, 1);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"获取模拟器 {emulatorIndex} 截图失败");
                return new Bitmap(1, 1);
            }
        }

        /// <summary>
        /// 开始截图处理服务
        /// </summary>
        /// <param name="interval">截图间隔（毫秒）</param>
        /// <returns>操作是否成功</returns>
        public async Task<bool> StartAsync(int interval = 1000)
        {
            if (_isRunning)
                return false;

            try
            {
                _currentInterval = interval;
                _screenCaptureService.CaptureInterval = interval;

                // 启动取消令牌
                _cancellationTokenSource = new CancellationTokenSource();
                var token = _cancellationTokenSource.Token;

                // 启动处理任务
                _processingTask = Task.Run(() => ProcessScreenshotsAsync(token), token);

                // 启动屏幕捕获
                _screenCaptureService.Start();

                _isRunning = true;
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "启动截图处理服务失败");
                await StopAsync();
                return false;
            }
        }

        /// <summary>
        /// 停止截图处理服务
        /// </summary>
        /// <returns>操作是否成功</returns>
        public async Task<bool> StopAsync()
        {
            if (!_isRunning)
                return false;

            try
            {
                // 停止屏幕捕获
                _screenCaptureService.Stop();

                // 停止处理任务
                if (_cancellationTokenSource != null)
                {
                    _cancellationTokenSource.Cancel();
                    _cancellationTokenSource.Dispose();
                }
                _cancellationTokenSource = new CancellationTokenSource();

                // 等待处理任务完成
                if (_processingTask != null)
                {
                    try
                    {
                        await Task.WhenAny(_processingTask, Task.Delay(1000));
                    }
                    catch { }
                }
                _processingTask = Task.CompletedTask;

                // 清空队列
                _screenshotQueue.Complete();

                _isRunning = false;
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "停止截图处理服务失败");
                return false;
            }
        }

        /// <summary>
        /// 处理截图
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>处理结果</returns>
        public async Task<ScreenshotAnalysisResult> ProcessScreenshotAsync(Bitmap screenshot, int emulatorIndex)
        {
            if (screenshot == null || emulatorIndex < 0 || emulatorIndex >= _configService.CurrentConfig.Emulators.Count)
                return ScreenshotAnalysisResult.CreateFailureResult("无效的参数", screenshot, emulatorIndex);

            var startTime = DateTime.Now;
            var result = ScreenshotAnalysisResult.CreateSuccessResult("未知", screenshot, emulatorIndex);

            try
            {
                // 1. 获取模拟器配置
                var emulator = _configService.CurrentConfig.Emulators[emulatorIndex];
                if (!emulator.Enabled)
                {
                    return ScreenshotAnalysisResult.CreateFailureResult("模拟器未启用", screenshot, emulatorIndex);
                }

                // 2. 提取系统名称区域
                var systemNameROI = _imageProcessingService.ExtractSystemNameRegion(screenshot, emulatorIndex);
                string systemName = "未知";
                if (systemNameROI.Image != null)
                {
                    systemName = _ocrService.RecognizeSystemName(systemNameROI.Image);
                }

                // 3. 提取舰船表格区域
                var shipTableROI = _imageProcessingService.ExtractShipTableRegion(screenshot, emulatorIndex);
                List<ShipInfo> ships = new List<ShipInfo>();
                if (shipTableROI.Image != null)
                {
                    ships = _ocrService.RecognizeShipTable(shipTableROI.Image);
                }

                // 4. 处理识别结果
                var recognitionResult = _ocrService.ProcessRecognitionResult(emulatorIndex, systemName, ships);

                // 创建新的结果对象
                result = new ScreenshotAnalysisResult
                {
                    SystemName = systemName,
                    Ships = ships,
                    OriginalScreenshot = screenshot,
                    ProcessedScreenshot = shipTableROI.Image,
                    EmulatorIndex = emulatorIndex,
                    ContainsDangerousShips = recognitionResult.ContainsDangerousShips,
                    IsSuccessful = true
                };

                // 5. 如果检测到危险舰船，发送警报
                if (recognitionResult.ContainsDangerousShips)
                {
                    await _alertService.PushShipAlertAsync(systemName, ships, emulatorIndex);
                }

                // 6. 如果需要，保存截图
                if (_configService.CurrentConfig.SaveScreenshots)
                {
                    if (!_configService.CurrentConfig.SaveDangerousScreenshotsOnly || recognitionResult.ContainsDangerousShips)
                    {
                        string filename = $"{DateTime.Now:yyyyMMdd_HHmmss}_{emulatorIndex}_{systemName}.png";
                        string path = Path.Combine(_configService.CurrentConfig.ScreenshotSavePath, filename);
                        await SaveScreenshotAsync(screenshot, path);
                    }
                }
            }
            catch (Exception ex)
            {
                result = ScreenshotAnalysisResult.CreateFailureResult($"处理截图时发生错误: {ex.Message}", screenshot, emulatorIndex);
            }
            finally
            {
                // 设置处理时间
                result.SetProcessingTime();

                // 检查处理时间是否超过阈值，如果超过则发送性能警报
                if (result.ProcessingTime.TotalMilliseconds > _configService.CurrentConfig.Performance.PerformanceAlertThresholdMs)
                {
                    await _alertService.PushPerformanceAlertAsync(
                        $"截图处理时间超过阈值 (模拟器 #{emulatorIndex + 1})",
                        result.ProcessingTime);
                }

                // 触发分析完成事件
                OnScreenshotAnalysisCompleted(new ScreenshotAnalysisEventArgs(result, emulatorIndex));
            }

            return result;
        }

        /// <summary>
        /// 保存截图到文件
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="filePath">文件路径</param>
        /// <returns>操作是否成功</returns>
        public async Task<bool> SaveScreenshotAsync(Bitmap screenshot, string filePath)
        {
            if (screenshot == null || string.IsNullOrEmpty(filePath))
                return false;

            try
            {
                // 确保目录存在
                string? directory = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 异步保存截图
                await Task.Run(() =>
                {
                    screenshot.Save(filePath, System.Drawing.Imaging.ImageFormat.Png);
                });

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "保存截图失败");
                return false;
            }
        }

        /// <summary>
        /// 屏幕捕获事件处理
        /// </summary>
        private async void CaptureService_ScreenCaptured(object? sender, ScreenCaptureEventArgs e)
        {
            if (!_isRunning || e.Screenshot == null)
                return;

            try
            {
                // 将截图添加到队列
                await _screenshotQueue.EnqueueAsync(e.Screenshot);
            }
            catch (Exception ex)
            {
                // 记录错误但不中断处理
                _logger.LogError(ex, "处理截图时出错");
            }
        }

        /// <summary>
        /// 配置变更事件处理
        /// </summary>
        private void ConfigService_ConfigChanged(object? sender, ConfigChangedEventArgs e)
        {
            if (e.Config == null)
                return;

            // 更新截图间隔
            _currentInterval = e.Config.ScreenshotInterval;

            // 如果正在运行，且间隔发生变化，重新启动捕获服务
            if (_isRunning && _screenCaptureService.CaptureInterval != _currentInterval)
            {
                _screenCaptureService.Stop();
                _screenCaptureService.CaptureInterval = _currentInterval;
                _screenCaptureService.Start();
            }
        }

        /// <summary>
        /// 处理截图队列
        /// </summary>
        private async Task ProcessScreenshotsAsync(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    // 从队列获取截图
                    var screenshot = await _screenshotQueue.DequeueAsync();
                    if (cancellationToken.IsCancellationRequested)
                        break;

                    if (screenshot == null)
                        continue;

                    // 获取处理配置
                    int maxThreads = _configService.CurrentConfig.Performance.MaxThreads;
                    var emulators = _configService.CurrentConfig.Emulators.Where(e => e.Enabled).ToList();

                    // 创建任务列表
                    var tasks = new List<Task>();

                    // 处理每个模拟器
                    foreach (var emulator in emulators)
                    {
                        if (cancellationToken.IsCancellationRequested)
                            break;

                        int emulatorIndex = _configService.CurrentConfig.Emulators.IndexOf(emulator);

                        // 创建处理任务
                        var task = ProcessScreenshotAsync(screenshot, emulatorIndex)
                            .ContinueWith(t =>
                            {
                                if (t.IsFaulted)
                                {
                                    _logger.LogError(t.Exception?.InnerException, "处理模拟器 {EmulatorIndex} 截图失败", emulatorIndex);
                                }
                            }, cancellationToken, TaskContinuationOptions.None, TaskScheduler.Default);

                        tasks.Add(task);

                        // 如果达到最大线程数，等待一些任务完成
                        if (tasks.Count >= maxThreads)
                        {
                            await Task.WhenAny(tasks);
                            tasks.RemoveAll(t => t.IsCompleted);
                        }
                    }

                    // 等待所有剩余任务完成
                    if (tasks.Count > 0)
                    {
                        await Task.WhenAll(tasks);
                    }
                }
                catch (OperationCanceledException)
                {
                    // 任务被取消，退出循环
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "处理截图队列时发生错误");
                    // 短暂延迟，避免CPU占用过高
                    try
                    {
                        await Task.Delay(100, cancellationToken);
                    }
                    catch (OperationCanceledException)
                    {
                        break;
                    }
                }
            }
        }

        /// <summary>
        /// 触发截图分析完成事件
        /// </summary>
        /// <param name="e">事件参数</param>
        protected virtual void OnScreenshotAnalysisCompleted(ScreenshotAnalysisEventArgs e)
        {
            ScreenshotAnalysisCompleted?.Invoke(this, e);
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        /// <param name="disposing">是否正在释放托管资源</param>
        protected virtual void Dispose(bool disposing)
        {
            if (_disposed)
                return;

            if (disposing)
            {
                // 停止服务
                StopAsync().Wait();

                // 取消订阅事件
                if (_screenCaptureService != null)
                {
                    _screenCaptureService.ScreenCaptured -= CaptureService_ScreenCaptured;
                }
                if (_configService != null)
                {
                    _configService.ConfigChanged -= ConfigService_ConfigChanged;
                }

                // 释放资源
                _cancellationTokenSource?.Dispose();
                _screenshotQueue?.Dispose();
            }

            _disposed = true;
        }
    }
}