using System.IO;
using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Serilog;
using EVEMonitor.Alert.Services;
using EVEMonitor.Capture.Services;
using EVEMonitor.Config.Services;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Services;
using EVEMonitor.ImageProcessing.Services;
using EVEMonitor.OCR.Services;

namespace EVEMonitor.UI
{
    /// <summary>
    /// App.xaml 的交互逻辑
    /// </summary>
    public partial class App : Application
    {
        private ServiceProvider _serviceProvider;

        /// <summary>
        /// 应用程序启动
        /// </summary>
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // 配置Serilog
            ConfigureLogging();

            // 配置服务
            ConfigureServices();

            // 显示主窗口
            var mainWindow = _serviceProvider.GetRequiredService<MainWindow>();
            mainWindow.Show();
        }

        /// <summary>
        /// 配置日志
        /// </summary>
        private void ConfigureLogging()
        {
            // 创建日志目录
            var logsDir = Path.Combine(Directory.GetCurrentDirectory(), "Logs");
            if (!Directory.Exists(logsDir))
            {
                Directory.CreateDirectory(logsDir);
            }

            // 配置Serilog
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Information()
                .WriteTo.File(Path.Combine(logsDir, "log-.txt"), 
                    rollingInterval: RollingInterval.Day,
                    retainedFileCountLimit: 7)
                .CreateLogger();

            // 注册未处理异常处理程序
            Current.DispatcherUnhandledException += (s, e) =>
            {
                Log.Error(e.Exception, "未处理的异常");
                MessageBox.Show($"发生未处理的异常: {e.Exception.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                e.Handled = true;
            };
        }

        /// <summary>
        /// 配置服务
        /// </summary>
        private void ConfigureServices()
        {
            var services = new ServiceCollection();

            // 注册配置服务
            services.AddSingleton<IConfigService>(provider => 
            {
                var configPath = Path.Combine(Directory.GetCurrentDirectory(), "config.json");
                return new ConfigService(configPath);
            });

            // 注册屏幕捕获服务
            services.AddSingleton<IScreenCaptureService>(provider =>
            {
                var configService = provider.GetRequiredService<IConfigService>();
                var config = configService.CurrentConfig;
                return new ScreenCaptureService(
                    new System.Drawing.Rectangle(0, 0, 1920, 1080), 
                    config.ScreenshotInterval);
            });

            // 注册图像处理服务
            services.AddSingleton<IImageProcessingService>(provider =>
            {
                var configService = provider.GetRequiredService<IConfigService>();
                return new ImageProcessingService(configService.CurrentConfig.Emulators);
            });

            // 注册OCR服务
            services.AddSingleton<IOcrService>(provider =>
            {
                var imageProcessingService = provider.GetRequiredService<IImageProcessingService>();
                var tessDataPath = Path.Combine(Directory.GetCurrentDirectory(), "tessdata");
                return new OcrService(tessDataPath, "eng+chi_sim", imageProcessingService as ImageProcessingService);
            });

            // 注册警报服务
            services.AddSingleton<IAlertService, DingTalkAlertService>();

            // 注册截图处理服务
            services.AddSingleton<IScreenshotService, ScreenshotService>();

            // 注册主窗口
            services.AddSingleton<MainWindow>();

            // 构建服务提供者
            _serviceProvider = services.BuildServiceProvider();
        }

        /// <summary>
        /// 应用程序退出
        /// </summary>
        protected override void OnExit(ExitEventArgs e)
        {
            base.OnExit(e);

            // 释放服务提供者
            _serviceProvider?.Dispose();

            // 关闭日志
            Log.CloseAndFlush();
        }
    }
} 