using System.Drawing;
using System.Drawing.Imaging;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.Core.Utils;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 截图处理服务实现
    /// </summary>
    public class ScreenshotService : IScreenshotService, IDisposable
    {
        private readonly IConfigService _configService;
        private readonly IScreenCaptureService _captureService;
        private readonly IImageProcessingService _imageProcessingService;
        private readonly IOcrService _ocrService;
        private readonly IAlertService _alertService;
        private readonly ScreenshotQueue _screenshotQueue;
        private CancellationTokenSource _cancellationTokenSource;
        private Task _processingTask;
        private int _currentInterval = 1000;
        private bool _isRunning = false;
        private bool _disposed = false;
        private readonly object _lockObject = new object();

        /// <summary>
        /// 截图服务状态
        /// </summary>
        public bool IsRunning => _isRunning;

        /// <summary>
        /// 当前截图间隔（毫秒）
        /// </summary>
        public int CurrentInterval => _currentInterval;

        /// <summary>
        /// 截图分析完成事件
        /// </summary>
        public event EventHandler<ScreenshotAnalysisEventArgs> ScreenshotAnalysisCompleted;

        /// <summary>
        /// 初始化截图处理服务
        /// </summary>
        /// <param name="configService">配置服务</param>
        /// <param name="captureService">屏幕捕获服务</param>
        /// <param name="imageProcessingService">图像处理服务</param>
        /// <param name="ocrService">OCR服务</param>
        /// <param name="alertService">警报服务</param>
        public ScreenshotService(
            IConfigService configService,
            IScreenCaptureService captureService,
            IImageProcessingService imageProcessingService,
            IOcrService ocrService,
            IAlertService alertService)
        {
            _configService = configService;
            _captureService = captureService;
            _imageProcessingService = imageProcessingService;
            _ocrService = ocrService;
            _alertService = alertService;
            _screenshotQueue = new ScreenshotQueue(_configService.CurrentConfig.Performance.MaxThreads * 2);

            // 订阅屏幕捕获事件
            _captureService.ScreenCaptured += CaptureService_ScreenCaptured;

            // 订阅配置变更事件
            _configService.ConfigChanged += ConfigService_ConfigChanged;
        }

        /// <summary>
        /// 获取指定模拟器的截图
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>截图</returns>
        public async Task<Bitmap> CaptureScreenshotAsync(int emulatorIndex)
        {
            if (emulatorIndex < 0 || emulatorIndex >= _configService.CurrentConfig.Emulators.Count)
                return null;

            var config = _configService.CurrentConfig.Emulators[emulatorIndex];
            if (!config.Enabled)
                return null;

            try
            {
                // 如果有有效的窗口句柄，则捕获窗口
                if (config.WindowHandle != IntPtr.Zero)
                {
                    // 窗口捕获逻辑
                    // 这里简化处理，直接捕获全屏
                }

                // 捕获屏幕
                var screenshot = _captureService.CaptureFrame();
                if (screenshot == null)
                    return null;

                // 如果需要裁剪，则处理裁剪
                var captureRegion = config.CaptureRegion;
                if (captureRegion.Width > 0 && captureRegion.Height > 0)
                {
                    var region = new Rectangle(
                        captureRegion.X,
                        captureRegion.Y,
                        captureRegion.Width,
                        captureRegion.Height
                    );

                    // 检查区域有效性
                    if (region.Width <= 0 || region.Height <= 0 ||
                        region.X < 0 || region.Y < 0 ||
                        region.Right > screenshot.Width || region.Bottom > screenshot.Height)
                    {
                        return screenshot;
                    }

                    // 裁剪截图
                    var croppedScreenshot = new Bitmap(region.Width, region.Height);
                    using (var g = Graphics.FromImage(croppedScreenshot))
                    {
                        g.DrawImage(screenshot, new Rectangle(0, 0, region.Width, region.Height), region, GraphicsUnit.Pixel);
                    }

                    screenshot.Dispose();
                    return croppedScreenshot;
                }

                return screenshot;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"获取模拟器 {emulatorIndex} 截图失败: {ex.Message}");
                return null;
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
                _captureService.CaptureInterval = interval;

                // 启动取消令牌
                _cancellationTokenSource = new CancellationTokenSource();
                var token = _cancellationTokenSource.Token;

                // 启动处理任务
                _processingTask = Task.Run(() => ProcessScreenshotsAsync(token), token);

                // 启动屏幕捕获
                _captureService.Start();

                _isRunning = true;
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"启动截图处理服务失败: {ex.Message}");
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
                _captureService.Stop();

                // 停止处理任务
                if (_cancellationTokenSource != null)
                {
                    _cancellationTokenSource.Cancel();
                    _cancellationTokenSource.Dispose();
                    _cancellationTokenSource = null;
                }

                // 等待处理任务完成
                if (_processingTask != null)
                {
                    try
                    {
                        await Task.WhenAny(_processingTask, Task.Delay(1000));
                    }
                    catch { }
                    _processingTask = null;
                }

                // 清空队列
                _screenshotQueue.Complete();

                _isRunning = false;
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"停止截图处理服务失败: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 处理单张截图
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>处理结果</returns>
        public async Task<ScreenshotAnalysisResult> ProcessScreenshotAsync(Bitmap screenshot, int emulatorIndex)
        {
            if (screenshot == null || emulatorIndex < 0 || emulatorIndex >= _configService.CurrentConfig.Emulators.Count)
                return new ScreenshotAnalysisResult { Success = false, ErrorMessage = "无效的参数" };

            var startTime = DateTime.Now;
            var result = new ScreenshotAnalysisResult
            {
                OriginalScreenshot = screenshot,
                ProcessedScreenshot = (Bitmap)screenshot.Clone()
            };

            try
            {
                // 1. 处理截图，提取感兴趣区域
                var emulatorImage = new EmulatorImage
                {
                    Index = emulatorIndex,
                    Image = screenshot,
                    Region = new Rectangle(0, 0, screenshot.Width, screenshot.Height)
                };

                var rois = _imageProcessingService.ExtractROIs(emulatorImage);
                if (rois.Count == 0)
                {
                    result.Success = false;
                    result.ErrorMessage = "未能提取感兴趣区域";
                    return result;
                }

                // 2. 识别星系名称
                var systemNameROI = rois.FirstOrDefault(r => r.Type == RegionOfInterestType.SystemName);
                string systemName = "";
                if (systemNameROI != null)
                {
                    systemName = _ocrService.RecognizeSystemName(systemNameROI.Image);
                    result.SystemName = systemName;
                }

                // 3. 识别舰船表格
                var shipTableROI = rois.FirstOrDefault(r => r.Type == RegionOfInterestType.ShipTable);
                List<ShipInfo> ships = new List<ShipInfo>();
                if (shipTableROI != null)
                {
                    ships = _ocrService.RecognizeShipTable(shipTableROI.Image);
                    result.DetectedShips = ships;
                }

                // 4. 处理识别结果
                result.Success = true;

                // 5. 如果检测到危险舰船，发送警报
                if (result.DangerDetected && result.DangerLevel >= _configService.CurrentConfig.DangerThreshold)
                {
                    await _alertService.PushShipAlertAsync(systemName, ships, emulatorIndex);
                }

                // 6. 如果需要，保存截图
                if (_configService.CurrentConfig.SaveScreenshots)
                {
                    if (!_configService.CurrentConfig.SaveDangerousScreenshotsOnly || result.DangerDetected)
                    {
                        string filename = $"{DateTime.Now:yyyyMMdd_HHmmss}_{emulatorIndex}_{systemName}.png";
                        string path = Path.Combine(_configService.CurrentConfig.ScreenshotSavePath, filename);
                        await SaveScreenshotAsync(screenshot, path);
                    }
                }
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"处理截图时发生错误: {ex.Message}";
            }
            finally
            {
                var endTime = DateTime.Now;
                result.ProcessingTime = endTime - startTime;

                // 检查处理时间是否超过阈值，如果超过则发送性能警报
                if (result.ProcessingTime.TotalMilliseconds > _configService.CurrentConfig.Performance.PerformanceAlertThresholdMs)
                {
                    await _alertService.PushPerformanceAlertAsync(
                        $"截图处理时间超过阈值 (模拟器 #{emulatorIndex + 1})",
                        result.ProcessingTime);
                }

                // 触发分析完成事件
                OnScreenshotAnalysisCompleted(result, emulatorIndex);
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
                string directory = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 异步保存截图
                await Task.Run(() =>
                {
                    screenshot.Save(filePath, ImageFormat.Png);
                });

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"保存截图失败: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 屏幕捕获事件处理
        /// </summary>
        private async void CaptureService_ScreenCaptured(object sender, ScreenCaptureEventArgs e)
        {
            if (e.Screenshot == null || !_isRunning)
                return;

            try
            {
                // 将截图添加到队列
                await _screenshotQueue.EnqueueAsync((Bitmap)e.Screenshot.Clone());
            }
            catch (Exception ex)
            {
                Console.WriteLine($"添加截图到队列失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 配置变更事件处理
        /// </summary>
        private void ConfigService_ConfigChanged(object sender, ConfigChangedEventArgs e)
        {
            if (_isRunning && e.Config.ScreenshotInterval != _currentInterval)
            {
                _currentInterval = e.Config.ScreenshotInterval;
                _captureService.CaptureInterval = _currentInterval;
            }

            // 更新图像处理服务的模拟器配置
            _imageProcessingService.EmulatorConfigs = e.Config.Emulators;
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
                    var screenshot = await _screenshotQueue.DequeueAsync(cancellationToken);
                    if (screenshot == null)
                        continue;

                    // 获取处理配置
                    int maxThreads = _configService.CurrentConfig.Performance.MaxThreads;
                    var emulators = _configService.CurrentConfig.Emulators.Where(e => e.Enabled).ToList();

                    // 处理每个模拟器
                    foreach (var emulator in emulators)
                    {
                        int emulatorIndex = _configService.CurrentConfig.Emulators.IndexOf(emulator);
                        
                        // 处理单个模拟器的截图
                        _ = Task.Run(async () =>
                        {
                            try
                            {
                                await ProcessScreenshotAsync(screenshot, emulatorIndex);
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"处理模拟器 {emulatorIndex} 截图失败: {ex.Message}");
                            }
                        }, cancellationToken);
                    }
                }
                catch (OperationCanceledException)
                {
                    // 任务被取消，退出循环
                    break;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"处理截图队列时发生错误: {ex.Message}");
                    // 短暂延迟，避免CPU占用过高
                    await Task.Delay(100, cancellationToken);
                }
            }
        }

        /// <summary>
        /// 触发截图分析完成事件
        /// </summary>
        /// <param name="result">分析结果</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        protected virtual void OnScreenshotAnalysisCompleted(ScreenshotAnalysisResult result, int emulatorIndex)
        {
            ScreenshotAnalysisCompleted?.Invoke(this, new ScreenshotAnalysisEventArgs(result, emulatorIndex));
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
        /// <param name="disposing">是否释放托管资源</param>
        protected virtual void Dispose(bool disposing)
        {
            if (_disposed)
                return;

            if (disposing)
            {
                // 停止服务
                StopAsync().Wait();

                // 取消订阅事件
                if (_captureService != null)
                {
                    _captureService.ScreenCaptured -= CaptureService_ScreenCaptured;
                }

                if (_configService != null)
                {
                    _configService.ConfigChanged -= ConfigService_ConfigChanged;
                }
            }

            _disposed = true;
        }
    }
} 