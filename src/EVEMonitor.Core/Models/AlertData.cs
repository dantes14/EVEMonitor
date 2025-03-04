namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 警报数据
    /// </summary>
    public class AlertData
    {
        /// <summary>
        /// 警报ID
        /// </summary>
        public string Id { get; set; } = Guid.NewGuid().ToString("N");

        /// <summary>
        /// 警报类型
        /// </summary>
        public AlertType Type { get; set; } = AlertType.Info;

        /// <summary>
        /// 警报标题
        /// </summary>
        public string Title { get; set; }

        /// <summary>
        /// 警报内容
        /// </summary>
        public string Content { get; set; }

        /// <summary>
        /// 警报时间
        /// </summary>
        public DateTime Timestamp { get; set; } = DateTime.Now;

        /// <summary>
        /// 警报来源
        /// </summary>
        public string Source { get; set; } = "系统";

        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int EmulatorIndex { get; set; } = -1;

        /// <summary>
        /// 星系名称
        /// </summary>
        public string SystemName { get; set; }

        /// <summary>
        /// 危险等级（0-10）
        /// </summary>
        public int DangerLevel { get; set; } = 0;

        /// <summary>
        /// 相关舰船信息
        /// </summary>
        public List<ShipInfo> RelatedShips { get; set; } = new List<ShipInfo>();

        /// <summary>
        /// 是否已处理
        /// </summary>
        public bool IsHandled { get; set; } = false;

        /// <summary>
        /// 处理时间
        /// </summary>
        public DateTime? HandledTime { get; set; }

        /// <summary>
        /// 处理备注
        /// </summary>
        public string HandledNote { get; set; }

        /// <summary>
        /// 获取警报摘要
        /// </summary>
        /// <returns>警报摘要</returns>
        public string GetSummary()
        {
            string typeStr = Type switch
            {
                AlertType.Info => "信息",
                AlertType.Warning => "警告",
                AlertType.Danger => "危险",
                AlertType.Performance => "性能",
                _ => "未知"
            };

            string emulatorInfo = EmulatorIndex >= 0 ? $"模拟器 #{EmulatorIndex + 1}" : "";
            string systemInfo = !string.IsNullOrEmpty(SystemName) ? $"星系: {SystemName}" : "";
            string timeInfo = $"{Timestamp:HH:mm:ss}";

            return $"[{typeStr}] {Title} - {emulatorInfo} {systemInfo} - {timeInfo}";
        }

        /// <summary>
        /// 转换为钉钉消息格式
        /// </summary>
        /// <returns>钉钉消息内容</returns>
        public string ToDingTalkMessage()
        {
            string typeEmoji = Type switch
            {
                AlertType.Info => "ℹ️",
                AlertType.Warning => "⚠️",
                AlertType.Danger => "🔴",
                AlertType.Performance => "⚙️",
                _ => "❓"
            };

            string header = $"{typeEmoji} **{Title}**\n\n";
            string body = $"{Content}\n\n";
            
            string details = "";
            if (!string.IsNullOrEmpty(SystemName))
            {
                details += $"- 星系: {SystemName}\n";
            }
            
            if (EmulatorIndex >= 0)
            {
                details += $"- 模拟器: #{EmulatorIndex + 1}\n";
            }
            
            if (DangerLevel > 0)
            {
                details += $"- 危险等级: {DangerLevel}/10\n";
            }
            
            if (RelatedShips.Any())
            {
                details += $"- 检测到舰船: {RelatedShips.Count}艘\n";
                int maxShips = Math.Min(5, RelatedShips.Count);
                for (int i = 0; i < maxShips; i++)
                {
                    details += $"  - {RelatedShips[i]}\n";
                }
                
                if (RelatedShips.Count > maxShips)
                {
                    details += $"  - 等 {RelatedShips.Count - maxShips} 艘...\n";
                }
            }
            
            string footer = $"\n*时间: {Timestamp:yyyy-MM-dd HH:mm:ss}*";
            
            return header + body + details + footer;
        }
    }

    /// <summary>
    /// 警报类型
    /// </summary>
    public enum AlertType
    {
        /// <summary>
        /// 信息
        /// </summary>
        Info,

        /// <summary>
        /// 警告
        /// </summary>
        Warning,

        /// <summary>
        /// 危险
        /// </summary>
        Danger,

        /// <summary>
        /// 性能
        /// </summary>
        Performance
    }
} 