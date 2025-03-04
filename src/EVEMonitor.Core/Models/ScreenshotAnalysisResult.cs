using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 截图分析结果
    /// </summary>
    public class ScreenshotAnalysisResult
    {
        /// <summary>
        /// 分析是否成功
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// 当前所在星系名称
        /// </summary>
        public string SystemName { get; set; }

        /// <summary>
        /// 检测到的舰船信息列表
        /// </summary>
        public List<ShipInfo> DetectedShips { get; set; } = new List<ShipInfo>();

        /// <summary>
        /// 原始截图
        /// </summary>
        public Bitmap OriginalScreenshot { get; set; }

        /// <summary>
        /// 处理后的截图（带标记）
        /// </summary>
        public Bitmap ProcessedScreenshot { get; set; }

        /// <summary>
        /// 处理时间
        /// </summary>
        public TimeSpan ProcessingTime { get; set; }

        /// <summary>
        /// 错误信息（如果有）
        /// </summary>
        public string ErrorMessage { get; set; }

        /// <summary>
        /// 截图时间戳
        /// </summary>
        public DateTime Timestamp { get; set; } = DateTime.Now;

        /// <summary>
        /// 是否检测到危险
        /// </summary>
        public bool DangerDetected => DetectedShips.Any(s => s.IsDangerous);

        /// <summary>
        /// 危险等级（0-10）
        /// </summary>
        public int DangerLevel
        {
            get
            {
                if (!DetectedShips.Any()) return 0;
                
                // 根据危险舰船数量和类型计算危险等级
                int level = 0;
                foreach (var ship in DetectedShips.Where(s => s.IsDangerous))
                {
                    level += ship.ThreatLevel;
                }
                
                // 归一化到0-10范围
                return Math.Min(10, level);
            }
        }

        /// <summary>
        /// 获取分析结果摘要
        /// </summary>
        /// <returns>分析结果摘要</returns>
        public string GetSummary()
        {
            if (!Success)
            {
                return $"分析失败: {ErrorMessage}";
            }

            string dangerStatus = DangerDetected ? $"危险等级: {DangerLevel}" : "安全";
            return $"星系: {SystemName ?? "未知"}, 检测到 {DetectedShips.Count} 艘舰船, {dangerStatus}, 处理时间: {ProcessingTime.TotalMilliseconds:F2}ms";
        }
    }
} 