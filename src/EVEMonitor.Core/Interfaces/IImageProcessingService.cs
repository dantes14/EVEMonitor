using System.Drawing;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 模拟器图像类
    /// </summary>
    public class EmulatorImage
    {
        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int Index { get; set; }
        
        /// <summary>
        /// 图像数据
        /// </summary>
        public Bitmap Image { get; set; }
        
        /// <summary>
        /// 区域信息
        /// </summary>
        public Rectangle Region { get; set; }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            Image?.Dispose();
        }
    }

    /// <summary>
    /// 感兴趣区域类型
    /// </summary>
    public enum RegionOfInterestType
    {
        /// <summary>
        /// 星系名称区域
        /// </summary>
        SystemName,
        
        /// <summary>
        /// 舰船表格区域
        /// </summary>
        ShipTable
    }

    /// <summary>
    /// 感兴趣区域
    /// </summary>
    public class RegionOfInterest
    {
        /// <summary>
        /// 区域类型
        /// </summary>
        public RegionOfInterestType Type { get; set; }
        
        /// <summary>
        /// 图像数据
        /// </summary>
        public Bitmap Image { get; set; }
        
        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            Image?.Dispose();
        }
    }

    /// <summary>
    /// 图像处理服务接口
    /// </summary>
    public interface IImageProcessingService
    {
        /// <summary>
        /// 模拟器布局配置
        /// </summary>
        List<EmulatorConfig> EmulatorConfigs { get; set; }

        /// <summary>
        /// 处理截图，分割为多个模拟器子图像
        /// </summary>
        /// <param name="screenshot">完整截图</param>
        /// <returns>模拟器图像列表</returns>
        List<EmulatorImage> ProcessScreenshot(Bitmap screenshot);

        /// <summary>
        /// 提取感兴趣区域
        /// </summary>
        /// <param name="emulatorImage">模拟器图像</param>
        /// <returns>感兴趣区域列表</returns>
        List<RegionOfInterest> ExtractROIs(EmulatorImage emulatorImage);

        /// <summary>
        /// 预处理图像以提高OCR识别率
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <returns>预处理后的图像</returns>
        Bitmap PreprocessImage(Bitmap image);
    }
} 