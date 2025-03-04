using System;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Forms;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using MessageBox = System.Windows.MessageBox;

namespace EVEMonitor.UI
{
    /// <summary>
    /// SettingsWindow.xaml 的交互逻辑
    /// </summary>
    public partial class SettingsWindow : Window
    {
        private readonly IConfigService _configService;
        private readonly IAlertService _alertService;
        private AppConfig _config;
        private string _dingTalkSecret;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="configService">配置服务</param>
        /// <param name="alertService">警报服务</param>
        public SettingsWindow(IConfigService configService, IAlertService alertService)
        {
            InitializeComponent();

            _configService = configService;
            _alertService = alertService;

            // 加载设置
            LoadSettings();
        }

        /// <summary>
        /// 加载设置
        /// </summary>
        private void LoadSettings()
        {
            try
            {
                // 克隆当前配置
                _config = (AppConfig)_configService.CurrentConfig.Clone();
                _dingTalkSecret = _config.DingTalkSecret;

                // 设置密码框的值
                txtDingTalkSecret.Password = _dingTalkSecret;

                // 设置DataContext
                DataContext = _config;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"加载设置失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                Close();
            }
        }

        /// <summary>
        /// 保存设置
        /// </summary>
        private void SaveSettings()
        {
            try
            {
                // 更新密钥
                _config.DingTalkSecret = _dingTalkSecret;

                // 保存配置
                if (_configService.SaveConfig(_config))
                {
                    // 更新当前配置
                    _configService.UpdateConfig(_config);
                    MessageBox.Show("设置已保存", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                    DialogResult = true;
                    Close();
                }
                else
                {
                    MessageBox.Show("保存设置失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"保存设置失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 添加模拟器
        /// </summary>
        private void AddEmulator()
        {
            try
            {
                int nextIndex = 0;
                foreach (var emulator in _config.Emulators)
                {
                    if (emulator.Index >= nextIndex)
                    {
                        nextIndex = emulator.Index + 1;
                    }
                }

                var newEmulator = new EmulatorConfig
                {
                    Name = $"EVE模拟器{nextIndex + 1}",
                    Enabled = true,
                    WindowTitle = "EVE Online",
                    Index = nextIndex,
                    CropArea = new System.Drawing.Rectangle(0, 0, 1920, 1080),
                    SystemNameROI = new System.Drawing.Rectangle(800, 10, 320, 30),
                    ShipTableROI = new System.Drawing.Rectangle(10, 100, 500, 600)
                };

                _config.Emulators.Add(newEmulator);
                
                // 刷新DataGrid
                dgEmulators.Items.Refresh();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"添加模拟器失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 删除选中模拟器
        /// </summary>
        private void RemoveSelectedEmulator()
        {
            try
            {
                var selectedEmulator = dgEmulators.SelectedItem as EmulatorConfig;
                if (selectedEmulator != null)
                {
                    if (MessageBox.Show($"确定要删除模拟器 \"{selectedEmulator.Name}\" 吗?", "确认", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
                    {
                        _config.Emulators.Remove(selectedEmulator);
                        
                        // 刷新DataGrid
                        dgEmulators.Items.Refresh();
                    }
                }
                else
                {
                    MessageBox.Show("请先选择要删除的模拟器", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"删除模拟器失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 设置模拟器区域
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        private void SetEmulatorRegions(int emulatorIndex)
        {
            try
            {
                var emulator = _config.Emulators.Find(e => e.Index == emulatorIndex);
                if (emulator != null)
                {
                    // TODO: 打开区域设置窗口
                    MessageBox.Show($"设置模拟器 \"{emulator.Name}\" 的区域功能暂未实现", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"设置模拟器区域失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 测试钉钉警报
        /// </summary>
        private async void TestDingTalkAlert()
        {
            try
            {
                if (string.IsNullOrEmpty(_config.DingTalkWebhookUrl))
                {
                    MessageBox.Show("请先填写钉钉Webhook URL", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                // 创建临时警报数据
                var alertData = new AlertData
                {
                    Title = "测试警报",
                    Message = "这是一条测试警报，如果您收到此消息，表示钉钉机器人配置正确。",
                    AlertType = AlertType.System,
                    Timestamp = DateTime.Now
                };

                // 临时保存配置以测试
                var tempConfig = _configService.CurrentConfig;
                _configService.UpdateConfig(_config);

                // 发送测试警报
                bool success = await _alertService.PushAlertAsync(alertData);

                // 恢复原来的配置
                _configService.UpdateConfig(tempConfig);

                if (success)
                {
                    MessageBox.Show("测试警报发送成功，请检查钉钉是否收到消息", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    MessageBox.Show("测试警报发送失败，请检查配置", "失败", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"测试钉钉警报失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 浏览文件夹按钮点击
        /// </summary>
        private void btnBrowse_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                using (var dialog = new FolderBrowserDialog())
                {
                    dialog.SelectedPath = _config.ScreenshotsPath;
                    dialog.Description = "选择截图保存路径";
                    
                    if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                    {
                        _config.ScreenshotsPath = dialog.SelectedPath;
                        txtScreenshotsPath.Text = dialog.SelectedPath;
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"选择文件夹失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 密码框内容变化
        /// </summary>
        private void txtDingTalkSecret_PasswordChanged(object sender, RoutedEventArgs e)
        {
            _dingTalkSecret = txtDingTalkSecret.Password;
        }

        /// <summary>
        /// 添加模拟器按钮点击
        /// </summary>
        private void btnAddEmulator_Click(object sender, RoutedEventArgs e)
        {
            AddEmulator();
        }

        /// <summary>
        /// 删除模拟器按钮点击
        /// </summary>
        private void btnRemoveEmulator_Click(object sender, RoutedEventArgs e)
        {
            RemoveSelectedEmulator();
        }

        /// <summary>
        /// 设置区域按钮点击
        /// </summary>
        private void btnSetRegions_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (sender is System.Windows.Controls.Button button && button.Tag is int emulatorIndex)
                {
                    SetEmulatorRegions(emulatorIndex);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"设置区域失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 测试钉钉警报按钮点击
        /// </summary>
        private void btnTestDingTalk_Click(object sender, RoutedEventArgs e)
        {
            TestDingTalkAlert();
        }

        /// <summary>
        /// 保存按钮点击
        /// </summary>
        private void btnSave_Click(object sender, RoutedEventArgs e)
        {
            SaveSettings();
        }

        /// <summary>
        /// 取消按钮点击
        /// </summary>
        private void btnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
} 