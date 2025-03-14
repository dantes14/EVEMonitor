using System;
using System.Collections.Concurrent;
using System.Drawing;
using System.Runtime.Versioning;
using System.Threading.Tasks;
using System.Threading.Channels;

namespace EVEMonitor.Core.Utils
{
    /// <summary>
    /// 截图队列，用于在多线程环境下安全地管理截图
    /// </summary>
    [SupportedOSPlatform("windows")]
    public class ScreenshotQueue : IDisposable
    {
        private readonly ConcurrentQueue<Bitmap> _queue = new ConcurrentQueue<Bitmap>();
        private readonly object _lockObject = new object();
        private readonly int _maxCapacity;
        private readonly Channel<Bitmap> _channel;

        /// <summary>
        /// 队列中的项目数量
        /// </summary>
        public int Count => _queue.Count;

        /// <summary>
        /// 初始化截图队列
        /// </summary>
        public ScreenshotQueue()
        {
            _maxCapacity = 20; // 默认容量
            _channel = Channel.CreateUnbounded<Bitmap>(new UnboundedChannelOptions
            {
                SingleReader = true,
                SingleWriter = true
            });
        }

        /// <summary>
        /// 初始化截图队列
        /// </summary>
        /// <param name="maxCapacity">最大容量</param>
        public ScreenshotQueue(int maxCapacity)
        {
            _maxCapacity = maxCapacity;
            _channel = Channel.CreateUnbounded<Bitmap>(new UnboundedChannelOptions
            {
                SingleReader = true,
                SingleWriter = true
            });
        }

        /// <summary>
        /// 清空队列
        /// </summary>
        [SupportedOSPlatform("windows")]
        public void Clear()
        {
            while (_queue.TryDequeue(out Bitmap? bitmap))
            {
                bitmap?.Dispose();
            }
        }

        /// <summary>
        /// 将图像添加到队列
        /// </summary>
        /// <param name="bitmap">要添加的位图</param>
        [SupportedOSPlatform("windows")]
        public void Enqueue(Bitmap bitmap)
        {
            if (bitmap == null)
                return;

            // 队列过长时删除旧的截图
            if (_queue.Count > _maxCapacity)
            {
                while (_queue.Count > _maxCapacity / 2 && _queue.TryDequeue(out Bitmap? oldBitmap))
                {
                    oldBitmap?.Dispose();
                }
            }

            // 添加图像的副本到队列
            _queue.Enqueue((Bitmap)bitmap.Clone());
        }

        /// <summary>
        /// 异步将图像添加到队列
        /// </summary>
        /// <param name="bitmap">要添加的位图</param>
        [SupportedOSPlatform("windows")]
        public Task EnqueueAsync(Bitmap bitmap)
        {
            Enqueue(bitmap);
            return Task.CompletedTask;
        }

        /// <summary>
        /// 尝试从队列获取一个截图
        /// </summary>
        /// <param name="bitmap">获取的截图</param>
        /// <returns>是否成功获取</returns>
        [SupportedOSPlatform("windows")]
        public bool TryDequeue(out Bitmap? bitmap)
        {
            if (_queue.TryDequeue(out bitmap))
            {
                return true;
            }
            return false;
        }

        /// <summary>
        /// 异步从队列获取一个截图
        /// </summary>
        /// <returns>获取的截图，如果队列为空则返回null</returns>
        [SupportedOSPlatform("windows")]
        public Task<Bitmap?> DequeueAsync()
        {
            if (TryDequeue(out Bitmap? bitmap))
            {
                return Task.FromResult(bitmap);
            }
            return Task.FromResult<Bitmap?>(null);
        }

        /// <summary>
        /// 完成队列处理
        /// </summary>
        public void Complete()
        {
            // 标记队列处理完成
        }

        /// <summary>
        /// 释放所有资源
        /// </summary>
        [SupportedOSPlatform("windows")]
        public void Dispose()
        {
            Clear();
        }
    }
}