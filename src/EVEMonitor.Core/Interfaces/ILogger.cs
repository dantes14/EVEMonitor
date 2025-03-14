namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 日志接口
    /// </summary>
    public interface ILogger
    {
        /// <summary>
        /// 记录跟踪信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogTrace(string message);

        /// <summary>
        /// 记录调试信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogDebug(string message);

        /// <summary>
        /// 记录普通信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogInformation(string message);

        /// <summary>
        /// 记录警告信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogWarning(string message);

        /// <summary>
        /// 记录错误信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogError(string message);

        /// <summary>
        /// 记录致命错误信息
        /// </summary>
        /// <param name="message">日志消息</param>
        void LogCritical(string message);
    }
}