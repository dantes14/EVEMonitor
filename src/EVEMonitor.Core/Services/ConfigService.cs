using System;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using System.Drawing;
using System.Text.Json.Serialization;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 配置服务实现
    /// </summary>
    public class ConfigService : IConfigService, IDisposable
    {
        private readonly ILogger<ConfigService>? _logger;
        private readonly JsonSerializerOptions _jsonOptions;
        private string _configFilePath = string.Empty;
        private AppConfig _currentConfig = null!;
        private FileSystemWatcher? _configWatcher;
        private bool _isWatching;
        private bool _disposed;
        private readonly object _lockObject = new();
        private readonly SemaphoreSlim _fileAccessSemaphore = new SemaphoreSlim(1, 1);

        /// <summary>
        /// 配置文件路径
        /// </summary>
        public string ConfigFilePath
        {
            get => _configFilePath;
            set
            {
                if (string.IsNullOrEmpty(value))
                    throw new ArgumentException("配置文件路径不能为空", nameof(value));

                if (_configFilePath != value)
                {
                    _configFilePath = value;
                    _currentConfig = LoadConfig(_configFilePath);

                    // 重新初始化文件监视器
                    if (_isWatching)
                    {
                        StopWatchingConfigChanges();
                        WatchConfigChanges();
                    }
                }
            }
        }

        /// <summary>
        /// 当前配置
        /// </summary>
        public AppConfig CurrentConfig
        {
            get => _currentConfig;
            private set
            {
                if (_currentConfig != value)
                {
                    _currentConfig = value;
                    OnConfigChanged(value);
                }
            }
        }

        /// <summary>
        /// 配置变更事件
        /// </summary>
        public event EventHandler<ConfigChangedEventArgs> ConfigChanged = null!;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="logger">日志记录器</param>
        /// <param name="configFilePath">配置文件路径</param>
        public ConfigService(ILogger<ConfigService>? logger = null, string? configFilePath = null)
        {
            _logger = logger;
            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNameCaseInsensitive = true,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
            };

            ConfigFilePath = configFilePath ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
            _currentConfig = LoadConfig(_configFilePath);
        }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>应用配置</returns>
        public AppConfig LoadConfig()
        {
            return LoadConfig(_configFilePath);
        }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>应用配置</returns>
        public AppConfig LoadConfig(string filePath)
        {
            try
            {
                _fileAccessSemaphore.Wait();

                try
                {
                    return LoadConfigFromFile(filePath);
                }
                finally
                {
                    _fileAccessSemaphore.Release();
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"加载配置异常：{ex.Message}");

                if (_fileAccessSemaphore.CurrentCount == 0)
                {
                    _fileAccessSemaphore.Release();
                }

                var defaultConfig = CreateDefaultConfig();
                try
                {
                    SaveConfig(defaultConfig);
                }
                catch
                {
                    // 忽略这里的错误，避免死循环
                }

                return defaultConfig;
            }
        }

        /// <summary>
        /// 保存配置
        /// </summary>
        /// <param name="config">应用配置</param>
        /// <returns>是否保存成功</returns>
        public bool SaveConfig(AppConfig config)
        {
            if (config == null)
            {
                _logger?.LogWarning("保存的配置为空");
                return false;
            }

            try
            {
                _fileAccessSemaphore.Wait();

                try
                {
                    return SaveConfigInternal(config);
                }
                finally
                {
                    _fileAccessSemaphore.Release();
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"保存配置异常：{ex.Message}");

                if (_fileAccessSemaphore.CurrentCount == 0)
                {
                    _fileAccessSemaphore.Release();
                }

                return false;
            }
        }

        /// <summary>
        /// 更新配置
        /// </summary>
        /// <param name="config">新配置</param>
        public void UpdateConfig(AppConfig config)
        {
            if (config == null)
            {
                _logger?.LogWarning("更新的配置为空");
                return;
            }

            lock (_lockObject)
            {
                // 停止监控
                bool wasWatching = _isWatching;
                StopWatchingConfigChanges();

                // 更新当前配置并保存
                _currentConfig = config;
                SaveConfig(config);

                // 触发事件
                OnConfigChanged(config);

                // 如果之前在监控，则恢复监控
                if (wasWatching)
                {
                    WatchConfigChanges();
                }
            }
        }

        /// <summary>
        /// 监控配置文件变化
        /// </summary>
        public void WatchConfigChanges()
        {
            if (!_isWatching)
            {
                try
                {
                    if (_configWatcher != null)
                    {
                        _configWatcher.Dispose();
                    }

                    string? directory = Path.GetDirectoryName(_configFilePath);
                    string fileName = Path.GetFileName(_configFilePath);

                    if (string.IsNullOrEmpty(directory))
                    {
                        directory = AppDomain.CurrentDomain.BaseDirectory;
                    }

                    if (!Directory.Exists(directory))
                    {
                        Directory.CreateDirectory(directory);
                    }

                    _configWatcher = new FileSystemWatcher(directory, fileName)
                    {
                        NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size | NotifyFilters.CreationTime
                    };

                    _configWatcher.Changed += ConfigFileChanged;
                    _configWatcher.EnableRaisingEvents = true;
                    _isWatching = true;

                    _logger?.LogInformation($"开始监控配置文件变化：{_configFilePath}");
                }
                catch (Exception ex)
                {
                    _logger?.LogError($"监控配置文件异常：{ex.Message}");
                    _isWatching = false;
                }
            }
        }

        /// <summary>
        /// 停止监控配置文件变化
        /// </summary>
        public void StopWatchingConfigChanges()
        {
            if (!_isWatching)
            {
                return;
            }

            try
            {
                lock (_lockObject)
                {
                    if (_configWatcher != null)
                    {
                        _configWatcher.Changed -= ConfigFileChanged;
                        _configWatcher.EnableRaisingEvents = false;
                        _configWatcher.Dispose();
                        _configWatcher = null;
                    }

                    _isWatching = false;
                    _logger?.LogInformation("停止监控配置文件变化");
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"停止监控配置文件异常：{ex.Message}");
            }
        }

        /// <summary>
        /// 触发配置变更事件
        /// </summary>
        protected virtual void OnConfigChanged(AppConfig config)
        {
            ConfigChanged?.Invoke(this, new ConfigChangedEventArgs(config));
        }

        /// <summary>
        /// 配置文件变化事件处理
        /// </summary>
        private void ConfigFileChanged(object sender, FileSystemEventArgs e)
        {
            if (e.ChangeType == WatcherChangeTypes.Changed)
            {
                // 由于文件系统可能触发多次Changed事件，这里添加延迟
                Thread.Sleep(100);

                try
                {
                    ReloadConfig();
                }
                catch (Exception ex)
                {
                    _logger?.LogError($"处理配置文件变更失败: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// 重新加载配置
        /// </summary>
        /// <returns>是否成功</returns>
        public bool ReloadConfig()
        {
            try
            {
                lock (_lockObject)
                {
                    CurrentConfig = LoadConfig(_configFilePath);
                    return true;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"重新加载配置失败: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 内部保存配置方法
        /// </summary>
        /// <param name="config">应用配置</param>
        /// <returns>是否保存成功</returns>
        private bool SaveConfigInternal(AppConfig config)
        {
            try
            {
                string? directory = Path.GetDirectoryName(_configFilePath);
                if (directory is not null && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                string json = JsonSerializer.Serialize(config, _jsonOptions);
                File.WriteAllText(_configFilePath, json);

                _currentConfig = config;
                _logger?.LogInformation("配置保存成功");

                return true;
            }
            catch (Exception ex)
            {
                _logger?.LogError($"保存配置内部异常：{ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 创建默认配置
        /// </summary>
        private static AppConfig CreateDefaultConfig()
        {
            var config = new AppConfig
            {
                ScreenshotInterval = 1000,
                SaveScreenshots = false,
                SaveDangerousScreenshotsOnly = true,
                ScreenshotSavePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Screenshots"),
                DangerThreshold = 1,
                Performance = new PerformanceConfig
                {
                    MaxThreads = Environment.ProcessorCount,
                    PerformanceAlertThresholdMs = 5000
                },
                Emulators = new List<InternalEmulatorConfig>()
            };

            // 添加默认模拟器
            config.Emulators.Add(new InternalEmulatorConfig
            {
                Name = "模拟器 1",
                Enabled = true,
                WindowTitle = "EVE Online",
                Index = 0,
                CaptureRegion = new Rectangle(0, 0, 1280, 720),
                SystemNameROI = new Rectangle(10, 10, 200, 30),
                ShipTableROI = new Rectangle(10, 50, 1260, 660)
            });

            return config;
        }

        /// <summary>
        /// 从配置文件加载配置
        /// </summary>
        /// <returns>加载的配置</returns>
        private AppConfig LoadConfigFromFile(string filePath)
        {
            try
            {
                if (!File.Exists(filePath))
                {
                    _logger?.LogWarning($"配置文件不存在: {filePath}，将创建默认配置");
                    var defaultConfig = CreateDefaultConfig();
                    SaveConfig(defaultConfig);
                    return defaultConfig;
                }

                string json = File.ReadAllText(filePath);
                if (string.IsNullOrWhiteSpace(json))
                {
                    _logger?.LogWarning("配置文件为空，将创建默认配置");
                    var defaultConfig = CreateDefaultConfig();
                    SaveConfig(defaultConfig);
                    return defaultConfig;
                }

                var config = JsonSerializer.Deserialize<AppConfig>(json, _jsonOptions);
                if (config == null)
                {
                    _logger?.LogWarning("配置文件反序列化失败，将创建默认配置");
                    return CreateDefaultConfig();
                }

                return config;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, $"加载配置文件失败: {ex.Message}");
                return CreateDefaultConfig();
            }
        }

        /// <summary>
        /// 从JSON字符串反序列化配置
        /// </summary>
        /// <param name="json">JSON字符串</param>
        /// <returns>应用配置</returns>
        public static AppConfig FromJson(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                return new AppConfig();
            }

            try
            {
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                var config = JsonSerializer.Deserialize<AppConfig>(json, options);
                return config ?? new AppConfig();
            }
            catch
            {
                return new AppConfig();
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
        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    StopWatchingConfigChanges();
                    _fileAccessSemaphore.Dispose();
                }
                _disposed = true;
            }
        }
    }
}