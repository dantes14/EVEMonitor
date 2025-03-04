using System.Drawing;
using System.Drawing.Imaging;
using OpenCvSharp;
using OpenCvSharp.Extensions;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;

namespace EVEMonitor.ImageProcessing.Services
{
    /// <summary>
    /// 图像处理服务实现
    /// </summary>
    public class ImageProcessingService : IImageProcessingService
    {
        /// <summary>
        /// 模拟器布局配置
        /// </summary>
        public List<EmulatorConfig> EmulatorConfigs { get; set; } = new List<EmulatorConfig>();

        /// <summary>
        /// 初始化图像处理服务
        /// </summary>
        public ImageProcessingService()
        {
        }

        /// <summary>
        /// 初始化图像处理服务
        /// </summary>
        /// <param name="emulatorConfigs">模拟器配置列表</param>
        public ImageProcessingService(List<EmulatorConfig> emulatorConfigs)
        {
            EmulatorConfigs = emulatorConfigs;
        }

        /// <summary>
        /// 处理截图，分割为多个模拟器子图像
        /// </summary>
        /// <param name="screenshot">完整截图</param>
        /// <returns>模拟器图像列表</returns>
        public List<EmulatorImage> ProcessScreenshot(Bitmap screenshot)
        {
            if (screenshot == null || EmulatorConfigs == null || !EmulatorConfigs.Any())
                return new List<EmulatorImage>();

            var result = new List<EmulatorImage>();

            // 遍历所有启用的模拟器配置
            for (int i = 0; i < EmulatorConfigs.Count; i++)
            {
                var config = EmulatorConfigs[i];
                if (!config.Enabled) continue;

                try
                {
                    // 检查窗口句柄是否有效
                    if (config.WindowHandle != IntPtr.Zero)
                    {
                        // TODO: 从活动窗口捕获，这里简化处理为从主截图裁剪
                    }

                    // 获取模拟器区域
                    var emulatorRegion = config.CaptureRegion;
                    var region = new Rectangle(
                        emulatorRegion.X,
                        emulatorRegion.Y,
                        emulatorRegion.Width,
                        emulatorRegion.Height
                    );

                    // 检查裁剪区域是否超出原图范围
                    if (region.X < 0) region.X = 0;
                    if (region.Y < 0) region.Y = 0;
                    if (region.Right > screenshot.Width) region.Width = screenshot.Width - region.X;
                    if (region.Bottom > screenshot.Height) region.Height = screenshot.Height - region.Y;

                    // 区域无效则跳过
                    if (region.Width <= 0 || region.Height <= 0)
                        continue;

                    // 裁剪出模拟器区域
                    Bitmap emulatorBitmap = new Bitmap(region.Width, region.Height);
                    using (Graphics g = Graphics.FromImage(emulatorBitmap))
                    {
                        g.DrawImage(screenshot, 
                            new Rectangle(0, 0, region.Width, region.Height),
                            region,
                            GraphicsUnit.Pixel);
                    }

                    // 创建模拟器图像对象
                    var emulatorImage = new EmulatorImage
                    {
                        Index = i,
                        Image = emulatorBitmap,
                        Region = region
                    };

                    result.Add(emulatorImage);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"处理模拟器 {i} 截图失败: {ex.Message}");
                }
            }

            return result;
        }

        /// <summary>
        /// 提取感兴趣区域
        /// </summary>
        /// <param name="emulatorImage">模拟器图像</param>
        /// <returns>感兴趣区域列表</returns>
        public List<RegionOfInterest> ExtractROIs(EmulatorImage emulatorImage)
        {
            if (emulatorImage == null || emulatorImage.Image == null)
                return new List<RegionOfInterest>();

            var result = new List<RegionOfInterest>();
            var config = GetEmulatorConfig(emulatorImage.Index);
            if (config == null)
                return result;

            try
            {
                // 提取星系名称区域
                var systemNameRegion = ExtractSystemNameRegion(emulatorImage.Image, config);
                if (systemNameRegion != null)
                {
                    result.Add(systemNameRegion);
                }

                // 提取舰船表格区域
                var shipTableRegion = ExtractShipTableRegion(emulatorImage.Image, config);
                if (shipTableRegion != null)
                {
                    result.Add(shipTableRegion);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"提取模拟器 {emulatorImage.Index} ROI失败: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// 提取星系名称区域
        /// </summary>
        /// <param name="image">模拟器图像</param>
        /// <param name="config">模拟器配置</param>
        /// <returns>星系名称区域</returns>
        private RegionOfInterest ExtractSystemNameRegion(Bitmap image, EmulatorConfig config)
        {
            // 创建星系名称区域的ROI
            // 实际区域需要根据游戏界面进行调整
            Rectangle systemNameRect = new Rectangle(
                image.Width / 2 - 100, // 假设位于中间偏上位置
                40,
                200,
                30
            );

            Bitmap systemNameImage = new Bitmap(systemNameRect.Width, systemNameRect.Height);
            using (Graphics g = Graphics.FromImage(systemNameImage))
            {
                g.DrawImage(image,
                    new Rectangle(0, 0, systemNameRect.Width, systemNameRect.Height),
                    systemNameRect,
                    GraphicsUnit.Pixel);
            }

            return new RegionOfInterest
            {
                Type = RegionOfInterestType.SystemName,
                Image = systemNameImage
            };
        }

        /// <summary>
        /// 提取舰船表格区域
        /// </summary>
        /// <param name="image">模拟器图像</param>
        /// <param name="config">模拟器配置</param>
        /// <returns>舰船表格区域</returns>
        private RegionOfInterest ExtractShipTableRegion(Bitmap image, EmulatorConfig config)
        {
            // 创建舰船表格区域的ROI
            // 实际区域需要根据游戏界面进行调整
            Rectangle shipTableRect = new Rectangle(
                image.Width - 250, // 假设位于右侧
                image.Height / 3,
                200,
                image.Height / 2
            );

            Bitmap shipTableImage = new Bitmap(shipTableRect.Width, shipTableRect.Height);
            using (Graphics g = Graphics.FromImage(shipTableImage))
            {
                g.DrawImage(image,
                    new Rectangle(0, 0, shipTableRect.Width, shipTableRect.Height),
                    shipTableRect,
                    GraphicsUnit.Pixel);
            }

            return new RegionOfInterest
            {
                Type = RegionOfInterestType.ShipTable,
                Image = shipTableImage
            };
        }

        /// <summary>
        /// 获取模拟器配置
        /// </summary>
        /// <param name="index">模拟器索引</param>
        /// <returns>模拟器配置</returns>
        private EmulatorConfig GetEmulatorConfig(int index)
        {
            if (EmulatorConfigs == null || index < 0 || index >= EmulatorConfigs.Count)
                return null;

            return EmulatorConfigs[index];
        }

        /// <summary>
        /// 预处理图像以提高OCR识别率
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <returns>预处理后的图像</returns>
        public Bitmap PreprocessImage(Bitmap image)
        {
            if (image == null)
                return null;

            // 将Bitmap转换为Mat
            using (var mat = BitmapConverter.ToMat(image))
            {
                // 转换为灰度图
                using (var grayMat = new Mat())
                {
                    Cv2.CvtColor(mat, grayMat, ColorConversionCodes.BGR2GRAY);

                    // 应用高斯模糊减少噪点
                    using (var blurredMat = new Mat())
                    {
                        Cv2.GaussianBlur(grayMat, blurredMat, new OpenCvSharp.Size(3, 3), 0);

                        // 应用自适应阈值二值化
                        using (var binaryMat = new Mat())
                        {
                            Cv2.AdaptiveThreshold(blurredMat, binaryMat, 255,
                                AdaptiveThresholdType.GaussianC, ThresholdType.Binary, 11, 2);

                            // 应用闭操作，连接断开的文本
                            using (var kernel = Cv2.GetStructuringElement(MorphShapes.Rect, new OpenCvSharp.Size(3, 3)))
                            using (var closedMat = new Mat())
                            {
                                Cv2.MorphologyEx(binaryMat, closedMat, MorphTypes.Close, kernel);

                                // 转换回Bitmap
                                return BitmapConverter.ToBitmap(closedMat);
                            }
                        }
                    }
                }
            }
        }
    }
} 