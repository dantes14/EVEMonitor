using System;
using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 舰船信息
    /// </summary>
    public class ShipInfo
    {
        /// <summary>
        /// 舰船ID
        /// </summary>
        public string Id { get; set; } = Guid.NewGuid().ToString("N");

        /// <summary>
        /// 舰船名称
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// 舰船类型
        /// </summary>
        public string Type { get; set; } = string.Empty;

        /// <summary>
        /// 舰船类型（别名，与Type保持一致）
        /// </summary>
        public string ShipType
        {
            get => Type;
            set => Type = value;
        }

        /// <summary>
        /// 舰船所属联盟/公司
        /// </summary>
        public string Corporation { get; set; } = string.Empty;

        /// <summary>
        /// 舰船在截图中的位置
        /// </summary>
        public Rectangle BoundingBox { get; set; }

        /// <summary>
        /// 舰船在截图中的置信度
        /// </summary>
        public float Confidence { get; set; }

        /// <summary>
        /// 是否为危险舰船
        /// </summary>
        public bool IsDangerous { get; set; }

        /// <summary>
        /// 威胁等级（1-5）
        /// </summary>
        public int ThreatLevel { get; set; } = 1;

        /// <summary>
        /// 舰船状态
        /// </summary>
        public ShipStatus Status { get; set; } = ShipStatus.Normal;

        /// <summary>
        /// 舰船距离（单位：千米）
        /// </summary>
        public double Distance { get; set; }

        /// <summary>
        /// 首次发现时间
        /// </summary>
        public DateTime FirstSeen { get; set; } = DateTime.Now;

        /// <summary>
        /// 最后更新时间
        /// </summary>
        public DateTime LastUpdated { get; set; } = DateTime.Now;

        /// <summary>
        /// 舰船标签颜色
        /// </summary>
        public Color TagColor
        {
            get
            {
                return Status switch
                {
                    ShipStatus.Hostile => Color.Red,
                    ShipStatus.Neutral => Color.Orange,
                    ShipStatus.Friendly => Color.Green,
                    _ => Color.Gray
                };
            }
        }

        /// <summary>
        /// 获取舰船信息摘要
        /// </summary>
        /// <returns>舰船信息摘要</returns>
        public override string ToString()
        {
            string distanceStr = Distance > 0 ? $"{Distance:F1}km" : "未知";
            string corpInfo = !string.IsNullOrEmpty(Corporation) ? $"[{Corporation}]" : "";
            return $"{Name} {corpInfo} - {Type} - {distanceStr} - {Status}";
        }
    }

    /// <summary>
    /// 舰船状态
    /// </summary>
    public enum ShipStatus
    {
        /// <summary>
        /// 正常
        /// </summary>
        Normal,

        /// <summary>
        /// 敌对
        /// </summary>
        Hostile,

        /// <summary>
        /// 中立
        /// </summary>
        Neutral,

        /// <summary>
        /// 友好
        /// </summary>
        Friendly
    }
}