using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Interfaces
{
    /// <summary>
    /// 警报服务接口
    /// </summary>
    public interface IAlertService
    {
        /// <summary>
        /// 钉钉Webhook URL
        /// </summary>
        string WebhookUrl { get; set; }

        /// <summary>
        /// 推送舰船警报
        /// </summary>
        /// <param name="systemName">星系名称</param>
        /// <param name="ships">舰船信息列表</param>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <returns>推送是否成功</returns>
        Task<bool> PushShipAlertAsync(string systemName, List<ShipInfo> ships, int emulatorIndex);

        /// <summary>
        /// 推送性能警报
        /// </summary>
        /// <param name="message">警报消息</param>
        /// <param name="processingTime">处理时间</param>
        /// <returns>推送是否成功</returns>
        Task<bool> PushPerformanceAlertAsync(string message, TimeSpan processingTime);

        /// <summary>
        /// 推送警报
        /// </summary>
        /// <param name="alertData">警报数据</param>
        /// <returns>推送是否成功</returns>
        Task<bool> PushAlertAsync(AlertData alertData);
    }
} 