using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Reflection;
using EVEMonitor.Core.Models;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Services;
using EVEMonitor.ImageProcessing.Services;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace EVEMonitor.ImageProcessing.Tests
{
    /// <summary>
    /// 图像处理服务测试类
    /// </summary>
    public class ImageProcessingServiceTests
    {
        private readonly Mock<ILogger<ImageProcessingService>> _loggerMock;
        private readonly Mock<IConfigService> _configServiceMock;
        private readonly ImageProcessingService _service;
        private readonly string _testImagesPath;

        public ImageProcessingServiceTests()
        {
            _loggerMock = new Mock<ILogger<ImageProcessingService>>();
            _configServiceMock = new Mock<IConfigService>();

            // 设置配置服务
            var config = new AppConfig
            {
                Emulators = new List<InternalEmulatorConfig>
                {
                    new InternalEmulatorConfig
                    {
                        Name = "TestEmulator",
                        Index = 0,
                        Enabled = true,
                        CaptureRegion = new Rectangle(0, 0, 800, 600),
                        SystemNameROI = new Rectangle(10, 10, 100, 30),
                        ShipTableROI = new Rectangle(10, 50, 200, 400)
                    }
                }
            };
            _configServiceMock.Setup(x => x.CurrentConfig).Returns(config);

            _service = new ImageProcessingService(_loggerMock.Object, _configServiceMock.Object);

            // 设置测试图像路径
            string? assemblyLocation = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            _testImagesPath = assemblyLocation != null
                ? Path.Combine(assemblyLocation, "TestImages")
                : Path.Combine(Directory.GetCurrentDirectory(), "TestImages");
        }

        [Fact]
        public void Constructor_ShouldInitializeCorrectly()
        {
            // Assert
            Assert.NotNull(_service);
        }

        [Fact]
        public void ProcessImage_WithValidImage_ShouldReturnProcessedImage()
        {
            // Arrange
            using var image = new Bitmap(800, 600);
            var emulatorName = "TestEmulator";

            // Act
            var result = _service.ProcessImage(image, emulatorName);

            // Assert
            Assert.NotNull(result);
            Assert.True(result.Width > 0);
            Assert.True(result.Height > 0);
        }

        [Fact]
        public void ProcessImage_WithNullImage_ShouldReturnNull()
        {
            // Arrange
            Bitmap? image = null;
            var emulatorName = "TestEmulator";

            // Act
            var result = _service.ProcessImage(image, emulatorName);

            // Assert
            Assert.Null(result);
        }

        [Fact]
        public void ExtractSystemNameRegion_WithValidImage_ShouldReturnRegion()
        {
            // Arrange
            using var image = new Bitmap(800, 600);
            var emulatorIndex = 0;

            // Act
            var result = _service.ExtractSystemNameRegion(image, emulatorIndex);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(RegionOfInterestType.SystemName, result.Type);
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.NotNull(result.Image);
        }

        [Fact]
        public void ExtractShipTableRegion_WithValidImage_ShouldReturnRegion()
        {
            // Arrange
            using var image = new Bitmap(800, 600);
            var emulatorIndex = 0;

            // Act
            var result = _service.ExtractShipTableRegion(image, emulatorIndex);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(RegionOfInterestType.ShipTable, result.Type);
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.NotNull(result.Image);
        }

        [Fact]
        public void ExtractSystemNameRegion_WithNullImage_ShouldReturnEmptyRegion()
        {
            // Arrange
            Bitmap? image = null;
            var emulatorIndex = 0;

            // Act
#pragma warning disable CS8604 // 可能的 null 引用参数
            var result = _service.ExtractSystemNameRegion(image, emulatorIndex);
#pragma warning restore CS8604

            // Assert
            Assert.NotNull(result);
            Assert.Equal(RegionOfInterestType.SystemName, result.Type);
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.Null(result.Image);
        }

        [Fact]
        public void ExtractShipTableRegion_WithNullImage_ShouldReturnEmptyRegion()
        {
            // Arrange
            Bitmap? image = null;
            var emulatorIndex = 0;

            // Act
#pragma warning disable CS8604 // 可能的 null 引用参数
            var result = _service.ExtractShipTableRegion(image, emulatorIndex);
#pragma warning restore CS8604

            // Assert
            Assert.NotNull(result);
            Assert.Equal(RegionOfInterestType.ShipTable, result.Type);
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.Null(result.Image);
        }

        [Fact]
        public void PreprocessImage_WithValidImage_ShouldReturnProcessedImage()
        {
            // Arrange
            using var image = new Bitmap(800, 600);

            // Act
            var result = _service.PreprocessImage(image);

            // Assert
            Assert.NotNull(result);
            Assert.True(result.Width > 0);
            Assert.True(result.Height > 0);
        }

        [Fact]
        public void PreprocessImage_WithNullImage_ShouldReturnEmptyImage()
        {
            // Act
            var result = _service.PreprocessImage(null);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(1, result.Width);
            Assert.Equal(1, result.Height);
        }
    }
}