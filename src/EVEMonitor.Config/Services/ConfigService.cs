using System;
using System.IO;
using System.Text.Json;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Config.Services
{
    /// <summary>
    /// 配置管理服务实现
    /// </summary>
    public class ConfigService : IConfigService, IDisposable
    {
        private string _configFilePath = string.Empty;
        private readonly JsonSerializerOptions _jsonOptions;
        private AppConfig _currentConfig = new();
        private FileSystemWatcher? _fileWatcher;
        private bool _disposed;

        /// <summary>
        /// 配置变更事件
        /// </summary>
        public event EventHandler<ConfigChangedEventArgs> ConfigChanged = delegate { };

        /// <summary>
        /// 当前配置
        /// </summary>
        public AppConfig CurrentConfig => _currentConfig;

        /// <summary>
        /// 配置文件路径
        /// </summary>
        public string ConfigFilePath
        {
            get => _configFilePath;
            set
            {
                if (string.IsNullOrEmpty(value))
                    throw new ArgumentNullException(nameof(value));

                if (_configFilePath != value)
                {
                    _configFilePath = value;
                    StopWatchingConfigChanges();
                    InitializeFileWatcher();
                    LoadConfig();
                }
            }
        }

        /// <summary>
        /// 初始化配置服务
        /// </summary>
        /// <param name="configFilePath">配置文件路径</param>
        public ConfigService(string configFilePath)
        {
            if (string.IsNullOrEmpty(configFilePath))
                throw new ArgumentNullException(nameof(configFilePath));

            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
                WriteIndented = true
            };

            ConfigFilePath = configFilePath;
        }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>配置对象</returns>
        public AppConfig LoadConfig()
        {
            _currentConfig = LoadConfigInternal() ?? new AppConfig();
            return _currentConfig;
        }

        /// <summary>
        /// 保存配置
        /// </summary>
        /// <param name="config">配置对象</param>
        /// <returns>保存是否成功</returns>
        public bool SaveConfig(AppConfig config)
        {
            if (config == null)
                return false;

            try
            {
                var json = JsonSerializer.Serialize(config, _jsonOptions);
                File.WriteAllText(_configFilePath, json);
                _currentConfig = config;
                OnConfigChanged();
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 更新配置
        /// </summary>
        /// <param name="config">配置对象</param>
        public void UpdateConfig(AppConfig config)
        {
            if (config == null)
                return;

            _currentConfig = config;
            SaveConfig(config);
            OnConfigChanged();
        }

        /// <summary>
        /// 开始监视配置变更
        /// </summary>
        public void WatchConfigChanges()
        {
            InitializeFileWatcher();
        }

        /// <summary>
        /// 停止监视配置变更
        /// </summary>
        public void StopWatchingConfigChanges()
        {
            if (_fileWatcher != null)
            {
                _fileWatcher.EnableRaisingEvents = false;
                _fileWatcher.Changed -= OnConfigFileChanged;
                _fileWatcher.Dispose();
                _fileWatcher = null;
            }
        }

        /// <summary>
        /// 触发配置变更事件
        /// </summary>
        protected virtual void OnConfigChanged()
        {
            ConfigChanged?.Invoke(this, new ConfigChangedEventArgs(_currentConfig));
        }

        /// <summary>
        /// 初始化文件监视器
        /// </summary>
        private void InitializeFileWatcher()
        {
            if (_fileWatcher != null)
            {
                _fileWatcher.Dispose();
            }

            var directory = Path.GetDirectoryName(_configFilePath);
            if (string.IsNullOrEmpty(directory))
                return;

            _fileWatcher = new FileSystemWatcher(directory)
            {
                Filter = Path.GetFileName(_configFilePath),
                NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size
            };

            _fileWatcher.Changed += OnConfigFileChanged;
            _fileWatcher.EnableRaisingEvents = true;
        }

        /// <summary>
        /// 配置文件变更处理
        /// </summary>
        private void OnConfigFileChanged(object sender, FileSystemEventArgs e)
        {
            var newConfig = LoadConfigInternal();
            if (newConfig != null && !AreConfigsEqual(_currentConfig, newConfig))
            {
                _currentConfig = newConfig;
                OnConfigChanged();
            }
        }

        /// <summary>
        /// 加载配置文件
        /// </summary>
        private AppConfig? LoadConfigInternal()
        {
            try
            {
                if (!File.Exists(_configFilePath))
                    return null;

                var json = File.ReadAllText(_configFilePath);
                return AppConfig.FromJson(json);
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// 比较两个配置对象是否相等
        /// </summary>
        private static bool AreConfigsEqual(AppConfig? config1, AppConfig? config2)
        {
            if (ReferenceEquals(config1, config2))
                return true;

            if (config1 == null || config2 == null)
                return false;

            return config1.ToJson() == config2.ToJson();
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            if (!_disposed)
            {
                StopWatchingConfigChanges();
                _disposed = true;
            }
            GC.SuppressFinalize(this);
        }
    }
}