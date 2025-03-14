using System.Drawing;
using System.Drawing.Imaging;
using OpenCvSharp;
using OpenCvSharp.Extensions;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.Core.Extensions;
using Microsoft.Extensions.Logging;
using System.Runtime.Versioning;

namespace EVEMonitor.ImageProcessing.Services
{
    /// <summary>
    /// 图像处理服务实现
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class ImageProcessingService : IImageProcessingService
    {
        private readonly ILogger<ImageProcessingService> _logger;
        private readonly IConfigService _configService;

        /// <summary>
        /// 初始化图像处理服务
        /// </summary>
        /// <param name="logger">日志记录器</param>
        /// <param name="configService">配置服务</param>
        public ImageProcessingService(ILogger<ImageProcessingService> logger, IConfigService configService)
        {
            _logger = logger;
            _configService = configService;
        }

        /// <summary>
        /// 处理图像
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <param name="emulatorName">模拟器名称</param>
        /// <returns>处理后的图像</returns>
        public Bitmap ProcessImage(Bitmap? image, string emulatorName)
        {
            if (image == null)
                return new Bitmap(1, 1);

            try
            {
                var emulator = _configService.CurrentConfig.Emulators.FirstOrDefault(e => e.Name == emulatorName);
                if (emulator == null)
                    return new Bitmap(1, 1);

                // 裁剪图像
                var region = emulator.CaptureRegion;
                if (region.Width <= 0 || region.Height <= 0)
                    return new Bitmap(1, 1);

                var result = new Bitmap(region.Width, region.Height);
                using (var graphics = Graphics.FromImage(result))
                {
                    graphics.DrawImage(image, new Rectangle(0, 0, region.Width, region.Height),
                        region, GraphicsUnit.Pixel);
                }

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "处理图像时发生错误");
                return new Bitmap(1, 1);
            }
        }

        /// <summary>
        /// 提取系统名称区域
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>系统名称区域</returns>
        public RegionOfInterest ExtractSystemNameRegion(Bitmap image, int emulatorIndex)
        {
            if (image == null)
                return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };

            try
            {
                var emulator = _configService.CurrentConfig.Emulators.FirstOrDefault(e => e.Index == emulatorIndex);
                if (emulator == null)
                    return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };

                var region = emulator.SystemNameROI;
                if (region.Width <= 0 || region.Height <= 0)
                    return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };

                var result = new Bitmap(region.Width, region.Height);
                using (var graphics = Graphics.FromImage(result))
                {
                    graphics.DrawImage(image, new Rectangle(0, 0, region.Width, region.Height),
                        region, GraphicsUnit.Pixel);
                }

                return new RegionOfInterest
                {
                    Type = RegionOfInterestType.SystemName,
                    EmulatorIndex = emulatorIndex,
                    Image = result,
                    Bounds = region
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "提取系统名称区域时发生错误");
                return new RegionOfInterest { Type = RegionOfInterestType.SystemName, EmulatorIndex = emulatorIndex };
            }
        }

        /// <summary>
        /// 提取舰船表格区域
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>舰船表格区域</returns>
        public RegionOfInterest ExtractShipTableRegion(Bitmap image, int emulatorIndex)
        {
            if (image == null)
                return new RegionOfInterest { Type = RegionOfInterestType.ShipTable, EmulatorIndex = emulatorIndex };

            try
            {
                var emulator = _configService.CurrentConfig.Emulators.FirstOrDefault(e => e.Index == emulatorIndex);
                if (emulator == null)
                    return new RegionOfInterest { Type = RegionOfInterestType.ShipTable, EmulatorIndex = emulatorIndex };

                var region = emulator.ShipTableROI;
                if (region.Width <= 0 || region.Height <= 0)
                    return new RegionOfInterest { Type = RegionOfInterestType.ShipTable, EmulatorIndex = emulatorIndex };

                var result = new Bitmap(region.Width, region.Height);
                using (var graphics = Graphics.FromImage(result))
                {
                    graphics.DrawImage(image, new Rectangle(0, 0, region.Width, region.Height),
                        region, GraphicsUnit.Pixel);
                }

                return new RegionOfInterest
                {
                    Type = RegionOfInterestType.ShipTable,
                    EmulatorIndex = emulatorIndex,
                    Image = result,
                    Bounds = region
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "提取舰船表格区域时发生错误");
                return new RegionOfInterest { Type = RegionOfInterestType.ShipTable, EmulatorIndex = emulatorIndex };
            }
        }

        /// <summary>
        /// 预处理图像以提高OCR识别率
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <returns>预处理后的图像</returns>
        public Bitmap PreprocessImage(Bitmap? image)
        {
            if (image == null)
                return new Bitmap(1, 1);

            try
            {
                using var mat = BitmapConverter.ToMat(image);
                using var processed = PreprocessImage(mat);
                return BitmapConverter.ToBitmap(processed);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理图像时发生错误");
                return new Bitmap(1, 1);
            }
        }

        /// <summary>
        /// 预处理图像
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <returns>预处理后的图像</returns>
        private Mat PreprocessImage(Mat image)
        {
            try
            {
                // 转换为灰度图
                var gray = new Mat();
                Cv2.CvtColor(image, gray, ColorConversionCodes.BGR2GRAY);

                // 二值化
                var binary = new Mat();
                Cv2.Threshold(gray, binary, 0, 255, ThresholdTypes.Binary | ThresholdTypes.Otsu);

                // 去噪
                var denoised = new Mat();
                Cv2.MedianBlur(binary, denoised, 3);

                return denoised;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理图像时发生错误");
                return image.Clone();
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            GC.SuppressFinalize(this);
        }
    }
}