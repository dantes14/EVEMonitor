using System.Drawing;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 应用配置
    /// </summary>
    public class AppConfig
    {
        /// <summary>
        /// 应用名称
        /// </summary>
        public string AppName { get; set; } = "EVE Monitor";

        /// <summary>
        /// 应用版本
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
        /// 是否自动启动监控
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
        /// 是否启用声音提醒
        /// </summary>
        public bool EnableSoundAlert { get; set; } = true;

        /// <summary>
        /// 是否启用钉钉推送
        /// </summary>
        public bool EnableDingTalkAlert { get; set; } = false;

        /// <summary>
        /// 钉钉Webhook地址
        /// </summary>
        public string DingTalkWebhookUrl { get; set; } = "";

        /// <summary>
        /// 钉钉安全密钥
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
        /// 是否仅保存危险截图
        /// </summary>
        public bool SaveDangerousScreenshotsOnly { get; set; } = true;

        /// <summary>
        /// 危险等级阈值（0-10）
        /// </summary>
        public int DangerThreshold { get; set; } = 3;

        /// <summary>
        /// 模拟器配置列表
        /// </summary>
        public List<EmulatorConfig> Emulators { get; set; } = new List<EmulatorConfig>();

        /// <summary>
        /// 危险舰船类型列表
        /// </summary>
        public List<string> DangerousShipTypes { get; set; } = new List<string>();

        /// <summary>
        /// 危险军团列表
        /// </summary>
        public List<string> DangerousCorporations { get; set; } = new List<string>();

        /// <summary>
        /// 友好军团列表
        /// </summary>
        public List<string> FriendlyCorporations { get; set; } = new List<string>();

        /// <summary>
        /// 日志设置
        /// </summary>
        public LoggingConfig Logging { get; set; } = new LoggingConfig();

        /// <summary>
        /// 性能设置
        /// </summary>
        public PerformanceConfig Performance { get; set; } = new PerformanceConfig();

        /// <summary>
        /// 界面设置
        /// </summary>
        public UIConfig UI { get; set; } = new UIConfig();

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
            config.Emulators.Add(new EmulatorConfig
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
    }

    /// <summary>
    /// 模拟器配置
    /// </summary>
    public class EmulatorConfig
    {
        /// <summary>
        /// 模拟器名称
        /// </summary>
        public string Name { get; set; } = "";

        /// <summary>
        /// 是否启用
        /// </summary>
        public bool Enabled { get; set; } = true;

        /// <summary>
        /// 窗口标题（用于查找窗口）
        /// </summary>
        public string WindowTitle { get; set; } = "";

        /// <summary>
        /// 窗口句柄
        /// </summary>
        [JsonIgnore]
        public IntPtr WindowHandle { get; set; } = IntPtr.Zero;

        /// <summary>
        /// 截图区域
        /// </summary>
        public CaptureRegion CaptureRegion { get; set; } = new CaptureRegion();
    }

    /// <summary>
    /// 截图区域
    /// </summary>
    public class CaptureRegion
    {
        /// <summary>
        /// X坐标
        /// </summary>
        public int X { get; set; } = 0;

        /// <summary>
        /// Y坐标
        /// </summary>
        public int Y { get; set; } = 0;

        /// <summary>
        /// 宽度
        /// </summary>
        public int Width { get; set; } = 1280;

        /// <summary>
        /// 高度
        /// </summary>
        public int Height { get; set; } = 720;

        /// <summary>
        /// 是否使用相对坐标
        /// </summary>
        public bool UseRelativeCoordinates { get; set; } = true;
    }

    /// <summary>
    /// 日志设置
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
        /// 日志文件最大大小（MB）
        /// </summary>
        public int MaxLogFileSizeMB { get; set; } = 10;

        /// <summary>
        /// 保留的日志文件数量
        /// </summary>
        public int MaxLogFileCount { get; set; } = 5;
    }

    /// <summary>
    /// 性能设置
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
        /// 内存使用警告阈值（MB）
        /// </summary>
        public int MemoryWarningThresholdMB { get; set; } = 500;
    }

    /// <summary>
    /// 界面设置
    /// </summary>
    public class UIConfig
    {
        /// <summary>
        /// 主题（Light/Dark）
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