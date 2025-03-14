namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 模拟器识别结果类，存储每个模拟器的OCR识别结果
    /// </summary>
    public class EmulatorRecognitionResult
    {
        /// <summary>
        /// 模拟器索引
        /// </summary>
        public int EmulatorIndex { get; set; }

        /// <summary>
        /// 星系名称
        /// </summary>
        public string SystemName { get; set; } = string.Empty;

        /// <summary>
        /// 舰船信息列表
        /// </summary>
        public List<ShipInfo> Ships { get; set; } = new List<ShipInfo>();

        /// <summary>
        /// 识别时间戳
        /// </summary>
        public DateTime Timestamp { get; set; } = DateTime.Now;

        /// <summary>
        /// 是否包含危险舰船
        /// </summary>
        public bool ContainsDangerousShips { get; set; }

        /// <summary>
        /// 检查是否有舰船数据
        /// </summary>
        /// <returns>如果有舰船数据返回true，否则返回false</returns>
        public bool HasShips()
        {
            return Ships != null && Ships.Count > 0;
        }

        /// <summary>
        /// 创建警报数据
        /// </summary>
        /// <returns>警报数据对象</returns>
        public AlertData CreateAlertData()
        {
            return new AlertData
            {
                AlertType = AlertType.Ship,
                EmulatorIndex = EmulatorIndex,
                SystemName = SystemName,
                RelatedShips = Ships,
                Timestamp = DateTime.Now
            };
        }
    }
}