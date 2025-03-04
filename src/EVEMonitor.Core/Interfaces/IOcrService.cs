using System.Drawing;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// OCR识别服务接口
    /// </summary>
    public interface IOcrService : IDisposable
    {
        /// <summary>
        /// 识别星系名称
        /// </summary>
        /// <param name="image">星系名称区域图像</param>
        /// <returns>识别的星系名称</returns>
        string RecognizeSystemName(Bitmap image);

        /// <summary>
        /// 识别舰船表格
        /// </summary>
        /// <param name="image">舰船表格区域图像</param>
        /// <returns>识别的舰船信息列表</returns>
        List<ShipInfo> RecognizeShipTable(Bitmap image);

        /// <summary>
        /// 处理识别结果
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <param name="systemName">星系名称</param>
        /// <param name="ships">舰船信息列表</param>
        /// <returns>模拟器识别结果</returns>
        EmulatorRecognitionResult ProcessRecognitionResult(int emulatorIndex, string systemName, List<ShipInfo> ships);
    }
} 