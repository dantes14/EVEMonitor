using System;
using System.Collections.ObjectModel;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using MaterialDesignThemes.Wpf;

namespace EVEMonitor.UI
{
    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window
    {
        private readonly IConfigService _configService;
        private readonly IScreenshotService _screenshotService;
        private readonly IAlertService _alertService;

        // 警报列表
        public ObservableCollection<AlertViewModel> AlertsList { get; } = new ObservableCollection<AlertViewModel>();

        /// <summary>
        /// 主窗口构造函数
        /// </summary>
        /// <param name="configService">配置服务</param>
        /// <param name="screenshotService">截图服务</param>
        /// <param name="alertService">警报服务</param>
        public MainWindow(IConfigService configService, IScreenshotService screenshotService, IAlertService alertService)
        {
            InitializeComponent();

            _configService = configService;
            _screenshotService = screenshotService;
            _alertService = alertService;

            // 设置DataContext
            DataContext = this;

            // 订阅事件
            _screenshotService.ScreenshotAnalysisCompleted += ScreenshotService_ScreenshotAnalysisCompleted;
            _configService.ConfigChanged += ConfigService_ConfigChanged;

            // 初始化UI
            InitializeUI();
        }

        /// <summary>
        /// 初始化UI
        /// </summary>
        private void InitializeUI()
        {
            try
            {
                // 更新状态
                UpdateStatus();

                // 更新设置信息
                UpdateSettingsInfo();

                // 禁用停止按钮
                btnStop.IsEnabled = false;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"初始化UI失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 更新状态显示
        /// </summary>
        private void UpdateStatus()
        {
            if (_screenshotService.IsRunning)
            {
                iconStatus.Foreground = new SolidColorBrush(Colors.Green);
                txtStatus.Text = "监控中";
                btnStart.IsEnabled = false;
                btnStop.IsEnabled = true;
            }
            else
            {
                iconStatus.Foreground = new SolidColorBrush(Colors.Gray);
                txtStatus.Text = "就绪";
                btnStart.IsEnabled = true;
                btnStop.IsEnabled = false;
            }
        }

        /// <summary>
        /// 更新设置信息
        /// </summary>
        private void UpdateSettingsInfo()
        {
            var config = _configService.CurrentConfig;
            var enabledEmulators = config.Emulators.Count(e => e.Enabled);
            txtEmulatorCount.Text = $"模拟器: {enabledEmulators}";
            txtInterval.Text = $"间隔: {config.ScreenshotInterval}ms";
        }

        /// <summary>
        /// 开始监控按钮点击
        /// </summary>
        private async void btnStart_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 开始监控
                bool success = await _screenshotService.StartAsync(_configService.CurrentConfig.ScreenshotInterval);
                if (success)
                {
                    UpdateStatus();
                    AddAlert(new AlertViewModel
                    {
                        Title = "监控已启动",
                        Content = "屏幕监控服务已成功启动",
                        TimeInfo = DateTime.Now.ToString("HH:mm:ss")
                    });
                }
                else
                {
                    MessageBox.Show("启动监控失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"启动监控时发生错误: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 停止监控按钮点击
        /// </summary>
        private async void btnStop_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 停止监控
                bool success = await _screenshotService.StopAsync();
                if (success)
                {
                    UpdateStatus();
                    AddAlert(new AlertViewModel
                    {
                        Title = "监控已停止",
                        Content = "屏幕监控服务已停止",
                        TimeInfo = DateTime.Now.ToString("HH:mm:ss")
                    });
                }
                else
                {
                    MessageBox.Show("停止监控失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"停止监控时发生错误: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 设置按钮点击
        /// </summary>
        private void btnSettings_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var settingsWindow = new SettingsWindow(_configService, _alertService);
                settingsWindow.Owner = this;

                // 显示设置窗口
                bool? result = settingsWindow.ShowDialog();
                if (result == true)
                {
                    // 设置已保存，更新UI
                    UpdateSettingsInfo();
                    
                    AddAlert(new AlertViewModel
                    {
                        Title = "设置已更新",
                        Content = "应用程序设置已更新",
                        TimeInfo = DateTime.Now.ToString("HH:mm:ss")
                    });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开设置窗口时发生错误: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 配置变更事件处理
        /// </summary>
        private void ConfigService_ConfigChanged(object sender, ConfigChangedEventArgs e)
        {
            // 在UI线程上更新设置
            Dispatcher.Invoke(() =>
            {
                try
                {
                    UpdateSettingsInfo();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"处理配置变更事件时发生错误: {ex.Message}");
                }
            });
        }

        /// <summary>
        /// 截图分析完成事件处理
        /// </summary>
        private void ScreenshotService_ScreenshotAnalysisCompleted(object sender, ScreenshotAnalysisEventArgs e)
        {
            // 在UI线程上更新界面
            Dispatcher.Invoke(() =>
            {
                try
                {
                    // 更新截图显示
                    UpdateScreenshot(e.Result.ProcessedScreenshot);

                    // 如果检测到危险，添加警报
                    if (e.Result.DangerDetected)
                    {
                        var dangerLevel = e.Result.DangerLevel;
                        string levelText = dangerLevel <= 3 ? "低" : (dangerLevel <= 7 ? "中" : "高");

                        AddAlert(new AlertViewModel
                        {
                            Title = $"危险舰船警报 ({levelText}危险)",
                            Content = $"在星系 {e.Result.SystemName ?? "未知"} 中检测到 {e.Result.DetectedShips.Count} 艘舰船，其中 {e.Result.DetectedShips.Count(s => s.IsDangerous)} 艘危险舰船",
                            TimeInfo = DateTime.Now.ToString("HH:mm:ss")
                        });
                    }
                }
                catch (Exception ex)
                {
                    // 仅记录错误，不中断程序
                    Console.WriteLine($"处理截图分析结果时发生错误: {ex.Message}");
                }
            });
        }

        /// <summary>
        /// 更新截图显示
        /// </summary>
        /// <param name="bitmap">截图</param>
        private void UpdateScreenshot(Bitmap bitmap)
        {
            if (bitmap == null)
                return;

            try
            {
                using (MemoryStream memory = new MemoryStream())
                {
                    bitmap.Save(memory, System.Drawing.Imaging.ImageFormat.Bmp);
                    memory.Position = 0;

                    BitmapImage bitmapImage = new BitmapImage();
                    bitmapImage.BeginInit();
                    bitmapImage.StreamSource = memory;
                    bitmapImage.CacheOption = BitmapCacheOption.OnLoad;
                    bitmapImage.EndInit();

                    imgScreenshot.Source = bitmapImage;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"更新截图显示时发生错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 添加警报
        /// </summary>
        /// <param name="alert">警报视图模型</param>
        private void AddAlert(AlertViewModel alert)
        {
            if (alert == null)
                return;

            try
            {
                // 限制警报数量，保持最近的100条
                while (AlertsList.Count >= 100)
                {
                    AlertsList.RemoveAt(AlertsList.Count - 1);
                }

                // 在开头添加新警报
                AlertsList.Insert(0, alert);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"添加警报时发生错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 窗口关闭时的处理
        /// </summary>
        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);

            // 停止服务
            _screenshotService.StopAsync().Wait();

            // 取消订阅事件
            _screenshotService.ScreenshotAnalysisCompleted -= ScreenshotService_ScreenshotAnalysisCompleted;
            _configService.ConfigChanged -= ConfigService_ConfigChanged;
        }
    }

    /// <summary>
    /// 警报视图模型
    /// </summary>
    public class AlertViewModel
    {
        /// <summary>
        /// 警报标题
        /// </summary>
        public string Title { get; set; }

        /// <summary>
        /// 警报内容
        /// </summary>
        public string Content { get; set; }

        /// <summary>
        /// 时间信息
        /// </summary>
        public string TimeInfo { get; set; }
    }
} 