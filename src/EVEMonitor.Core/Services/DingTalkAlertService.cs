using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using Microsoft.Extensions.Logging;

namespace EVEMonitor.Core.Services
{
    /// <summary>
    /// 钉钉警报服务实现
    /// </summary>
    public class DingTalkAlertService : IAlertService
    {
        private readonly ILogger<DingTalkAlertService> _logger;
        private readonly IConfigService _configService;
        private readonly HttpClient _httpClient;
        private readonly object _lockObject = new object();
        private DateTime _lastAlertTime = DateTime.MinValue;
        private readonly TimeSpan _minimumAlertInterval = TimeSpan.FromSeconds(10);
        private string _webhookUrl = string.Empty;

        /// <summary>
        /// 钉钉Webhook URL
        /// </summary>
        public string WebhookUrl
        {
            get => _webhookUrl;
            set => _webhookUrl = value;
        }

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="logger">日志服务</param>
        /// <param name="configService">配置服务</param>
        public DingTalkAlertService(ILogger<DingTalkAlertService> logger, IConfigService configService)
        {
            _logger = logger;
            _configService = configService;
            _httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(10)
            };

            // 从配置中获取Webhook URL
            if (_configService.CurrentConfig != null)
            {
                WebhookUrl = _configService.CurrentConfig.DingTalkWebhookUrl;
            }

            // 订阅配置变更事件
            _configService.ConfigChanged += OnConfigChanged;
        }

        /// <summary>
        /// 推送舰船警报
        /// </summary>
        /// <param name="systemName">星系名称</param>
        /// <param name="ships">舰船信息列表</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>推送是否成功</returns>
        public async Task<bool> PushShipAlertAsync(string systemName, List<ShipInfo> ships, int emulatorIndex)
        {
            if (ships == null || ships.Count == 0)
            {
                _logger?.LogWarning("舰船信息列表为空");
                return false;
            }

            var alertData = new AlertData
            {
                Title = $"危险舰船警报 - 模拟器 {emulatorIndex + 1}",
                Message = $"在星系 {systemName} 中发现 {ships.Count} 艘危险舰船",
                AlertType = AlertType.DangerousShip,
                AdditionalData = ships[0], // 取第一个舰船作为主要信息
                SystemName = systemName,
                Timestamp = DateTime.Now
            };

            return await PushAlertAsync(alertData);
        }

        /// <summary>
        /// 发送警报
        /// </summary>
        /// <param name="alertData">警报数据</param>
        /// <returns>是否发送成功</returns>
        public async Task<bool> PushAlertAsync(AlertData alertData)
        {
            if (alertData == null)
            {
                _logger?.LogWarning("警报数据为空");
                return false;
            }

            var config = _configService.CurrentConfig;
            if (!config.EnableDingTalkAlerts)
            {
                _logger?.LogInformation("钉钉警报未启用，跳过发送");
                return false;
            }

            // 检查是否需要限制警报频率
            if (!ShouldSendAlert())
            {
                _logger?.LogInformation("警报频率过高，跳过发送");
                return false;
            }

            try
            {
                string webhookUrl = config.DingTalkWebhookUrl;
                string secret = config.DingTalkSecret;

                if (string.IsNullOrEmpty(webhookUrl))
                {
                    _logger?.LogWarning("钉钉Webhook URL未配置");
                    return false;
                }

                // 如果有配置加签密钥，处理加签
                if (!string.IsNullOrEmpty(secret))
                {
                    long timestamp = DateTimeOffset.Now.ToUnixTimeMilliseconds();
                    string signContent = $"{timestamp}\n{secret}";
                    string sign = ComputeHmacSha256(signContent, secret);
                    webhookUrl = $"{webhookUrl}&timestamp={timestamp}&sign={sign}";
                }

                // 构建消息
                var message = CreateMarkdownMessage(alertData);

                // 发送消息
                var stringContent = new StringContent(JsonSerializer.Serialize(message), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync(webhookUrl, stringContent);

                if (response.IsSuccessStatusCode)
                {
                    // 更新最后警报时间
                    lock (_lockObject)
                    {
                        _lastAlertTime = DateTime.Now;
                    }

                    string responseBody = await response.Content.ReadAsStringAsync();
                    _logger?.LogInformation($"钉钉警报发送成功：{responseBody}");
                    return true;
                }
                else
                {
                    string errorResponse = await response.Content.ReadAsStringAsync();
                    _logger?.LogError($"钉钉警报发送失败，状态码：{response.StatusCode}，响应：{errorResponse}");
                    return false;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"发送钉钉警报异常：{ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 发送性能警报
        /// </summary>
        /// <param name="message">消息</param>
        /// <param name="processingTime">处理时间</param>
        /// <returns>是否发送成功</returns>
        public async Task<bool> PushPerformanceAlertAsync(string message, TimeSpan processingTime)
        {
            var alertData = new AlertData
            {
                Title = "性能警报",
                Message = $"性能警告：{message}，处理时间：{processingTime.TotalMilliseconds:F2}ms",
                AlertType = AlertType.Performance,
                Timestamp = DateTime.Now
            };

            return await PushAlertAsync(alertData);
        }

        /// <summary>
        /// 构建Markdown格式消息
        /// </summary>
        /// <param name="alertData">警报数据</param>
        /// <returns>消息对象</returns>
        private object CreateMarkdownMessage(AlertData alertData)
        {
            string title = alertData.Title;
            StringBuilder content = new StringBuilder();

            content.AppendLine($"### {title}");
            content.AppendLine($"#### 时间：{alertData.Timestamp:yyyy-MM-dd HH:mm:ss}");
            content.AppendLine($"#### 消息：{alertData.Message}");

            // 根据不同的警报类型添加不同的信息
            switch (alertData.AlertType)
            {
                case AlertType.DangerousShip:
                    var shipInfo = alertData.AdditionalData as ShipInfo;
                    if (shipInfo != null)
                    {
                        content.AppendLine($"#### 舰船信息：");
                        content.AppendLine($"- 名称：{shipInfo.Name}");
                        content.AppendLine($"- 类型：{shipInfo.ShipType}");
                        content.AppendLine($"- 距离：{shipInfo.Distance}");
                        content.AppendLine($"- 公司：{shipInfo.Corporation}");
                    }
                    break;

                case AlertType.SystemAlert:
                    content.AppendLine($"#### 星系：{alertData.SystemName}");
                    break;
            }

            content.AppendLine("\n> EVE屏幕监控警报系统");

            return new
            {
                msgtype = "markdown",
                markdown = new
                {
                    title = title,
                    text = content.ToString()
                }
            };
        }

        /// <summary>
        /// 计算HMAC SHA256签名
        /// </summary>
        /// <param name="content">签名内容</param>
        /// <param name="key">密钥</param>
        /// <returns>签名结果</returns>
        private string ComputeHmacSha256(string content, string key)
        {
            byte[] keyBytes = Encoding.UTF8.GetBytes(key);
            byte[] contentBytes = Encoding.UTF8.GetBytes(content);

            using (HMACSHA256 hmac = new HMACSHA256(keyBytes))
            {
                byte[] hashBytes = hmac.ComputeHash(contentBytes);
                return Convert.ToBase64String(hashBytes);
            }
        }

        /// <summary>
        /// 判断是否应该发送警报（限制频率）
        /// </summary>
        /// <returns>是否应该发送</returns>
        private bool ShouldSendAlert()
        {
            lock (_lockObject)
            {
                TimeSpan elapsed = DateTime.Now - _lastAlertTime;
                return elapsed >= _minimumAlertInterval;
            }
        }

        /// <summary>
        /// 配置变更事件处理
        /// </summary>
        private void OnConfigChanged(object? sender, ConfigChangedEventArgs e)
        {
            if (e.Config == null)
                return;

            lock (_lockObject)
            {
                WebhookUrl = e.Config.DingTalkWebhookUrl;
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            _configService.ConfigChanged -= OnConfigChanged;
            _httpClient.Dispose();
        }
    }
}