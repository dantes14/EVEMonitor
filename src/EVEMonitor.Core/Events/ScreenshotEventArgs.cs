using System;
using System.Drawing;

namespace EVEMonitor.Core.Events
{
    public class ScreenshotEventArgs : EventArgs
    {
        public Bitmap Screenshot { get; }
        public DateTime Timestamp { get; }

        public ScreenshotEventArgs(Bitmap screenshot)
        {
            Screenshot = screenshot;
            Timestamp = DateTime.Now;
        }
    }
}