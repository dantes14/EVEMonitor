using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Tesseract;
using SDIImageFormat = System.Drawing.Imaging.ImageFormat;

namespace EVEMonitor.OCR.Helpers
{
    /// <summary>
    /// 用于将System.Drawing.Bitmap转换为Tesseract.Pix的工具类
    /// </summary>
    public static class PixConverter
    {
        /// <summary>
        /// 将Bitmap转换为Tesseract.Pix格式
        /// </summary>
        /// <param name="bitmap">需要转换的Bitmap图像</param>
        /// <returns>Tesseract的Pix图像</returns>
        public static Pix ToPix(Bitmap bitmap)
        {
            if (bitmap == null)
                throw new ArgumentNullException(nameof(bitmap));

            // 确保图像格式为32位RGBA
            using (var tempBitmap = EnsurePixelFormat(bitmap))
            {
                // 使用Tesseract提供的转换方法
                return Pix.LoadFromMemory(ImageToByte(tempBitmap));
            }
        }

        /// <summary>
        /// 将Bitmap转换为字节数组
        /// </summary>
        private static byte[] ImageToByte(Bitmap img)
        {
            using (var stream = new System.IO.MemoryStream())
            {
                img.Save(stream, SDIImageFormat.Bmp);
                return stream.ToArray();
            }
        }

        /// <summary>
        /// 确保Bitmap具有正确的像素格式
        /// </summary>
        /// <param name="bitmap">原始Bitmap</param>
        /// <returns>具有正确像素格式的Bitmap</returns>
        private static Bitmap EnsurePixelFormat(Bitmap bitmap)
        {
            if (bitmap.PixelFormat == PixelFormat.Format32bppArgb ||
                bitmap.PixelFormat == PixelFormat.Format24bppRgb)
            {
                return new Bitmap(bitmap);
            }

            // 转换为32位ARGB格式
            var convertedBitmap = new Bitmap(bitmap.Width, bitmap.Height, PixelFormat.Format32bppArgb);
            using (var g = Graphics.FromImage(convertedBitmap))
            {
                g.DrawImage(bitmap, new Rectangle(0, 0, bitmap.Width, bitmap.Height));
            }
            return convertedBitmap;
        }

        /// <summary>
        /// 获取像素格式对应的每像素位数
        /// </summary>
        /// <param name="pixelFormat">像素格式</param>
        /// <returns>每像素位数</returns>
        private static int GetBitsPerPixel(PixelFormat pixelFormat)
        {
            switch (pixelFormat)
            {
                case PixelFormat.Format24bppRgb:
                    return 24;
                case PixelFormat.Format32bppRgb:
                case PixelFormat.Format32bppArgb:
                case PixelFormat.Format32bppPArgb:
                    return 32;
                case PixelFormat.Format8bppIndexed:
                    return 8;
                default:
                    throw new ArgumentException($"Unsupported pixel format: {pixelFormat}");
            }
        }
    }
}