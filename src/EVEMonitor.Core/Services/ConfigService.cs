using System;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 配置服务实现
    /// </summary>
    public class ConfigService : IConfigService
    {
        private readonly ILogger _logger;
        private FileSystemWatcher _configWatcher;
        private bool _isWatching = false;
        private readonly object _lockObject = new object();
        private AppConfig _currentConfig;
        private readonly JsonSerializerOptions _jsonOptions;
        private readonly SemaphoreSlim _fileAccessSemaphore = new SemaphoreSlim(1, 1);

        /// <summary>
        /// 配置文件路径
        /// </summary>
        public string ConfigFilePath { get; private set; }

        /// <summary>
        /// 当前配置
        /// </summary>
        public AppConfig CurrentConfig => _currentConfig;

        /// <summary>
        /// 配置变更事件
        /// </summary>
        public event EventHandler<ConfigChangedEventArgs> ConfigChanged;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="logger">日志服务</param>
        /// <param name="configFilePath">配置文件路径</param>
        public ConfigService(ILogger logger, string configFilePath = null)
        {
            _logger = logger;
            ConfigFilePath = configFilePath ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
            
            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };

            // 首次加载配置
            _currentConfig = LoadConfig();
        }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>应用配置</returns>
        public AppConfig LoadConfig()
        {
            try
            {
                _fileAccessSemaphore.Wait();

                try
                {
                    if (!File.Exists(ConfigFilePath))
                    {
                        _logger?.LogWarning($"配置文件不存在，创建默认配置：{ConfigFilePath}");
                        var defaultConfig = CreateDefaultConfig();
                        SaveConfigInternal(defaultConfig);
                        return defaultConfig;
                    }

                    string json = File.ReadAllText(ConfigFilePath);
                    var config = JsonSerializer.Deserialize<AppConfig>(json, _jsonOptions);

                    if (config == null)
                    {
                        _logger?.LogWarning("配置文件为空或格式无效，创建默认配置");
                        config = CreateDefaultConfig();
                        SaveConfigInternal(config);
                    }

                    _logger?.LogInformation("配置加载成功");
                    return config;
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
                    SaveConfigInternal(defaultConfig);
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
                OnConfigChanged(new ConfigChangedEventArgs(config));

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
            if (_isWatching)
            {
                return;
            }

            try
            {
                lock (_lockObject)
                {
                    if (_configWatcher != null)
                    {
                        _configWatcher.Dispose();
                    }

                    string directory = Path.GetDirectoryName(ConfigFilePath);
                    string fileName = Path.GetFileName(ConfigFilePath);

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

                    _logger?.LogInformation($"开始监控配置文件变化：{ConfigFilePath}");
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"监控配置文件异常：{ex.Message}");
                _isWatching = false;
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
        /// <param name="e">事件参数</param>
        protected virtual void OnConfigChanged(ConfigChangedEventArgs e)
        {
            ConfigChanged?.Invoke(this, e);
        }

        /// <summary>
        /// 配置文件变化事件处理
        /// </summary>
        private void ConfigFileChanged(object sender, FileSystemEventArgs e)
        {
            // 由于文件系统可能会触发多次事件，添加延迟处理
            Task.Delay(500).ContinueWith(_ =>
            {
                try
                {
                    // 重新加载配置
                    var newConfig = LoadConfig();
                    
                    lock (_lockObject)
                    {
                        // 更新当前配置
                        _currentConfig = newConfig;
                        
                        // 触发事件
                        OnConfigChanged(new ConfigChangedEventArgs(newConfig));
                    }
                    
                    _logger?.LogInformation("检测到配置文件变化，重新加载配置成功");
                }
                catch (Exception ex)
                {
                    _logger?.LogError($"处理配置文件变化异常：{ex.Message}");
                }
            });
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
                string directory = Path.GetDirectoryName(ConfigFilePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                string json = JsonSerializer.Serialize(config, _jsonOptions);
                File.WriteAllText(ConfigFilePath, json);
                
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
        /// <returns>默认应用配置</returns>
        private AppConfig CreateDefaultConfig()
        {
            return new AppConfig
            {
                ScreenshotInterval = 3000,
                SaveScreenshots = true,
                ScreenshotsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Screenshots"),
                DangerAlertThreshold = 5,
                EnableDingTalkAlerts = false,
                DingTalkWebhookUrl = "",
                DingTalkSecret = "",
                Emulators = new System.Collections.Generic.List<EmulatorConfig>
                {
                    new EmulatorConfig
                    {
                        Name = "EVE模拟器1",
                        Enabled = true,
                        WindowTitle = "EVE Online",
                        Index = 0,
                        CropArea = new System.Drawing.Rectangle(0, 0, 1920, 1080),
                        SystemNameROI = new System.Drawing.Rectangle(800, 10, 320, 30),
                        ShipTableROI = new System.Drawing.Rectangle(10, 100, 500, 600)
                    }
                }
            };
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            StopWatchingConfigChanges();
            _fileAccessSemaphore.Dispose();
        }
    }
} 