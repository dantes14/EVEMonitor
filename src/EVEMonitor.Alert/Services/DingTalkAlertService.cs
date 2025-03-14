using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Alert.Services
{
    /// <summary>
    /// 钉钉警报服务实现
    /// </summary>
    public class DingTalkAlertService : IAlertService
    {
        private readonly HttpClient _httpClient;
        private readonly IConfigService _configService;
        private string _secret;

        /// <summary>
        /// 钉钉Webhook URL
        /// </summary>
        public string WebhookUrl { get; set; }

        /// <summary>
        /// 初始化钉钉警报服务
        /// </summary>
        /// <param name="configService">配置服务</param>
        public DingTalkAlertService(IConfigService configService)
        {
            _configService = configService;
            _httpClient = new HttpClient();
            WebhookUrl = _configService.CurrentConfig.DingTalkWebhookUrl;
            _secret = _configService.CurrentConfig.DingTalkSecret;

            // 订阅配置变更事件
            _configService.ConfigChanged += (sender, args) =>
            {
                WebhookUrl = args.Config.DingTalkWebhookUrl;
                _secret = args.Config.DingTalkSecret;
            };
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
            if (string.IsNullOrEmpty(WebhookUrl) || !ships.Any())
                return false;

            var dangerousShips = ships.Where(s => s.IsDangerous).ToList();
            if (!dangerousShips.Any())
                return true; // 没有危险舰船，不需要推送

            var alertData = new AlertData
            {
                AlertType = AlertType.Danger,
                Title = $"危险舰船警报 - {systemName}",
                Message = $"在星系 {systemName} 中检测到 {dangerousShips.Count} 艘危险舰船",
                EmulatorIndex = emulatorIndex,
                SystemName = systemName,
                RelatedShips = dangerousShips,
                DangerLevel = CalculateDangerLevel(dangerousShips)
            };

            return await PushAlertAsync(alertData);
        }

        /// <summary>
        /// 推送性能警报
        /// </summary>
        /// <param name="message">警报消息</param>
        /// <param name="processingTime">处理时间</param>
        /// <returns>推送是否成功</returns>
        public async Task<bool> PushPerformanceAlertAsync(string message, TimeSpan processingTime)
        {
            if (string.IsNullOrEmpty(WebhookUrl))
                return false;

            if (processingTime.TotalMilliseconds < _configService.CurrentConfig.Performance.PerformanceAlertThresholdMs)
                return true; // 处理时间未超过阈值，不需要推送

            var alertData = new AlertData
            {
                AlertType = AlertType.Performance,
                Title = "性能警报",
                Message = $"{message} (处理时间: {processingTime.TotalMilliseconds:F2}ms)",
                EmulatorIndex = -1,
            };

            return await PushAlertAsync(alertData);
        }

        /// <summary>
        /// 推送警报
        /// </summary>
        /// <param name="alertData">警报数据</param>
        /// <returns>推送是否成功</returns>
        public async Task<bool> PushAlertAsync(AlertData alertData)
        {
            if (string.IsNullOrEmpty(WebhookUrl) || alertData == null)
                return false;

            try
            {
                string url = WebhookUrl;

                // 如果有密钥，则生成签名
                if (!string.IsNullOrEmpty(_secret))
                {
                    long timestamp = DateTimeOffset.Now.ToUnixTimeMilliseconds();
                    string sign = GenerateSignature(timestamp, _secret);
                    url = $"{WebhookUrl}&timestamp={timestamp}&sign={sign}";
                }

                var message = alertData.ToDingTalkMessage();
                var payload = new
                {
                    msgtype = "markdown",
                    markdown = new
                    {
                        title = alertData.Title,
                        text = message
                    }
                };

                var content = new StringContent(
                    JsonSerializer.Serialize(payload),
                    Encoding.UTF8,
                    "application/json");

                var response = await _httpClient.PostAsync(url, content);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                // 记录异常但不抛出，防止因警报发送失败影响主流程
                Console.WriteLine($"发送警报失败: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 计算危险等级
        /// </summary>
        /// <param name="ships">舰船列表</param>
        /// <returns>危险等级（0-10）</returns>
        private int CalculateDangerLevel(List<ShipInfo> ships)
        {
            if (!ships.Any())
                return 0;

            int level = 0;
            foreach (var ship in ships.Where(s => s.IsDangerous))
            {
                level += ship.ThreatLevel;
            }

            // 归一化到0-10范围
            return Math.Min(10, level);
        }

        /// <summary>
        /// 生成钉钉签名
        /// </summary>
        /// <param name="timestamp">时间戳</param>
        /// <param name="secret">密钥</param>
        /// <returns>签名</returns>
        private string GenerateSignature(long timestamp, string secret)
        {
            string stringToSign = $"{timestamp}\n{secret}";
            byte[] keyBytes = Encoding.UTF8.GetBytes(secret);
            byte[] messageBytes = Encoding.UTF8.GetBytes(stringToSign);

            using (var hmac = new HMACSHA256(keyBytes))
            {
                byte[] hashBytes = hmac.ComputeHash(messageBytes);
                return Convert.ToBase64String(hashBytes);
            }
        }
    }
}