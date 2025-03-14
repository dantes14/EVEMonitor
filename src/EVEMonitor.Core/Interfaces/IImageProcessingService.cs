using System;
using System.Collections.Generic;
using System.Drawing;
using System.Runtime.Versioning;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 模拟器图像类
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class EmulatorImage
    {
        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int Index { get; set; }

        /// <summary>
        /// 图像
        /// </summary>
        public required Bitmap Image { get; set; }

        /// <summary>
        /// 区域
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
    public class RegionOfInterest : IDisposable
    {
        /// <summary>
        /// 区域类型
        /// </summary>
        public RegionOfInterestType Type { get; set; }

        /// <summary>
        /// 图像数据
        /// </summary>
        [SupportedOSPlatform("windows")]
        public Bitmap? Image { get; set; }

        /// <summary>
        /// 区域在原图中的位置
        /// </summary>
        public Rectangle Bounds { get; set; }

        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int EmulatorIndex { get; set; }

        /// <summary>
        /// 释放资源
        /// </summary>
        [SupportedOSPlatform("windows")]
        public void Dispose()
        {
            Image?.Dispose();
            GC.SuppressFinalize(this);
        }
    }

    /// <summary>
    /// 区域类型
    /// </summary>
    public enum RegionType
    {
        /// <summary>
        /// 未知
        /// </summary>
        Unknown = 0,

        /// <summary>
        /// 系统名称
        /// </summary>
        SystemName = 1,

        /// <summary>
        /// 舰船表格
        /// </summary>
        ShipTable = 2
    }

    /// <summary>
    /// 图像处理服务接口
    /// </summary>
    [SupportedOSPlatform("windows")]
    public interface IImageProcessingService
    {
        /// <summary>
        /// 处理图像
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <param name="emulatorName">模拟器名称</param>
        /// <returns>处理后的图像</returns>
        Bitmap ProcessImage(Bitmap? image, string emulatorName);

        /// <summary>
        /// 预处理图像以提高OCR识别率
        /// </summary>
        /// <param name="image">原始图像</param>
        /// <returns>预处理后的图像</returns>
        Bitmap PreprocessImage(Bitmap? image);

        /// <summary>
        /// 提取系统名称区域
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>系统名称区域</returns>
        RegionOfInterest ExtractSystemNameRegion(Bitmap screenshot, int emulatorIndex = 0);

        /// <summary>
        /// 提取舰船表格区域
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>舰船表格区域</returns>
        RegionOfInterest ExtractShipTableRegion(Bitmap screenshot, int emulatorIndex = 0);
    }
}