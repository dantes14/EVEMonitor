using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Runtime.Versioning;
using System.Windows.Forms;
using Timer = System.Timers.Timer;
using ElapsedEventArgs = System.Timers.ElapsedEventArgs;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using Microsoft.Extensions.Logging;

namespace EVEMonitor.Capture.Services
{
    /// <summary>
    /// 屏幕捕获服务实现
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class ScreenCaptureService : IScreenCaptureService, IDisposable
    {
        private readonly ILogger<ScreenCaptureService> _logger;
        private readonly Timer _captureTimer;
        private bool _isCapturing = false;
        private bool _disposed = false;
        private Rectangle _captureRegion;
        private int _captureInterval = 1000;

        /// <summary>
        /// 屏幕捕获事件
        /// </summary>
        public event EventHandler<ScreenCaptureEventArgs>? ScreenCaptured;

        /// <summary>
        /// 捕获区域
        /// </summary>
        public Rectangle CaptureRegion
        {
            get => _captureRegion;
            set => _captureRegion = value;
        }

        /// <summary>
        /// 捕获间隔(毫秒)
        /// </summary>
        public int CaptureInterval
        {
            get => _captureInterval;
            set
            {
                if (value < 100)
                    throw new ArgumentException("捕获间隔不能小于100毫秒");
                _captureInterval = value;
                if (_captureTimer != null)
                    _captureTimer.Interval = value;
            }
        }

        /// <summary>
        /// 是否正在捕获
        /// </summary>
        public bool IsCapturing => _isCapturing;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="logger">日志服务</param>
        /// <param name="captureRegion">捕获区域</param>
        /// <param name="captureInterval">捕获间隔(毫秒)</param>
        public ScreenCaptureService(ILogger<ScreenCaptureService> logger, Rectangle captureRegion, int captureInterval = 1000)
        {
            _logger = logger;
            _captureRegion = captureRegion;
            _captureInterval = captureInterval;
            _captureTimer = new Timer(CaptureInterval);
            _captureTimer.Elapsed += CaptureTimer_Tick;
        }

        /// <summary>
        /// 开始捕获
        /// </summary>
        public void Start()
        {
            if (_isCapturing)
                return;

            _captureTimer.Interval = CaptureInterval;
            _captureTimer.Enabled = true;
            _isCapturing = true;
            _logger.LogInformation("屏幕捕获服务已启动");
        }

        /// <summary>
        /// 停止捕获
        /// </summary>
        public void Stop()
        {
            if (!_isCapturing)
                return;

            _captureTimer.Enabled = false;
            _isCapturing = false;
            _logger.LogInformation("屏幕捕获服务已停止");
        }

        /// <summary>
        /// 捕获单帧
        /// </summary>
        /// <returns>捕获的截图</returns>
        public Bitmap CaptureFrame()
        {
            // 如果捕获区域无效，则捕获整个主屏幕
            if (CaptureRegion.Width <= 0 || CaptureRegion.Height <= 0)
            {
                var screen = Screen.PrimaryScreen;
                if (screen == null)
                {
                    throw new InvalidOperationException("无法获取主屏幕信息");
                }
                CaptureRegion = screen.Bounds;
            }

            // 创建位图对象
            Bitmap bitmap = new Bitmap(CaptureRegion.Width, CaptureRegion.Height, PixelFormat.Format32bppArgb);

            try
            {
                // 使用Graphics对象捕获屏幕内容
                using (Graphics graphics = Graphics.FromImage(bitmap))
                {
                    graphics.CopyFromScreen(
                        CaptureRegion.X,
                        CaptureRegion.Y,
                        0,
                        0,
                        CaptureRegion.Size,
                        CopyPixelOperation.SourceCopy
                    );
                }

                return bitmap;
            }
            catch (Exception ex)
            {
                // 如果捕获失败，释放位图并抛出异常
                bitmap.Dispose();
                _logger.LogError(ex, "捕获屏幕失败");
                throw;
            }
        }

        /// <summary>
        /// 定时器回调，执行屏幕捕获
        /// </summary>
        private void CaptureTimer_Tick(object? sender, ElapsedEventArgs e)
        {
            try
            {
                var bitmap = CaptureFrame();
                OnScreenCaptured(bitmap);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "定时捕获失败");
            }
        }

        /// <summary>
        /// 触发截图事件
        /// </summary>
        /// <param name="screenshot">截图</param>
        protected virtual void OnScreenCaptured(Bitmap screenshot)
        {
            // 捕获到截图后触发事件
            if (ScreenCaptured != null && screenshot != null)
            {
                // 使用新版本的ScreenCaptureEventArgs类
                var args = new ScreenCaptureEventArgs(screenshot)
                {
                    WindowHandle = IntPtr.Zero,
                    CaptureTime = DateTime.Now
                };
                ScreenCaptured.Invoke(this, args);
            }
        }

        /// <summary>
        /// 捕获指定窗口的屏幕
        /// </summary>
        /// <param name="windowTitle">窗口标题</param>
        /// <returns>截图</returns>
        public async Task<Bitmap?> CaptureWindowAsync(string windowTitle)
        {
            try
            {
                return await Task.Run(() =>
                {
                    var handle = FindWindow(string.Empty, windowTitle);
                    if (handle == IntPtr.Zero)
                    {
                        _logger.LogWarning("未找到窗口：{WindowTitle}", windowTitle);
                        return null;
                    }

                    return CaptureWindowByHandle(handle);
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "捕获窗口截图时发生错误：{WindowTitle}", windowTitle);
                return null;
            }
        }

        /// <summary>
        /// 捕获指定窗口的屏幕
        /// </summary>
        /// <param name="handle">窗口句柄</param>
        /// <returns>截图</returns>
        public async Task<Bitmap?> CaptureWindowAsync(IntPtr handle)
        {
            try
            {
                return await Task.Run(() => CaptureWindowByHandle(handle));
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "捕获窗口截图时发生错误：{Handle}", handle);
                return null;
            }
        }

        private Bitmap? CaptureWindowByHandle(IntPtr handle)
        {
            if (handle == IntPtr.Zero)
            {
                _logger.LogWarning("无效的窗口句柄");
                return null;
            }

            // 获取窗口位置和大小
            GetWindowRect(handle, out RECT rect);
            var width = rect.Right - rect.Left;
            var height = rect.Bottom - rect.Top;

            if (width <= 0 || height <= 0)
            {
                _logger.LogWarning("窗口大小无效：{Handle}", handle);
                return null;
            }

            // 创建截图
            var bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
            using (var graphics = Graphics.FromImage(bitmap))
            {
                graphics.CopyFromScreen(rect.Left, rect.Top, 0, 0, new Size(width, height), CopyPixelOperation.SourceCopy);
            }

            // 触发事件
            var args = new ScreenCaptureEventArgs(bitmap)
            {
                WindowHandle = handle,
                CaptureTime = DateTime.Now
            };
            ScreenCaptured?.Invoke(this, args);

            return bitmap;
        }

        /// <summary>
        /// 捕获多个窗口的屏幕截图
        /// </summary>
        /// <param name="windowHandles">窗口句柄集合</param>
        /// <param name="cropRects">裁剪区域集合，可为null</param>
        /// <returns>捕获的位图集合</returns>
        public async Task<Dictionary<IntPtr, Bitmap>> CaptureWindowsAsync(IEnumerable<IntPtr> windowHandles, Dictionary<IntPtr, Rectangle>? cropRects = null)
        {
            Dictionary<IntPtr, Bitmap> results = new Dictionary<IntPtr, Bitmap>();

            foreach (var handle in windowHandles)
            {
                var bitmap = await CaptureWindowAsync(handle);
                if (bitmap != null)
                {
                    if (cropRects != null && cropRects.TryGetValue(handle, out var cropRect))
                    {
                        // 如果有裁剪区域，则裁剪图像
                        var croppedBitmap = new Bitmap(cropRect.Width, cropRect.Height);
                        using (var graphics = Graphics.FromImage(croppedBitmap))
                        {
                            graphics.DrawImage(bitmap, new Rectangle(0, 0, cropRect.Width, cropRect.Height),
                                cropRect, GraphicsUnit.Pixel);
                        }
                        bitmap.Dispose();
                        bitmap = croppedBitmap;
                    }
                    results[handle] = bitmap;
                }
            }

            return results;
        }

        /// <summary>
        /// 捕获整个屏幕的截图
        /// </summary>
        /// <returns>捕获的位图</returns>
        public async Task<Bitmap?> CaptureScreenAsync()
        {
            return await Task.Run(() =>
            {
                try
                {
                    // 获取主屏幕尺寸
                    int screenWidth = GetSystemMetrics(SM_CXSCREEN);
                    int screenHeight = GetSystemMetrics(SM_CYSCREEN);

                    // 创建位图
                    Bitmap bitmap = new Bitmap(screenWidth, screenHeight);

                    using (Graphics graphics = Graphics.FromImage(bitmap))
                    {
                        // 设置图形质量
                        graphics.CompositingQuality = System.Drawing.Drawing2D.CompositingQuality.HighQuality;
                        graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
                        graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.HighQuality;

                        // 复制屏幕内容到位图
                        graphics.CopyFromScreen(
                            0,
                            0,
                            0,
                            0,
                            new Size(screenWidth, screenHeight),
                            CopyPixelOperation.SourceCopy);
                    }

                    // 使用新版本的ScreenCaptureEventArgs类
                    var args = new ScreenCaptureEventArgs(bitmap)
                    {
                        WindowHandle = IntPtr.Zero,
                        CapturedImage = bitmap,
                        CaptureTime = DateTime.Now
                    };
                    ScreenCaptured?.Invoke(this, args);

                    return bitmap;
                }
                catch (Exception ex)
                {
                    _logger?.LogError($"屏幕捕获异常：{ex.Message}");
                    return null;
                }
            });
        }

        /// <summary>
        /// 查找指定标题的窗口句柄
        /// </summary>
        /// <param name="windowTitle">窗口标题</param>
        /// <returns>窗口句柄</returns>
        public IntPtr FindWindowByTitle(string windowTitle)
        {
            if (string.IsNullOrEmpty(windowTitle))
            {
                _logger?.LogWarning("窗口标题为空");
                return IntPtr.Zero;
            }

            try
            {
                IntPtr handle = FindWindow(string.Empty, windowTitle);
                if (handle == IntPtr.Zero)
                {
                    _logger?.LogWarning($"未找到标题为'{windowTitle}'的窗口");
                }
                return handle;
            }
            catch (Exception ex)
            {
                _logger?.LogError($"查找窗口异常：{ex.Message}");
                return IntPtr.Zero;
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            if (!_disposed)
            {
                _captureTimer?.Dispose();
                _disposed = true;
            }
        }

        #region Win32 API

        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);

        [DllImport("user32.dll")]
        private static extern int GetSystemMetrics(int nIndex);

        private const int SM_CXSCREEN = 0;
        private const int SM_CYSCREEN = 1;

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;

            public override string ToString()
            {
                return $"{{X={Left},Y={Top},Width={Right - Left},Height={Bottom - Top}}}";
            }
        }

        #endregion

        private Bitmap? CaptureWindow(IntPtr hWnd)
        {
            try
            {
                if (!GetWindowRect(hWnd, out RECT rect))
                {
                    _logger.LogWarning("获取窗口位置失败");
                    return null;
                }

                int width = rect.Right - rect.Left;
                int height = rect.Bottom - rect.Top;

                if (width <= 0 || height <= 0)
                {
                    _logger.LogWarning("窗口大小无效：width={Width}, height={Height}", width, height);
                    return null;
                }

                var bitmap = new Bitmap(width, height);
                using var graphics = Graphics.FromImage(bitmap);
                graphics.CopyFromScreen(rect.Left, rect.Top, 0, 0, new Size(width, height));

                return bitmap;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "截图过程中发生错误");
                return null;
            }
        }

        private IntPtr FindEmulatorWindow(string windowTitle)
        {
            return FindWindow(string.Empty, windowTitle);
        }
    }
}