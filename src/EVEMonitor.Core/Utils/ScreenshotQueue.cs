using System.Drawing;
using System.Threading.Channels;

namespace EVEMonitor.Core.Utils
{
    /// <summary>
    /// 截图队列类，用于管理截图数据的缓存和顺序处理
    /// </summary>
    public class ScreenshotQueue
    {
        private readonly Channel<Bitmap> _channel;
        private readonly int _capacity;

        /// <summary>
        /// 初始化截图队列
        /// </summary>
        /// <param name="capacity">队列容量</param>
        public ScreenshotQueue(int capacity = 10)
        {
            _capacity = capacity;
            var options = new BoundedChannelOptions(capacity)
            {
                FullMode = BoundedChannelFullMode.Wait,
                SingleReader = true,
                SingleWriter = false
            };
            _channel = Channel.CreateBounded<Bitmap>(options);
        }

        /// <summary>
        /// 获取当前队列长度
        /// </summary>
        public int Count => _channel.Reader.Count;

        /// <summary>
        /// 添加截图到队列
        /// </summary>
        /// <param name="screenshot">截图</param>
        /// <param name="cancellationToken">取消令牌</param>
        /// <returns>添加操作的任务</returns>
        public async ValueTask EnqueueAsync(Bitmap screenshot, CancellationToken cancellationToken = default)
        {
            if (screenshot == null) throw new ArgumentNullException(nameof(screenshot));

            await _channel.Writer.WriteAsync(screenshot, cancellationToken);
        }

        /// <summary>
        /// 从队列获取截图
        /// </summary>
        /// <param name="cancellationToken">取消令牌</param>
        /// <returns>截图</returns>
        public async ValueTask<Bitmap> DequeueAsync(CancellationToken cancellationToken = default)
        {
            return await _channel.Reader.ReadAsync(cancellationToken);
        }

        /// <summary>
        /// 尝试从队列获取截图
        /// </summary>
        /// <param name="screenshot">输出的截图</param>
        /// <returns>是否成功获取</returns>
        public bool TryDequeue(out Bitmap screenshot)
        {
            return _channel.Reader.TryRead(out screenshot);
        }

        /// <summary>
        /// 完成写入
        /// </summary>
        public void Complete()
        {
            _channel.Writer.Complete();
        }

        /// <summary>
        /// 队列是否为空
        /// </summary>
        public bool IsEmpty => _channel.Reader.Count == 0;

        /// <summary>
        /// 队列是否已满
        /// </summary>
        public bool IsFull => _channel.Reader.Count >= _capacity;
    }
} 