using System.Drawing;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 截图处理服务接口
    /// </summary>
    public interface IScreenshotService
    {
        /// <summary>
        /// 获取指定模拟器的截图
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>截图</returns>
        Task<Bitmap> CaptureScreenshotAsync(int emulatorIndex);

        /// <summary>
        /// 开始截图处理服务
        /// </summary>
        /// <param name="interval">截图间隔（毫秒）</param>
        /// <returns>操作是否成功</returns>
        Task<bool> StartAsync(int interval = 1000);

        /// <summary>
        /// 停止截图处理服务
        /// </summary>
        /// <returns>操作是否成功</returns>
        Task<bool> StopAsync();

        /// <summary>
        /// 处理单张截图
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>处理结果</returns>
        Task<ScreenshotAnalysisResult> ProcessScreenshotAsync(Bitmap screenshot, int emulatorIndex);

        /// <summary>
        /// 保存截图到文件
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="filePath">文件路径</param>
        /// <returns>操作是否成功</returns>
        Task<bool> SaveScreenshotAsync(Bitmap screenshot, string filePath);

        /// <summary>
        /// 截图服务状态
        /// </summary>
        bool IsRunning { get; }

        /// <summary>
        /// 当前截图间隔（毫秒）
        /// </summary>
        int CurrentInterval { get; }

        /// <summary>
        /// 截图分析完成事件
        /// </summary>
        event EventHandler<ScreenshotAnalysisEventArgs> ScreenshotAnalysisCompleted;
    }

    /// <summary>
    /// 截图分析事件参数
    /// </summary>
    public class ScreenshotAnalysisEventArgs : EventArgs
    {
        /// <summary>
        /// 分析结果
        /// </summary>
        public ScreenshotAnalysisResult Result { get; }

        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int EmulatorIndex { get; }

        /// <summary>
        /// 初始化截图分析事件参数
        /// </summary>
        /// <param name="result">分析结果</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        public ScreenshotAnalysisEventArgs(ScreenshotAnalysisResult result, int emulatorIndex)
        {
            Result = result;
            EmulatorIndex = emulatorIndex;
        }
    }
} 