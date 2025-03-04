using System;
using System.Collections.Generic;
using System.IO;
using EVEMonitor.Core.Interfaces;

namespace EVEMonitor.Core.Services
{
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
        public Logger(string logFilePath = null, LogLevel minLogLevel = LogLevel.Information)
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
                
                string logDirectory = Path.GetDirectoryName(_logFilePath);
                if (!string.IsNullOrEmpty(logDirectory) && !Directory.Exists(logDirectory))
                {
                    Directory.CreateDirectory(logDirectory);
                }
            }
            
            // 添加默认的文件日志输出
            AddLogOutput(new FileLogOutput(_logFilePath));
            
            // 添加控制台日志输出（如果在控制台应用程序中）
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
        private void Log(LogLevel level, string message)
        {
            if (level < _minLogLevel)
            {
                return;
            }
            
            var logEntry = new LogEntry
            {
                Level = level,
                Message = message,
                Timestamp = DateTime.Now
            };
            
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
        public string Message { get; set; }
        
        /// <summary>
        /// 日志时间戳
        /// </summary>
        public DateTime Timestamp { get; set; }
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