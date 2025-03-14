using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Runtime.Versioning;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 截图分析结果
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class ScreenshotAnalysisResult
    {
        private DateTime _startTime = DateTime.Now;
        private TimeSpan _processingTime = TimeSpan.Zero;

        /// <summary>
        /// 系统名称
        /// </summary>
        public required string SystemName { get; init; }

        /// <summary>
        /// 舰船列表
        /// </summary>
        public List<ShipInfo> Ships { get; init; } = new List<ShipInfo>();

        /// <summary>
        /// 原始截图
        /// </summary>
        public Bitmap? OriginalScreenshot { get; init; }

        /// <summary>
        /// 处理后的截图
        /// </summary>
        public Bitmap? ProcessedScreenshot { get; init; }

        /// <summary>
        /// 处理时间戳
        /// </summary>
        public DateTime Timestamp { get; init; } = DateTime.Now;

        /// <summary>
        /// 错误信息
        /// </summary>
        public string ErrorMessage { get; init; } = string.Empty;

        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int EmulatorIndex { get; init; }

        /// <summary>
        /// 是否包含危险舰船
        /// </summary>
        public bool ContainsDangerousShips { get; init; }

        /// <summary>
        /// 处理是否成功
        /// </summary>
        public bool IsSuccessful { get; init; } = true;

        /// <summary>
        /// 分析是否成功
        /// </summary>
        public bool Success => IsSuccessful;

        /// <summary>
        /// 检测到的舰船信息列表
        /// </summary>
        public List<ShipInfo> DetectedShips => Ships;

        /// <summary>
        /// 处理时间
        /// </summary>
        public TimeSpan ProcessingTime
        {
            get => _processingTime;
            init => _processingTime = value;
        }

        /// <summary>
        /// 设置处理时间
        /// </summary>
        public void SetProcessingTime()
        {
            _processingTime = DateTime.Now - _startTime;
        }

        /// <summary>
        /// 是否检测到危险
        /// </summary>
        public bool DangerDetected => ContainsDangerousShips;

        /// <summary>
        /// 危险等级（0-10）
        /// </summary>
        public int DangerLevel
        {
            get
            {
                if (!Ships.Any()) return 0;

                // 根据危险舰船数量和类型计算危险等级
                int level = 0;
                foreach (var ship in Ships.Where(s => s.IsDangerous))
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
            return $"星系: {SystemName}, 检测到 {Ships.Count} 艘舰船, {dangerStatus}, 处理时间: {ProcessingTime.TotalMilliseconds:F2}ms";
        }

        /// <summary>
        /// 创建一个成功的分析结果
        /// </summary>
        [SupportedOSPlatform("windows")]
        public static ScreenshotAnalysisResult CreateSuccessResult(string systemName, Bitmap? originalScreenshot, int emulatorIndex)
        {
            return new ScreenshotAnalysisResult
            {
                SystemName = systemName,
                OriginalScreenshot = originalScreenshot,
                EmulatorIndex = emulatorIndex,
                IsSuccessful = true
            };
        }

        /// <summary>
        /// 创建一个失败的分析结果
        /// </summary>
        [SupportedOSPlatform("windows")]
        public static ScreenshotAnalysisResult CreateFailureResult(string errorMessage, Bitmap? originalScreenshot, int emulatorIndex)
        {
            return new ScreenshotAnalysisResult
            {
                SystemName = "未知",
                OriginalScreenshot = originalScreenshot,
                EmulatorIndex = emulatorIndex,
                ErrorMessage = errorMessage,
                IsSuccessful = false
            };
        }
    }
}