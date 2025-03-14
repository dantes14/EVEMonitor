using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 模拟器配置
    /// </summary>
    public class EmulatorConfig
    {
        /// <summary>
        /// 模拟器名称
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// 是否启用
        /// </summary>
        public bool Enabled { get; set; }

        /// <summary>
        /// 窗口标题
        /// </summary>
        public string WindowTitle { get; set; } = string.Empty;

        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int Index { get; set; }

        /// <summary>
        /// 截图区域
        /// </summary>
        public Rectangle CaptureRegion { get; set; }

        /// <summary>
        /// 星系名称识别区域
        /// </summary>
        public Rectangle SystemNameRegion { get; set; }

        /// <summary>
        /// 舰船表格识别区域
        /// </summary>
        public Rectangle ShipTableRegion { get; set; }

        /// <summary>
        /// 获取绝对坐标的舰船表格区域
        /// </summary>
        /// <returns>绝对坐标的舰船表格区域</returns>
        public Rectangle GetAbsoluteShipTableRegion()
        {
            return new Rectangle(
                CaptureRegion.X + ShipTableRegion.X,
                CaptureRegion.Y + ShipTableRegion.Y,
                ShipTableRegion.Width,
                ShipTableRegion.Height
            );
        }

        /// <summary>
        /// 获取绝对坐标的星系名称区域
        /// </summary>
        /// <returns>绝对坐标的星系名称区域</returns>
        public Rectangle GetAbsoluteSystemNameRegion()
        {
            return new Rectangle(
                CaptureRegion.X + SystemNameRegion.X,
                CaptureRegion.Y + SystemNameRegion.Y,
                SystemNameRegion.Width,
                SystemNameRegion.Height
            );
        }
    }
}