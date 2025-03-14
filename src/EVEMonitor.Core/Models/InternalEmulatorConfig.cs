using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 内部模拟器配置
    /// </summary>
    public class InternalEmulatorConfig
    {
        /// <summary>
        /// 是否启用
        /// </summary>
        public bool Enabled { get; set; }

        /// <summary>
        /// 窗口标题
        /// </summary>
        public string WindowTitle { get; set; } = string.Empty;

        /// <summary>
        /// 索引
        /// </summary>
        public int Index { get; set; }

        /// <summary>
        /// 名称
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// 截图区域
        /// </summary>
        public Rectangle CaptureRegion { get; set; }

        /// <summary>
        /// 系统名称识别区域
        /// </summary>
        public Rectangle SystemNameROI { get; set; }

        /// <summary>
        /// 舰船表格识别区域
        /// </summary>
        public Rectangle ShipTableROI { get; set; }

        /// <summary>
        /// 转换为 EmulatorConfig
        /// </summary>
        /// <returns>EmulatorConfig 对象</returns>
        public EmulatorConfig ToEmulatorConfig()
        {
            return new EmulatorConfig
            {
                Name = this.Name,
                Enabled = this.Enabled,
                WindowTitle = this.WindowTitle,
                Index = this.Index,
                CaptureRegion = this.CaptureRegion,
                SystemNameRegion = this.SystemNameROI,
                ShipTableRegion = this.ShipTableROI
            };
        }
    }
}