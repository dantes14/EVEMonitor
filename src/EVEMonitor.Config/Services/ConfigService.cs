using System.IO;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Config.Services
{
    /// <summary>
    /// 配置管理服务实现
    /// </summary>
    public class ConfigService : IConfigService, IDisposable
    {
        private AppConfig _currentConfig;
        private FileSystemWatcher _fileWatcher;
        private readonly object _lockObject = new object();
        private bool _isWatching = false;

        /// <summary>
        /// 配置文件路径
        /// </summary>
        public string ConfigFilePath { get; set; }

        /// <summary>
        /// 当前配置
        /// </summary>
        public AppConfig CurrentConfig => _currentConfig;

        /// <summary>
        /// 配置变更事件
        /// </summary>
        public event EventHandler<ConfigChangedEventArgs> ConfigChanged;

        /// <summary>
        /// 初始化配置管理服务
        /// </summary>
        /// <param name="configFilePath">配置文件路径</param>
        public ConfigService(string configFilePath = "config.json")
        {
            ConfigFilePath = configFilePath;
            _currentConfig = LoadConfig();
        }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>加载的配置</returns>
        public AppConfig LoadConfig()
        {
            try
            {
                if (!File.Exists(ConfigFilePath))
                {
                    var defaultConfig = AppConfig.CreateDefault();
                    SaveConfig(defaultConfig);
                    return defaultConfig;
                }

                string json = File.ReadAllText(ConfigFilePath);
                var config = AppConfig.FromJson(json);
                return config;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"加载配置失败: {ex.Message}");
                return AppConfig.CreateDefault();
            }
        }

        /// <summary>
        /// 保存配置
        /// </summary>
        /// <param name="config">要保存的配置</param>
        /// <returns>保存是否成功</returns>
        public bool SaveConfig(AppConfig config)
        {
            if (config == null)
                return false;

            try
            {
                // 确保目录存在
                string directory = Path.GetDirectoryName(ConfigFilePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 暂停文件监视以避免触发自己的事件
                bool wasWatching = _isWatching;
                if (wasWatching)
                {
                    StopWatchingConfigChanges();
                }

                // 保存配置
                string json = config.ToJson();
                File.WriteAllText(ConfigFilePath, json);

                // 恢复文件监视
                if (wasWatching)
                {
                    WatchConfigChanges();
                }

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"保存配置失败: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 更新配置
        /// </summary>
        /// <param name="config">新的配置</param>
        public void UpdateConfig(AppConfig config)
        {
            if (config == null)
                return;

            lock (_lockObject)
            {
                _currentConfig = config;
                SaveConfig(config);
                OnConfigChanged(config);
            }
        }

        /// <summary>
        /// 监听配置文件变更
        /// </summary>
        public void WatchConfigChanges()
        {
            if (_isWatching)
                return;

            try
            {
                string directory = Path.GetDirectoryName(ConfigFilePath) ?? ".";
                string filename = Path.GetFileName(ConfigFilePath);

                _fileWatcher = new FileSystemWatcher(directory, filename)
                {
                    NotifyFilter = NotifyFilters.LastWrite,
                    EnableRaisingEvents = true
                };

                _fileWatcher.Changed += OnFileChanged;
                _isWatching = true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"启动配置监视失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 停止监听配置文件变更
        /// </summary>
        public void StopWatchingConfigChanges()
        {
            if (!_isWatching || _fileWatcher == null)
                return;

            try
            {
                _fileWatcher.Changed -= OnFileChanged;
                _fileWatcher.EnableRaisingEvents = false;
                _fileWatcher.Dispose();
                _fileWatcher = null;
                _isWatching = false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"停止配置监视失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 文件变更处理
        /// </summary>
        private void OnFileChanged(object sender, FileSystemEventArgs e)
        {
            // 由于FileSystemWatcher可能会多次触发，所以需要延迟处理并去重
            Task.Delay(500).ContinueWith(_ =>
            {
                try
                {
                    lock (_lockObject)
                    {
                        var newConfig = LoadConfig();
                        if (newConfig != null && !AreConfigsEqual(_currentConfig, newConfig))
                        {
                            _currentConfig = newConfig;
                            OnConfigChanged(newConfig);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"处理配置变更失败: {ex.Message}");
                }
            });
        }

        /// <summary>
        /// 触发配置变更事件
        /// </summary>
        /// <param name="config">新配置</param>
        private void OnConfigChanged(AppConfig config)
        {
            ConfigChanged?.Invoke(this, new ConfigChangedEventArgs(config));
        }

        /// <summary>
        /// 比较两个配置是否相同
        /// </summary>
        /// <param name="config1">配置1</param>
        /// <param name="config2">配置2</param>
        /// <returns>是否相同</returns>
        private bool AreConfigsEqual(AppConfig config1, AppConfig config2)
        {
            if (config1 == null || config2 == null)
                return config1 == config2;

            // 简单比较JSON
            return config1.ToJson() == config2.ToJson();
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            StopWatchingConfigChanges();
            GC.SuppressFinalize(this);
        }
    }
} 