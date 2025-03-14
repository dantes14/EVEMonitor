namespace EVEMonitor.Core.Models
{
    /// <summary>
    /// 钉钉机器人配置
    /// </summary>
    public class DingTalkConfig
    {
        /// <summary>
        /// 机器人访问令牌
        /// </summary>
        public string AccessToken { get; set; } = string.Empty;

        /// <summary>
        /// 机器人密钥
        /// </summary>
        public string Secret { get; set; } = string.Empty;

        /// <summary>
        /// 是否启用
        /// </summary>
        public bool Enabled { get; set; }
    }
}