using System;
using System.Collections.Generic;
using System.Linq;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 警报类型枚举
    /// </summary>
    public enum AlertType
    {
        /// <summary>
        /// 未知
        /// </summary>
        Unknown = 0,

        /// <summary>
        /// 信息
        /// </summary>
        Info = 1,

        /// <summary>
        /// 警告
        /// </summary>
        Warning = 2,

        /// <summary>
        /// 危险
        /// </summary>
        Danger = 3,

        /// <summary>
        /// 危险舰船
        /// </summary>
        DangerousShip = 4,

        /// <summary>
        /// 星系警报
        /// </summary>
        SystemAlert = 5,

        /// <summary>
        /// 性能警报
        /// </summary>
        Performance = 6,

        /// <summary>
        /// 系统警报
        /// </summary>
        System = 7,

        /// <summary>
        /// 错误警报
        /// </summary>
        Error = 8,

        /// <summary>
        /// 舰船警报
        /// </summary>
        Ship = 9
    }

    /// <summary>
    /// 警报数据类
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
        public AlertType AlertType { get; set; } = AlertType.Unknown;

        /// <summary>
        /// 警报标题
        /// </summary>
        public string Title { get; set; } = string.Empty;

        /// <summary>
        /// 警报内容
        /// </summary>
        public string Message { get; set; } = string.Empty;

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
        public string SystemName { get; set; } = string.Empty;

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
        public string HandledNote { get; set; } = string.Empty;

        /// <summary>
        /// 附加数据
        /// </summary>
        public object? AdditionalData { get; set; }

        /// <summary>
        /// 获取警报摘要
        /// </summary>
        /// <returns>警报摘要</returns>
        public string GetSummary()
        {
            string typeStr = AlertType switch
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
            string typeEmoji = AlertType switch
            {
                AlertType.Info => "ℹ️",
                AlertType.Warning => "⚠️",
                AlertType.Danger => "🔴",
                AlertType.Performance => "⚙️",
                _ => "❓"
            };

            string header = $"{typeEmoji} **{Title}**\n\n";
            string body = $"{Message}\n\n";

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
}