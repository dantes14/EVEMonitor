using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 日志输出接口
    /// </summary>
    public interface ILogOutput
    {
        /// <summary>
        /// 写入日志
        /// </summary>
        /// <param name="logEntry">日志条目</param>
        void WriteLog(LogEntry logEntry);
    }
}