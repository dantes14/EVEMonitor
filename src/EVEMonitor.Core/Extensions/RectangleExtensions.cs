using System.Drawing;

namespace EVEMonitor.Core.Extensions
{
    /// <summary>
    /// Rectangle 扩展方法
    /// </summary>
    public static class RectangleExtensions
    {
        /// <summary>
        /// 将 Rectangle 转换为 Rectangle
        /// </summary>
        /// <param name="rect">Rectangle 对象</param>
        /// <returns>转换后的 Rectangle</returns>
        public static Rectangle ToRectangle(this Rectangle rect)
        {
            return rect;
        }
    }
} 