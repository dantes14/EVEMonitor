using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Capture.Services
{
    /// <summary>
    /// 屏幕捕获服务实现
    /// </summary>
    public class ScreenCaptureService : IScreenCaptureService
    {
        private readonly ILogger _logger;
        private readonly Timer _captureTimer;
        private bool _isCapturing = false;
        private bool _disposed = false;

        /// <summary>
        /// 捕获区域
        /// </summary>
        public Rectangle CaptureRegion { get; set; }

        /// <summary>
        /// 捕获间隔(毫秒)
        /// </summary>
        public int CaptureInterval { get; set; }

        /// <summary>
        /// 屏幕捕获事件
        /// </summary>
        public event EventHandler<ScreenCaptureEventArgs> ScreenCaptured;

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
        public ScreenCaptureService(ILogger logger, Rectangle captureRegion, int captureInterval = 1000)
        {
            _logger = logger;
            CaptureRegion = captureRegion;
            CaptureInterval = captureInterval;
            _captureTimer = new Timer { Interval = CaptureInterval };
            _captureTimer.Tick += CaptureTimer_Tick;
        }

        /// <summary>
        /// 开始捕获
        /// </summary>
        public void Start()
        {
            if (_isCapturing)
                return;

            _captureTimer.Interval = CaptureInterval;
            _captureTimer.Start();
            _isCapturing = true;
        }

        /// <summary>
        /// 停止捕获
        /// </summary>
        public void Stop()
        {
            if (!_isCapturing)
                return;

            _captureTimer.Stop();
            _isCapturing = false;
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
                CaptureRegion = new Rectangle(0, 0, Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height);
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
                // 如果捕获失败，释放位图并返回null
                bitmap.Dispose();
                Console.WriteLine($"捕获屏幕失败: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 定时器回调，执行屏幕捕获
        /// </summary>
        private void CaptureTimer_Tick(object sender, EventArgs e)
        {
            try
            {
                var bitmap = CaptureFrame();
                OnScreenCaptured(bitmap);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"定时捕获失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 触发截图事件
        /// </summary>
        /// <param name="screenshot">截图</param>
        protected virtual void OnScreenCaptured(Bitmap screenshot)
        {
            ScreenCaptured?.Invoke(this, new ScreenCaptureEventArgs(screenshot));
        }

        /// <summary>
        /// 捕获特定窗口的屏幕截图
        /// </summary>
        /// <param name="windowHandle">窗口句柄</param>
        /// <param name="cropRect">裁剪区域，为null则不裁剪</param>
        /// <returns>捕获的位图</returns>
        public async Task<Bitmap> CaptureWindowAsync(IntPtr windowHandle, Rectangle? cropRect = null)
        {
            return await Task.Run(() =>
            {
                try
                {
                    if (windowHandle == IntPtr.Zero)
                    {
                        _logger?.LogWarning("无效的窗口句柄");
                        return null;
                    }

                    // 获取窗口尺寸
                    if (!GetWindowRect(windowHandle, out RECT windowRect))
                    {
                        _logger?.LogError($"无法获取窗口矩形区域，错误代码：{Marshal.GetLastWin32Error()}");
                        return null;
                    }

                    int width = windowRect.Right - windowRect.Left;
                    int height = windowRect.Bottom - windowRect.Top;

                    if (width <= 0 || height <= 0)
                    {
                        _logger?.LogWarning($"窗口尺寸无效：{width}x{height}");
                        return null;
                    }

                    // 创建位图
                    Bitmap bitmap = new Bitmap(width, height);

                    using (Graphics graphics = Graphics.FromImage(bitmap))
                    {
                        // 设置图形质量
                        graphics.CompositingQuality = System.Drawing.Drawing2D.CompositingQuality.HighQuality;
                        graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
                        graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.HighQuality;

                        // 复制窗口内容到位图
                        graphics.CopyFromScreen(
                            windowRect.Left,
                            windowRect.Top,
                            0,
                            0,
                            new Size(width, height),
                            CopyPixelOperation.SourceCopy);
                    }

                    // 如果需要裁剪
                    if (cropRect.HasValue)
                    {
                        Rectangle crop = cropRect.Value;
                        
                        // 确保裁剪区域在位图范围内
                        if (crop.X >= 0 && crop.Y >= 0 && crop.Width > 0 && crop.Height > 0 &&
                            crop.X + crop.Width <= bitmap.Width && crop.Y + crop.Height <= bitmap.Height)
                        {
                            Bitmap croppedBitmap = new Bitmap(crop.Width, crop.Height);
                            using (Graphics g = Graphics.FromImage(croppedBitmap))
                            {
                                g.DrawImage(bitmap, new Rectangle(0, 0, crop.Width, crop.Height),
                                    crop, GraphicsUnit.Pixel);
                            }
                            bitmap.Dispose();
                            bitmap = croppedBitmap;
                        }
                        else
                        {
                            _logger?.LogWarning($"裁剪区域超出位图范围：位图={bitmap.Width}x{bitmap.Height}，裁剪={crop}");
                        }
                    }

                    // 触发事件
                    ScreenCaptured?.Invoke(this, new ScreenCaptureEventArgs
                    {
                        WindowHandle = windowHandle,
                        CapturedImage = bitmap,
                        CaptureTime = DateTime.Now
                    });

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
        /// 捕获多个窗口的屏幕截图
        /// </summary>
        /// <param name="windowHandles">窗口句柄集合</param>
        /// <param name="cropRects">裁剪区域集合，可为null</param>
        /// <returns>捕获的位图集合</returns>
        public async Task<Dictionary<IntPtr, Bitmap>> CaptureWindowsAsync(IEnumerable<IntPtr> windowHandles, Dictionary<IntPtr, Rectangle> cropRects = null)
        {
            Dictionary<IntPtr, Bitmap> results = new Dictionary<IntPtr, Bitmap>();

            foreach (var handle in windowHandles)
            {
                Rectangle? cropRect = null;
                if (cropRects != null && cropRects.TryGetValue(handle, out Rectangle rect))
                {
                    cropRect = rect;
                }

                var bitmap = await CaptureWindowAsync(handle, cropRect);
                if (bitmap != null)
                {
                    results[handle] = bitmap;
                }
            }

            return results;
        }

        /// <summary>
        /// 捕获整个屏幕的截图
        /// </summary>
        /// <returns>捕获的位图</returns>
        public async Task<Bitmap> CaptureScreenAsync()
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

                    // 触发事件
                    ScreenCaptured?.Invoke(this, new ScreenCaptureEventArgs
                    {
                        WindowHandle = IntPtr.Zero, // 表示全屏
                        CapturedImage = bitmap,
                        CaptureTime = DateTime.Now
                    });

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
                IntPtr handle = FindWindow(null, windowTitle);
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
                Stop();
                _captureTimer.Dispose();
            }

            _disposed = true;
        }

        #region Win32 API

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

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
    }
} 