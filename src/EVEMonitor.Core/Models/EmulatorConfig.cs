using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 模拟器配置类，用于存储模拟器窗口相关的配置信息
    /// </summary>
    public class EmulatorConfig
    {
        /// <summary>
        /// 模拟器名称
        /// </summary>
        public string Name { get; set; } = string.Empty;
        
        /// <summary>
        /// 模拟器区域
        /// </summary>
        public Rectangle Region { get; set; }
        
        /// <summary>
        /// 星系名称区域相对位置
        /// </summary>
        public Rectangle SystemNameRegion { get; set; }
        
        /// <summary>
        /// 舰船表格区域相对位置
        /// </summary>
        public Rectangle ShipTableRegion { get; set; }

        /// <summary>
        /// 获取星系名称的绝对区域
        /// </summary>
        /// <returns>星系名称的绝对区域</returns>
        public Rectangle GetAbsoluteSystemNameRegion()
        {
            return new Rectangle(
                Region.X + SystemNameRegion.X,
                Region.Y + SystemNameRegion.Y,
                SystemNameRegion.Width,
                SystemNameRegion.Height);
        }

        /// <summary>
        /// 获取舰船表格的绝对区域
        /// </summary>
        /// <returns>舰船表格的绝对区域</returns>
        public Rectangle GetAbsoluteShipTableRegion()
        {
            return new Rectangle(
                Region.X + ShipTableRegion.X,
                Region.Y + ShipTableRegion.Y,
                ShipTableRegion.Width,
                ShipTableRegion.Height);
        }
    }
} 