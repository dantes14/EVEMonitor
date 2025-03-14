using System;
using System.Collections.Generic;
using System.Drawing;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using Moq;
using EVEMonitor.Core.Services;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using Microsoft.Extensions.Logging;
using System.Runtime.Versioning;

namespace EVEMonitor.Core.Tests.Services
{
    [SupportedOSPlatform("windows")]
    public class ScreenshotServiceTests
    {
        private readonly Mock<ILogger<ScreenshotService>> _loggerMock;
        private readonly Mock<IConfigService> _configServiceMock;
        private readonly Mock<IImageProcessingService> _imageProcessingServiceMock;
        private readonly Mock<IScreenCaptureService> _screenCaptureServiceMock;
        private readonly Mock<IOcrService> _ocrServiceMock;
        private readonly Mock<IAlertService> _alertServiceMock;
        private readonly ScreenshotService _service;

        public ScreenshotServiceTests()
        {
            _loggerMock = new Mock<ILogger<ScreenshotService>>();
            _configServiceMock = new Mock<IConfigService>();
            _imageProcessingServiceMock = new Mock<IImageProcessingService>();
            _screenCaptureServiceMock = new Mock<IScreenCaptureService>();
            _ocrServiceMock = new Mock<IOcrService>();
            _alertServiceMock = new Mock<IAlertService>();

            _service = new ScreenshotService(
                _loggerMock.Object,
                _configServiceMock.Object,
                _imageProcessingServiceMock.Object,
                _screenCaptureServiceMock.Object,
                _ocrServiceMock.Object,
                _alertServiceMock.Object);
        }

        [Fact]
        public void Constructor_ValidParameters_CreatesService()
        {
            // Assert
            Assert.NotNull(_service);
        }

        [Fact]
        public async Task StartAsync_ValidInterval_StartsService()
        {
            // Arrange
            var interval = 1000;

            // Act
            await _service.StartAsync(interval);

            // Assert
            Assert.True(_service.IsRunning);
            Assert.Equal(interval, _service.CurrentInterval);
        }

        [Fact]
        public async Task StopAsync_RunningService_StopsService()
        {
            // Arrange
            await _service.StartAsync(1000);

            // Act
            await _service.StopAsync();

            // Assert
            Assert.False(_service.IsRunning);
        }

        [Fact]
        public async Task CaptureScreenAsync_ValidParameters_CapturesScreen()
        {
            // Arrange
            var testBitmap = new Bitmap(800, 600);
            _screenCaptureServiceMock
                .Setup(c => c.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(testBitmap);

            // Act
            await _service.StartAsync(1000);

            // 等待处理完成
            await Task.Delay(100);
            await _service.StopAsync();

            // Assert
            _screenCaptureServiceMock.Verify(c => c.CaptureWindowAsync(It.IsAny<string>()), Times.AtLeastOnce());
        }

        [Fact]
        public async Task ProcessScreenshotAsync_ValidScreenshot_ProcessesCorrectly()
        {
            // Arrange
            var testBitmap = new Bitmap(800, 600);
            _screenCaptureServiceMock
                .Setup(c => c.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(testBitmap);

            // Act
            await _service.StartAsync(1000);

            // 等待处理完成
            await Task.Delay(100);
            await _service.StopAsync();

            // Assert
            _imageProcessingServiceMock.Verify(i => i.ProcessImage(It.IsAny<Bitmap>(), It.IsAny<string>()), Times.AtLeastOnce());
        }

        [Fact]
        public async Task ProcessScreenshotAsync_DangerousShipDetected_SendsAlert()
        {
            // Arrange
            var testBitmap = new Bitmap(800, 600);
            _screenCaptureServiceMock
                .Setup(c => c.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(testBitmap);

            bool alertSent = false;
            _alertServiceMock
                .Setup(a => a.PushShipAlertAsync(It.IsAny<string>(), It.IsAny<List<ShipInfo>>(), It.IsAny<int>()))
                .Callback(() => alertSent = true)
                .ReturnsAsync(true);

            // Act
            await _service.StartAsync(1000);

            // 等待处理完成
            await Task.Delay(100);
            await _service.StopAsync();

            // Assert
            Assert.True(alertSent);
        }

        [Fact]
        public async Task TakeScreenshotAsync_WithValidEmulator_ShouldReturnProcessedImage()
        {
            // Arrange
            var emulatorName = "TestEmulator";
            var screenshot = new Bitmap(800, 600);
            var processedImage = new Bitmap(400, 300);

            _screenCaptureServiceMock.Setup(x => x.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(screenshot);

            _imageProcessingServiceMock.Setup(x => x.ProcessImage(screenshot, emulatorName))
                .Returns(processedImage);

            // Act
            var result = await _service.TakeScreenshotAsync(emulatorName);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(processedImage, result);
        }

        [Fact]
        public async Task TakeScreenshotAsync_WithInvalidEmulator_ShouldReturnNull()
        {
            // Arrange
            var emulatorName = "InvalidEmulator";

            _screenCaptureServiceMock.Setup(x => x.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync((Bitmap?)null);

            // Act
            var result = await _service.TakeScreenshotAsync(emulatorName);

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public async Task TakeScreenshotAsync_WithProcessingError_ShouldReturnOriginalImage()
        {
            // Arrange
            var emulatorName = "TestEmulator";
            var screenshot = new Bitmap(800, 600);

            _screenCaptureServiceMock.Setup(x => x.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(screenshot);

            _imageProcessingServiceMock.Setup(x => x.ProcessImage(screenshot, emulatorName))
                .Returns(screenshot);

            // Act
            var result = await _service.TakeScreenshotAsync(emulatorName);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(screenshot, result);
        }

        [Fact]
        public async Task ExtractSystemNameRegionAsync_WithValidEmulator_ShouldReturnRegionOfInterest()
        {
            // Arrange
            var emulatorIndex = 0;
            var screenshot = new Bitmap(800, 600);
            var regionOfInterest = new RegionOfInterest
            {
                Type = RegionOfInterestType.SystemName,
                Image = new Bitmap(200, 50),
                Bounds = new Rectangle(100, 100, 200, 50),
                EmulatorIndex = emulatorIndex
            };

            _screenCaptureServiceMock.Setup(x => x.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync(screenshot);

            _imageProcessingServiceMock.Setup(x => x.ExtractSystemNameRegion(screenshot, emulatorIndex))
                .Returns(regionOfInterest);

            // Act
            var result = await _service.ExtractSystemNameRegionAsync(emulatorIndex);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(regionOfInterest, result);
        }

        [Fact]
        public async Task ExtractSystemNameRegionAsync_WithInvalidEmulator_ShouldReturnEmptyRegion()
        {
            // Arrange
            var emulatorIndex = 0;

            _screenCaptureServiceMock.Setup(x => x.CaptureWindowAsync(It.IsAny<string>()))
                .ReturnsAsync((Bitmap?)null);

            // Act
            var result = await _service.ExtractSystemNameRegionAsync(emulatorIndex);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(RegionOfInterestType.SystemName, result.Type);
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.Null(result.Image);
        }
    }
}