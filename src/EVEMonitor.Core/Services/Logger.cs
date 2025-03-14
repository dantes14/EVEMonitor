using System;
using System.Collections.Generic;
using System.IO;
using EVEMonitor.Core.Interfaces;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 日志级别
    /// </summary>
    public enum LogLevel
    {
        /// <summary>
        /// 跟踪
        /// </summary>
        Trace = 0,

        /// <summary>
        /// 调试
        /// </summary>
        Debug = 1,

        /// <summary>
        /// 信息
        /// </summary>
        Information = 2,

        /// <summary>
        /// 警告
        /// </summary>
        Warning = 3,

        /// <summary>
        /// 错误
        /// </summary>
        Error = 4,

        /// <summary>
        /// 严重错误
        /// </summary>
        Critical = 5
    }

    /// <summary>
    /// 日志服务实现
    /// </summary>
    public class Logger : ILogger
    {
        private readonly string _logFilePath;
        private readonly LogLevel _minLogLevel;
        private readonly object _lockObject = new object();
        private readonly List<ILogOutput> _logOutputs = new List<ILogOutput>();

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="logFilePath">日志文件路径</param>
        /// <param name="minLogLevel">最低日志级别</param>
        public Logger(string? logFilePath = null, LogLevel minLogLevel = LogLevel.Information)
        {
            _minLogLevel = minLogLevel;

            if (string.IsNullOrEmpty(logFilePath))
            {
                string logDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Logs");
                if (!Directory.Exists(logDirectory))
                {
                    Directory.CreateDirectory(logDirectory);
                }

                _logFilePath = Path.Combine(logDirectory, $"EVEMonitor_{DateTime.Now:yyyyMMdd}.log");
            }
            else
            {
                _logFilePath = logFilePath;

                string? logDirectory = Path.GetDirectoryName(_logFilePath);
                if (!string.IsNullOrEmpty(logDirectory) && !Directory.Exists(logDirectory))
                {
                    Directory.CreateDirectory(logDirectory);
                }
            }

            // 添加默认的文件日志输出
            AddLogOutput(new FileLogOutput(_logFilePath));

            // 如果是交互式环境，添加控制台日志输出
            if (Environment.UserInteractive)
            {
                AddLogOutput(new ConsoleLogOutput());
            }
        }

        /// <summary>
        /// 添加日志输出目标
        /// </summary>
        /// <param name="logOutput">日志输出接口</param>
        public void AddLogOutput(ILogOutput logOutput)
        {
            if (logOutput == null)
            {
                return;
            }

            lock (_lockObject)
            {
                _logOutputs.Add(logOutput);
            }
        }

        /// <summary>
        /// 移除日志输出目标
        /// </summary>
        /// <param name="logOutput">日志输出接口</param>
        public void RemoveLogOutput(ILogOutput logOutput)
        {
            if (logOutput == null)
            {
                return;
            }

            lock (_lockObject)
            {
                _logOutputs.Remove(logOutput);
            }
        }

        /// <summary>
        /// 记录跟踪日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogTrace(string message)
        {
            Log(LogLevel.Trace, message);
        }

        /// <summary>
        /// 记录调试日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogDebug(string message)
        {
            Log(LogLevel.Debug, message);
        }

        /// <summary>
        /// 记录信息日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogInformation(string message)
        {
            Log(LogLevel.Information, message);
        }

        /// <summary>
        /// 记录警告日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogWarning(string message)
        {
            Log(LogLevel.Warning, message);
        }

        /// <summary>
        /// 记录错误日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogError(string message)
        {
            Log(LogLevel.Error, message);
        }

        /// <summary>
        /// 记录严重错误日志
        /// </summary>
        /// <param name="message">日志消息</param>
        public void LogCritical(string message)
        {
            Log(LogLevel.Critical, message);
        }

        /// <summary>
        /// 记录日志
        /// </summary>
        /// <param name="level">日志级别</param>
        /// <param name="message">日志消息</param>
        /// <param name="ex">异常信息</param>
        public void Log(LogLevel level, string message, Exception? ex = null)
        {
            if (level < _minLogLevel)
                return;

            if (ex != null)
            {
                message = $"{message}\n异常: {ex.Message}\n堆栈: {ex.StackTrace}";
            }

            var logEntry = new LogEntry
            {
                Level = level,
                Message = message,
                Timestamp = DateTime.Now
            };

            // 通知所有日志输出
            OnLogAdded(logEntry);

            // 输出到文件
            if (!string.IsNullOrEmpty(_logFilePath))
            {
                try
                {
                    WriteToFile(logEntry);
                }
                catch (Exception fileEx)
                {
                    // 如果写入文件失败，输出到控制台
                    if (Environment.UserInteractive)
                    {
                        Console.ForegroundColor = ConsoleColor.Red;
                        Console.WriteLine($"写入日志文件失败: {fileEx.Message}");
                        Console.ResetColor();
                    }
                }
            }
        }

        /// <summary>
        /// 通知日志输出
        /// </summary>
        /// <param name="logEntry">日志条目</param>
        protected virtual void OnLogAdded(LogEntry logEntry)
        {
            lock (_lockObject)
            {
                foreach (var output in _logOutputs)
                {
                    try
                    {
                        output.WriteLog(logEntry);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"写入日志异常：{ex.Message}");
                    }
                }
            }
        }

        /// <summary>
        /// 写入日志到文件
        /// </summary>
        /// <param name="logEntry">日志条目</param>
        private void WriteToFile(LogEntry logEntry)
        {
            string logLine = $"{logEntry.Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{logEntry.Level}] {logEntry.Message}";
            File.AppendAllText(_logFilePath, logLine + Environment.NewLine);
        }
    }

    /// <summary>
    /// 文件日志输出实现
    /// </summary>
    public class FileLogOutput : ILogOutput
    {
        private readonly string _filePath;
        private readonly object _lockObject = new object();

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="filePath">日志文件路径</param>
        public FileLogOutput(string filePath)
        {
            _filePath = filePath;
        }

        /// <summary>
        /// 写入日志
        /// </summary>
        /// <param name="logEntry">日志条目</param>
        public void WriteLog(LogEntry logEntry)
        {
            try
            {
                string logLine = $"{logEntry.Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{logEntry.Level}] {logEntry.Message}";

                lock (_lockObject)
                {
                    File.AppendAllText(_filePath, logLine + Environment.NewLine);
                }
            }
            catch
            {
                // 忽略错误，避免在日志系统中抛出异常
            }
        }
    }

    /// <summary>
    /// 控制台日志输出实现
    /// </summary>
    public class ConsoleLogOutput : ILogOutput
    {
        private static readonly Dictionary<LogLevel, ConsoleColor> LogColors = new Dictionary<LogLevel, ConsoleColor>
        {
            { LogLevel.Trace, ConsoleColor.Gray },
            { LogLevel.Debug, ConsoleColor.Gray },
            { LogLevel.Information, ConsoleColor.White },
            { LogLevel.Warning, ConsoleColor.Yellow },
            { LogLevel.Error, ConsoleColor.Red },
            { LogLevel.Critical, ConsoleColor.DarkRed }
        };

        /// <summary>
        /// 写入日志
        /// </summary>
        /// <param name="logEntry">日志条目</param>
        public void WriteLog(LogEntry logEntry)
        {
            try
            {
                ConsoleColor originalColor = Console.ForegroundColor;
                Console.ForegroundColor = LogColors.ContainsKey(logEntry.Level) ? LogColors[logEntry.Level] : originalColor;

                Console.WriteLine($"{logEntry.Timestamp:HH:mm:ss.fff} [{logEntry.Level}] {logEntry.Message}");

                Console.ForegroundColor = originalColor;
            }
            catch
            {
                // 忽略错误，避免在日志系统中抛出异常
            }
        }
    }

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
        public required string Message { get; set; }

        /// <summary>
        /// 日志时间戳
        /// </summary>
        public DateTime Timestamp { get; set; }

        /// <summary>
        /// 初始化日志条目
        /// </summary>
        public LogEntry()
        {
            Timestamp = DateTime.Now;
        }
    }

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