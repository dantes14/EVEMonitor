using System;
using System.Drawing;
using System.Threading;
using EVEMonitor.Capture.Services;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace EVEMonitor.Capture.Tests
{
    public class ScreenCaptureServiceTests
    {
        private readonly Mock<ILogger<ScreenCaptureService>> _loggerMock;

        public ScreenCaptureServiceTests()
        {
            _loggerMock = new Mock<ILogger<ScreenCaptureService>>();
        }

        [Fact]
        public void Constructor_ShouldInitializeCorrectly()
        {
            // Arrange & Act
            var captureRegion = new Rectangle(0, 0, 1920, 1080);
            var service = new ScreenCaptureService(_loggerMock.Object, captureRegion);

            // Assert
            Assert.NotNull(service);
        }

        [Fact]
        public void CaptureFrame_ShouldReturnBitmap()
        {
            // Arrange
            var captureRegion = new Rectangle(0, 0, 1920, 1080);
            var service = new ScreenCaptureService(_loggerMock.Object, captureRegion);

            // Act
            using (var result = service.CaptureFrame())
            {
                // Assert
                Assert.NotNull(result);
            }
        }

        [Fact]
        public void CaptureScreen_ShouldReturnBitmap()
        {
            // Arrange
            var captureRegion = new Rectangle(0, 0, 1920, 1080);
            var service = new ScreenCaptureService(_loggerMock.Object, captureRegion);

            // Act
            using (var result = service.CaptureFrame())
            {
                // Assert
                Assert.NotNull(result);
                Assert.True(result.Width > 0);
                Assert.True(result.Height > 0);
            }
        }

        [Fact]
        public void StartAndStop_ShouldChangeIsCapturingProperty()
        {
            // Arrange
            var captureRegion = new Rectangle(0, 0, 1920, 1080);
            var service = new ScreenCaptureService(_loggerMock.Object, captureRegion);

            // Act - Start
            service.Start();

            // Assert
            Assert.True(service.IsCapturing);

            // Act - Stop
            service.Stop();

            // Assert
            Assert.False(service.IsCapturing);
        }

        [Fact]
        public void ScreenCaptured_EventShouldTrigger()
        {
            // Arrange
            var captureRegion = new Rectangle(0, 0, 1920, 1080);
            var service = new ScreenCaptureService(_loggerMock.Object, captureRegion);
            bool eventRaised = false;

            service.ScreenCaptured += (sender, e) =>
            {
                eventRaised = true;
                Assert.NotNull(e.CapturedImage);
            };

            // Act
            service.Start();

            // 等待一个捕获周期
            Thread.Sleep(service.CaptureInterval + 500);

            // Cleanup
            service.Stop();

            // Assert
            Assert.True(eventRaised);
        }
    }
}