using EVEMonitor.Core.Services;
using System;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 日志条目
    /// </summary>
    public class LogEntry
    {
        /// <summary>
        /// 日志级别
        /// </summary>
        public LogLevel Level { get; set; }

        /// <summary>
        /// 日志消息
        /// </summary>
        public string Message { get; set; } = string.Empty;

        /// <summary>
        /// 日志时间戳
        /// </summary>
        public DateTime Timestamp { get; set; }
    }
}