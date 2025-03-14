using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Drawing;
using System.Linq;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 应用程序配置类，用于存储和管理应用程序配置
    /// </summary>
    public class AppConfig
    {
        /// <summary>
        /// 应用程序名称
        /// </summary>
        public string AppName { get; set; } = "EVE Monitor";

        /// <summary>
        /// 应用程序版本
        /// </summary>
        public string Version { get; set; } = "1.0.0";

        /// <summary>
        /// 是否启用调试模式
        /// </summary>
        public bool DebugMode { get; set; } = false;

        /// <summary>
        /// 截图间隔（毫秒）
        /// </summary>
        public int ScreenshotInterval { get; set; } = 1000;

        /// <summary>
        /// 是否自动开始监控
        /// </summary>
        public bool AutoStartMonitoring { get; set; } = false;

        /// <summary>
        /// 是否最小化到托盘
        /// </summary>
        public bool MinimizeToTray { get; set; } = true;

        /// <summary>
        /// 是否启动时最小化
        /// </summary>
        public bool StartMinimized { get; set; } = false;

        /// <summary>
        /// 是否启用声音警报
        /// </summary>
        public bool EnableSoundAlert { get; set; } = true;

        /// <summary>
        /// 是否启用钉钉警报
        /// </summary>
        public bool EnableDingTalkAlert { get; set; } = false;

        /// <summary>
        /// 是否启用钉钉警报（别名，与EnableDingTalkAlert保持一致）
        /// </summary>
        public bool EnableDingTalkAlerts
        {
            get => EnableDingTalkAlert;
            set => EnableDingTalkAlert = value;
        }

        /// <summary>
        /// 钉钉Webhook地址
        /// </summary>
        public string DingTalkWebhookUrl { get; set; } = "";

        /// <summary>
        /// 钉钉加签密钥
        /// </summary>
        public string DingTalkSecret { get; set; } = "";

        /// <summary>
        /// 是否保存截图
        /// </summary>
        public bool SaveScreenshots { get; set; } = false;

        /// <summary>
        /// 截图保存路径
        /// </summary>
        public string ScreenshotSavePath { get; set; } = "Screenshots";

        /// <summary>
        /// 截图保存路径（别名，与ScreenshotSavePath保持一致）
        /// </summary>
        public string ScreenshotsPath
        {
            get => ScreenshotSavePath;
            set => ScreenshotSavePath = value;
        }

        /// <summary>
        /// 是否仅保存危险截图
        /// </summary>
        public bool SaveDangerousScreenshotsOnly { get; set; } = true;

        /// <summary>
        /// 危险阈值
        /// </summary>
        public int DangerThreshold { get; set; } = 3;

        /// <summary>
        /// 危险警报阈值（别名，与DangerThreshold保持一致）
        /// </summary>
        public int DangerAlertThreshold
        {
            get => DangerThreshold;
            set => DangerThreshold = value;
        }

        /// <summary>
        /// 模拟器配置列表
        /// </summary>
        public List<InternalEmulatorConfig> Emulators { get; set; } = new();

        /// <summary>
        /// 危险舰船类型列表
        /// </summary>
        public List<string> DangerousShipTypes { get; set; } = new List<string>
        {
            "Battleship", "Carrier", "Dreadnought", "Titan", "Supercarrier",
            "战列舰", "航母", "无畏舰", "泰坦", "超级航母"
        };

        /// <summary>
        /// 危险公司列表
        /// </summary>
        public List<string> DangerousCorporations { get; set; } = new List<string>
        {
            "CODE.", "Goonswarm", "Pandemic Legion",
            "代码联盟", "蜂群", "流行军团"
        };

        /// <summary>
        /// 友好公司列表
        /// </summary>
        public List<string> FriendlyCorporations { get; set; } = new List<string>
        {
            "Our Corp", "Friendly Alliance",
            "我方公司", "友好联盟"
        };

        /// <summary>
        /// 日志配置
        /// </summary>
        public LoggingConfig Logging { get; set; } = new LoggingConfig();

        /// <summary>
        /// 性能配置
        /// </summary>
        public PerformanceConfig Performance { get; set; } = new PerformanceConfig();

        /// <summary>
        /// UI配置
        /// </summary>
        public UIConfig UI { get; set; } = new UIConfig();

        /// <summary>
        /// 钉钉机器人配置
        /// </summary>
        public DingTalkConfig DingTalk { get; set; } = new();

        /// <summary>
        /// 将配置序列化为JSON字符串
        /// </summary>
        /// <returns>JSON字符串</returns>
        public string ToJson()
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
            };
            return JsonSerializer.Serialize(this, options);
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
                return JsonSerializer.Deserialize<AppConfig>(json, options) ?? new AppConfig();
            }
            catch
            {
                return new AppConfig();
            }
        }

        /// <summary>
        /// 创建默认配置
        /// </summary>
        /// <returns>默认配置</returns>
        public static AppConfig CreateDefault()
        {
            var config = new AppConfig();

            // 添加默认模拟器
            config.Emulators.Add(new InternalEmulatorConfig
            {
                Name = "模拟器 1",
                Enabled = true
            });

            // 添加默认危险舰船类型
            config.DangerousShipTypes.AddRange(new[]
            {
                "Battleship",
                "Carrier",
                "Dreadnought",
                "Titan",
                "Supercarrier"
            });

            return config;
        }

        /// <summary>
        /// 复制模拟器配置
        /// </summary>
        /// <param name="other">其他配置</param>
        public void CopyEmulators(AppConfig other)
        {
            if (other == null)
                return;

            foreach (var emulator in other.Emulators)
            {
                var existingEmulator = Emulators.FirstOrDefault(e => e.Name == emulator.Name);
                if (existingEmulator != null)
                {
                    existingEmulator.Enabled = emulator.Enabled;
                    existingEmulator.WindowTitle = emulator.WindowTitle;
                    existingEmulator.Index = emulator.Index;
                    existingEmulator.CaptureRegion = emulator.CaptureRegion;
                    existingEmulator.SystemNameROI = emulator.SystemNameROI;
                    existingEmulator.ShipTableROI = emulator.ShipTableROI;
                }
                else
                {
                    Emulators.Add(new InternalEmulatorConfig
                    {
                        Enabled = emulator.Enabled,
                        WindowTitle = emulator.WindowTitle,
                        Index = emulator.Index,
                        Name = emulator.Name,
                        CaptureRegion = emulator.CaptureRegion,
                        SystemNameROI = emulator.SystemNameROI,
                        ShipTableROI = emulator.ShipTableROI
                    });
                }
            }
        }
    }

    /// <summary>
    /// 日志配置
    /// </summary>
    public class LoggingConfig
    {
        /// <summary>
        /// 日志级别
        /// </summary>
        public string LogLevel { get; set; } = "Information";

        /// <summary>
        /// 是否记录到文件
        /// </summary>
        public bool LogToFile { get; set; } = true;

        /// <summary>
        /// 日志文件路径
        /// </summary>
        public string LogFilePath { get; set; } = "Logs";

        /// <summary>
        /// 最大日志文件大小（MB）
        /// </summary>
        public int MaxLogFileSizeMB { get; set; } = 10;

        /// <summary>
        /// 最大日志文件数量
        /// </summary>
        public int MaxLogFileCount { get; set; } = 5;
    }

    /// <summary>
    /// 性能配置
    /// </summary>
    public class PerformanceConfig
    {
        /// <summary>
        /// 最大线程数
        /// </summary>
        public int MaxThreads { get; set; } = 4;

        /// <summary>
        /// 性能警报阈值（毫秒）
        /// </summary>
        public int PerformanceAlertThresholdMs { get; set; } = 500;

        /// <summary>
        /// 是否启用性能监控
        /// </summary>
        public bool EnablePerformanceMonitoring { get; set; } = true;

        /// <summary>
        /// 内存警告阈值（MB）
        /// </summary>
        public int MemoryWarningThresholdMB { get; set; } = 500;
    }

    /// <summary>
    /// UI配置
    /// </summary>
    public class UIConfig
    {
        /// <summary>
        /// 主题
        /// </summary>
        public string Theme { get; set; } = "Dark";

        /// <summary>
        /// 主色调
        /// </summary>
        public string PrimaryColor { get; set; } = "#1E90FF";

        /// <summary>
        /// 字体大小
        /// </summary>
        public int FontSize { get; set; } = 12;

        /// <summary>
        /// 是否显示网格线
        /// </summary>
        public bool ShowGridLines { get; set; } = true;

        /// <summary>
        /// 是否显示工具提示
        /// </summary>
        public bool ShowTooltips { get; set; } = true;
    }
}