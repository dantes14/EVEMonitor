using System.Drawing;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 屏幕捕获事件参数
    /// </summary>
    public class ScreenCaptureEventArgs : EventArgs
    {
        /// <summary>
        /// 截图
        /// </summary>
        public Bitmap Screenshot { get; }

        /// <summary>
        /// 初始化屏幕捕获事件参数
        /// </summary>
        /// <param name="screenshot">截图</param>
        public ScreenCaptureEventArgs(Bitmap screenshot)
        {
            Screenshot = screenshot;
        }
    }

    /// <summary>
    /// 屏幕捕获服务接口
    /// </summary>
    public interface IScreenCaptureService : IDisposable
    {
        /// <summary>
        /// 捕获区域
        /// </summary>
        Rectangle CaptureRegion { get; set; }

        /// <summary>
        /// 捕获间隔(毫秒)
        /// </summary>
        int CaptureInterval { get; set; }

        /// <summary>
        /// 截图事件
        /// </summary>
        event EventHandler<ScreenCaptureEventArgs> ScreenCaptured;

        /// <summary>
        /// 开始捕获
        /// </summary>
        void Start();

        /// <summary>
        /// 停止捕获
        /// </summary>
        void Stop();

        /// <summary>
        /// 是否正在捕获
        /// </summary>
        bool IsCapturing { get; }

        /// <summary>
        /// 捕获单帧
        /// </summary>
        /// <returns>捕获的截图</returns>
        Bitmap CaptureFrame();
    }
} 