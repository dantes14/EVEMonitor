using System;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Events
{
    public class AlertEventArgs : EventArgs
    {
        public AlertData AlertData { get; }

        public AlertEventArgs(AlertData alertData)
        {
            AlertData = alertData;
        }
    }
}