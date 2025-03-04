using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 配置变更事件参数
    /// </summary>
    public class ConfigChangedEventArgs : EventArgs
    {
        /// <summary>
        /// 配置
        /// </summary>
        public AppConfig Config { get; }

        /// <summary>
        /// 初始化配置变更事件参数
        /// </summary>
        /// <param name="config">配置</param>
        public ConfigChangedEventArgs(AppConfig config)
        {
            Config = config;
        }
    }

    /// <summary>
    /// 配置服务接口
    /// </summary>
    public interface IConfigService
    {
        /// <summary>
        /// 配置文件路径
        /// </summary>
        string ConfigFilePath { get; set; }

        /// <summary>
        /// 当前配置
        /// </summary>
        AppConfig CurrentConfig { get; }

        /// <summary>
        /// 加载配置
        /// </summary>
        /// <returns>加载的配置</returns>
        AppConfig LoadConfig();

        /// <summary>
        /// 保存配置
        /// </summary>
        /// <param name="config">要保存的配置</param>
        /// <returns>保存是否成功</returns>
        bool SaveConfig(AppConfig config);

        /// <summary>
        /// 更新配置
        /// </summary>
        /// <param name="config">新的配置</param>
        void UpdateConfig(AppConfig config);

        /// <summary>
        /// 监听配置文件变更
        /// </summary>
        void WatchConfigChanges();

        /// <summary>
        /// 停止监听配置文件变更
        /// </summary>
        void StopWatchingConfigChanges();

        /// <summary>
        /// 配置变更事件
        /// </summary>
        event EventHandler<ConfigChangedEventArgs> ConfigChanged;
    }
}