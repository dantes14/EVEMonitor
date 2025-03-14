namespace EVEMonitor.OCR.Models
{
    /// <summary>
    /// OCR识别结果
    /// </summary>
    public class OcrResult
    {
        /// <summary>
        /// 识别的文本
        /// </summary>
        public string Text { get; set; } = string.Empty;

        /// <summary>
        /// 识别的置信度
        /// </summary>
        public float Confidence { get; set; }
    }
}