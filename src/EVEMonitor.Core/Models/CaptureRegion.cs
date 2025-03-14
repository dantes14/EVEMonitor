using System.Drawing;

namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 截图区域
    /// </summary>
    public class CaptureRegion
    {
        /// <summary>
        /// X 坐标
        /// </summary>
        public int X { get; set; }

        /// <summary>
        /// Y 坐标
        /// </summary>
        public int Y { get; set; }

        /// <summary>
        /// 宽度
        /// </summary>
        public int Width { get; set; }

        /// <summary>
        /// 高度
        /// </summary>
        public int Height { get; set; }

        /// <summary>
        /// 是否使用相对坐标
        /// </summary>
        public bool UseRelativeCoordinates { get; set; }

        /// <summary>
        /// 转换为 Rectangle
        /// </summary>
        public Rectangle ToRectangle()
        {
            return new Rectangle(X, Y, Width, Height);
        }

        /// <summary>
        /// 从 Rectangle 创建
        /// </summary>
        public static CaptureRegion FromRectangle(Rectangle rect, bool useRelative = false)
        {
            return new CaptureRegion
            {
                X = rect.X,
                Y = rect.Y,
                Width = rect.Width,
                Height = rect.Height,
                UseRelativeCoordinates = useRelative
            };
        }
    }
} 